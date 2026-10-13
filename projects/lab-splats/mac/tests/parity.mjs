import { readFileSync } from "fs";
import { cameraAt } from "../viewer/shotcam.js";
const cases = JSON.parse(readFileSync(new URL("./cases.json", import.meta.url)));
let maxM = 0, maxF = 0, n = 0;
for (const c of cases) c.ts.forEach((t, i) => {
  const js = cameraAt(c.cam, t, c.up), [pm, pf] = c.py[i];
  for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) maxM = Math.max(maxM, Math.abs(js.c2w[r][k] - pm[r][k]));
  maxF = Math.max(maxF, Math.abs(js.fov - pf)); n++;
});
console.log(JSON.stringify({ samples: n, max_abs_c2w_err: maxM, max_abs_fov_err: maxF, pass: maxM < 1e-9 && maxF < 1e-9 }));
