// node tools/make_orbit.mjs <run> <ply rel vol> <out shot>  : 8 s orbit of the training cameras' focus point
import { readFileSync, writeFileSync } from "node:fs";
import { autoUp, normalize } from "../viewer/shotcam.js";
const [run, ply, out] = process.argv.slice(2);
const cams = JSON.parse(readFileSync(`vol/runs/${run}/cameras.json`));
const up = autoUp(cams);
// least-squares point nearest all optical axes: sum (I - f f^T) (x - c) = 0
const A = [[0,0,0],[0,0,0],[0,0,0]], b = [0,0,0]; let C = [0,0,0];
for (const c of cams.cams) {
  const p = [c.c2w[0][3], c.c2w[1][3], c.c2w[2][3]], f = normalize([c.c2w[0][2], c.c2w[1][2], c.c2w[2][2]]);
  for (let i = 0; i < 3; i++) { C[i] += p[i] / cams.cams.length; for (let j = 0; j < 3; j++) { const m = (i === j ? 1 : 0) - f[i] * f[j]; A[i][j] += m; b[i] += m * p[j]; } }
}
const det = (M) => M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1]) - M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0]) + M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]);
const solve = (M, v) => { const D = det(M); return [0,1,2].map((k) => det(M.map((r, i) => r.map((x, j) => (j === k ? v[i] : x)))) / D); };
const target = solve(A, b);
const dot = (a, c) => a[0]*c[0]+a[1]*c[1]+a[2]*c[2];
// ring radius and height of cameras relative to target
const rel = cams.cams.map((c) => [c.c2w[0][3]-target[0], c.c2w[1][3]-target[1], c.c2w[2][3]-target[2]]);
const h = rel.reduce((s, r) => s + dot(r, up), 0) / rel.length;
const rad = rel.reduce((s, r) => { const v = r.map((x, i) => x - dot(r, up) * up[i]); return s + Math.hypot(...v); }, 0) / rel.length;
const e1 = normalize(rel[0].map((x, i) => x - dot(rel[0], up) * up[i])), e2 = [up[1]*e1[2]-up[2]*e1[1], up[2]*e1[0]-up[0]*e1[2], up[0]*e1[1]-up[1]*e1[0]];
const keys = []; const N = 5, dur = 8;
for (let k = 0; k < N; k++) {
  const a = (k / (N - 1)) * Math.PI * 0.9, r = rad * (0.75 - 0.2 * k / (N - 1)), hh = h * (0.8 - 0.3 * k / (N - 1));
  const pos = [0,1,2].map((i) => target[i] + r * (Math.cos(a) * e1[i] + Math.sin(a) * e2[i]) + hh * up[i]);
  keys.push({ t: (k / (N - 1)) * dur, pos: pos.map((v) => +v.toFixed(4)), look: target.map((v, i) => +(v + 0.15 * up[i]).toFixed(4)), fov: 50 - 6 * k / (N - 1), roll: 0 });
}
const shot = { width: 1920, height: 1080, fps: 30, duration: dur, bg: [0, 0, 0], lens: { samples: 8, shutter: 0.5, aperture: 0.0, focus: "look" },
  camera: { type: "keys", up: `auto:${run}`, ease: "inout", keys }, layers: [{ ply, xform: null, effects: [] }] };
writeFileSync(out, JSON.stringify(shot, null, 1));
console.log(JSON.stringify({ target, ring_radius: rad, cam_height: h, up }));
