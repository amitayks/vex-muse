// material_grid.mjs <specs.json> <outDir> [--w 480 --h 270 --t 1.0]
// Look development without a comp: specs.json is {"<label>": <preset {components:[...]}>, ...}.
// Renders each preset at small size and time t to <outDir>/<label>.png, then a labelled sheet
// <outDir>/_sheet.jpg (via sheet.py). ~0.5-3 s per 480x270 preset; a first compile can take 35 s.
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';
import { launch, open } from './_chrome.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : d; };
const W = +opt('--w', 480), H = +opt('--h', 270), T = +opt('--t', 1);
const [specFile, outDir] = args;
if (!specFile || !outDir) { console.error('usage: material_grid.mjs <specs.json> <outDir> [--w 480 --h 270 --t 1]'); process.exit(2); }
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });
const b = await launch();
const p = await open(b, 'file://' + path.join(here, 'grid.html'), { width: W, height: H });
let fails = 0;
for (const [name, spec] of Object.entries(specs)) {
  const s = Date.now();
  try {
    await p.evaluate((sp, t, w, h) => window.renderOne(sp, t, w, h), spec, T, W, H);
    await p.screenshot({ path: path.join(outDir, `${name}.png`) });
    console.log(name, 'ok', Date.now() - s, 'ms');
  } catch (e) { fails++; console.log(name, 'FAIL', e.message.slice(0, 200)); }
  await p.evaluate(() => window.destroyCur());
}
await b.close();
const py = process.env.PY || 'python3';
try { execFileSync(py, [path.join(here, 'sheet.py'), outDir, path.join(outDir, '_sheet.jpg'), '4', String(Math.min(W, 480))], { stdio: 'inherit' }); }
catch (e) { console.log('sheet.py failed (needs Pillow: use $PY from tools/env.sh)'); }
process.exit(fails ? 1 : 0);
