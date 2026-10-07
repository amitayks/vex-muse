// check_determinism.mjs <comp>/index.html [--n 6] [--scale 0.5] [--times t1,t2,...]
// Proves a WebGPU comp is a pure function of t before any paid render: captures N times in order,
// then the same times shuffled, then one time again after 2.5 s idle (a stray wall-clock render
// would move it), hashes every frame and compares. Exit 0 = PASS, 1 = FAIL (prints which t differ).
import crypto from 'crypto';
import path from 'path';
import { launch, open, seek, compSize } from './_chrome.mjs';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : d; };
const n = +opt('--n', 6), scale = +opt('--scale', 0.5), timesArg = opt('--times', '');
const page = args[0];
if (!page) { console.error('usage: check_determinism.mjs <comp>/index.html [--n 6] [--scale 0.5] [--times a,b,c]'); process.exit(2); }
const b = await launch();
const probe = await open(b, 'file://' + path.resolve(page), { width: 1920, height: 1080 });
const { w, h, dur } = await compSize(probe); await probe.close();
const p = await open(b, 'file://' + path.resolve(page), { width: w, height: h, scale });
await p.evaluate(async () => { await document.fonts.ready; });
const times = timesArg ? timesArg.split(',').map(Number)
  : Array.from({ length: n }, (_, i) => +((dur * (i + 0.5)) / n).toFixed(3));
const shot = async (t) => { await seek(p, t); return crypto.createHash('sha256').update(await p.screenshot()).digest('hex').slice(0, 12); };
const seq = {}; for (const t of times) seq[t] = await shot(t);
const shuffled = [...times].sort((a, b) => ((a * 7919) % 1) - ((b * 7919) % 1) || b - a);
const bad = [];
for (const t of shuffled) { const hsh = await shot(t); if (hsh !== seq[t]) bad.push({ t, seq: seq[t], shuffled: hsh }); }
await new Promise((r) => setTimeout(r, 2500));
const tIdle = times[Math.floor(times.length / 2)]; const hIdle = await shot(tIdle);
if (hIdle !== seq[tIdle]) bad.push({ t: tIdle, seq: seq[tIdle], afterIdle: hIdle });
const distinct = new Set(Object.values(seq)).size;
await b.close();
console.log(JSON.stringify({ times, distinctFrames: distinct, mismatches: bad }));
if (distinct < Math.min(2, times.length)) { console.log('FAIL: every frame is identical (blank or frozen canvas?)'); process.exit(1); }
if (bad.length) { console.log('FAIL: frames depend on seek order or wall-clock time'); process.exit(1); }
console.log(`PASS: ${times.length} times identical in order, shuffled and after idle`);
