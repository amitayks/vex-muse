// score.mjs — render a JavaScript score (WebAudio) to WAV, offline and deterministic, in headless Chrome.
//
//   node score.mjs <score.js> <out.wav> [--dur 30] [--sr 48000] [--chrome $CHROME_PATH]
//
// <score.js> defines   async function score(ctx, T)   where ctx is an OfflineAudioContext (stereo) and
// T = { bpm, beat, bar, at(bar, beat=0), dur, rand(seed) } helpers. Build the graph and schedule every
// event in absolute time; do not use setTimeout or Math.random (use T.rand(seed) — seeded, reproducible).
// Optional: export const meta = { bpm: 120 } at the top as `var meta = {...}`.
// Runs from studio/ (uses its puppeteer-core); no GPU needed. Output: 16-bit PCM WAV.
import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';
// ESM resolves packages next to THIS file, not the cwd: load puppeteer-core from studio/ (or the cwd) explicitly.
const here = new URL('.', import.meta.url).pathname, studio = here.replace(/\/\.pi\/skills\/.*$/, '/studio/');
const puppeteer = createRequire(existsSync(studio + 'node_modules/puppeteer-core') ? studio : process.cwd() + '/')('puppeteer-core');
import { readFileSync, writeFileSync } from 'node:fs';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const [src, out] = argv;
if (!src || !out) { console.log('usage: node score.mjs <score.js> <out.wav> [--dur 30] [--sr 48000]'); process.exit(1); }
const dur = +opt('--dur', 30), sr = +opt('--sr', 48000);
const chrome = opt('--chrome', process.env.CHROME_PATH);
const code = readFileSync(src, 'utf8');

const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage();
page.on('pageerror', e => console.log('[page error]', e.message));
page.on('console', m => { if (['error', 'warn', 'log'].includes(m.type())) console.log('[page]', m.text()); });
await page.setContent('<html><body></body></html>');
const b64 = await page.evaluate(async (code, dur, sr) => {
  const meta = (new Function(code + '\n;return typeof meta!=="undefined"?meta:{}'))();
  const score = (new Function(code + '\n;return score'))();
  const bpm = meta.bpm || 120, beat = 60 / bpm, bar = beat * (meta.beatsPerBar || 4);
  const ctx = new OfflineAudioContext(2, Math.ceil(dur * sr), sr);
  const rand = seed => { let s = (seed * 2654435761) >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
  await score(ctx, { bpm, beat, bar, at: (b, bt = 0) => b * bar + bt * beat, dur, rand });
  const buf = await ctx.startRendering();
  const L = buf.getChannelData(0), R = buf.getChannelData(1), n = L.length;
  const ab = new ArrayBuffer(44 + n * 4), v = new DataView(ab);
  const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); v.setUint32(4, 36 + n * 4, true); w(8, 'WAVE'); w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, 2, true); v.setUint32(24, sr, true); v.setUint32(28, sr * 4, true); v.setUint16(32, 4, true); v.setUint16(34, 16, true);
  w(36, 'data'); v.setUint32(40, n * 4, true);
  let peak = 0; for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  const g = peak > 0.98 ? 0.98 / peak : 1;
  for (let i = 0; i < n; i++) { v.setInt16(44 + i * 4, Math.max(-1, Math.min(1, L[i] * g)) * 32767, true); v.setInt16(46 + i * 4, Math.max(-1, Math.min(1, R[i] * g)) * 32767, true); }
  let s = ''; const u = new Uint8Array(ab); for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000));
  return btoa(s);
}, code, dur, sr);
writeFileSync(out, Buffer.from(b64, 'base64'));
await browser.close();
console.log(JSON.stringify({ out, dur, sr }));
