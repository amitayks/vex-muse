// webgpu_snap.mjs <comp>/index.html <outDir> t1 [t2 ...] [--scale 0.5]
// Full-frame stills of a WebGPU HyperFrames comp at the given times (seconds), captured the same way as
// the Modal render. `hyperframes snapshot` cannot do this here (it refuses software WebGPU adapters).
// Speed on a 2-CPU box: 5-20 s per 1080p frame; first frame of each preset adds its compile time.
import fs from 'fs';
import path from 'path';
import { launch, open, seek, compSize } from './_chrome.mjs';

const args = process.argv.slice(2);
const si = args.indexOf('--scale'); const scale = si >= 0 ? +args.splice(si, 2)[1] : 1;
const [page, outDir, ...ts] = args;
if (!page || !outDir || !ts.length) { console.error('usage: webgpu_snap.mjs <comp>/index.html <outDir> t1 [t2 ...] [--scale 0.5]'); process.exit(2); }
fs.mkdirSync(outDir, { recursive: true });
const b = await launch();
const probe = await open(b, 'file://' + path.resolve(page), { width: 1920, height: 1080 });
const { w, h } = await compSize(probe); await probe.close();
const p = await open(b, 'file://' + path.resolve(page), { width: w, height: h, scale });
await p.evaluate(async () => { await document.fonts.ready; });
for (const t of ts.map(Number)) {
  const s = Date.now();
  await seek(p, t);
  const name = path.join(outDir, `t${t.toFixed(3).padStart(7, '0')}.png`);
  await p.screenshot({ path: name });
  console.log('shot', t, ((Date.now() - s) / 1000).toFixed(1) + 's', name);
}
await b.close();
