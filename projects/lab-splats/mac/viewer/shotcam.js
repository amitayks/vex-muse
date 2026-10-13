// shotcam.js - camera math for Muse shot JSON, a line-by-line port of
// projects/lab-splats/scripts/modal_splat.py (look_c2w, _catmull, _ease, camera_at).
// All matrices are OpenCV camera-to-world (x right, y down, z forward), row-major 4x4 as nested arrays,
// in the world frame of the PLY. No three.js here: shotcam.test.mjs runs it in node.

const sub = (a, b) => a.map((v, i) => v - b[i]);
const add = (a, b) => a.map((v, i) => v + b[i]);
const mul = (a, s) => a.map((v) => v * s);
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (v) => Math.sqrt(dot(v, v));
export const normalize = (v) => mul(v, 1 / Math.max(norm(v), 1e-12));

// modal_splat.look_c2w
export function lookC2w(pos, look, up, rollDeg = 0) {
  const f = normalize(sub(look, pos));
  let d = mul(normalize(up), -1);
  let r = normalize(cross(d, f));
  d = cross(f, r);
  if (rollDeg) {
    const a = (rollDeg * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a);
    const r2 = add(mul(r, c), mul(d, s)), d2 = add(mul(r, -s), mul(d, c));
    r = r2; d = d2;
  }
  return [
    [r[0], d[0], f[0], pos[0]],
    [r[1], d[1], f[1], pos[1]],
    [r[2], d[2], f[2], pos[2]],
    [0, 0, 0, 1],
  ];
}

// modal_splat._catmull: Hermite with Catmull-Rom tangents scaled by segment durations; clamps at the ends.
export function catmull(P, times, t) {
  const n = P.length;
  if (n === 1 || t <= times[0]) return P[0].slice();
  if (t >= times[n - 1]) return P[n - 1].slice();
  let i = 0;
  for (let j = 0; j < n - 1; j++) if (times[j] <= t) i = j;
  const u = (t - times[i]) / Math.max(times[i + 1] - times[i], 1e-9);
  const p0 = P[Math.max(i - 1, 0)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(i + 2, n - 1)];
  const cl = (k) => times[Math.min(Math.max(k, 0), n - 1)];
  const tm = (a, b) => cl(b) - cl(a);
  const dt = times[i + 1] - times[i];
  const m1 = mul(sub(p2, p0), dt / Math.max(tm(i - 1, i + 1), 1e-9));
  const m2 = mul(sub(p3, p1), dt / Math.max(tm(i, i + 2), 1e-9));
  const u2 = u * u, u3 = u2 * u;
  const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
  return p1.map((_, k) => h00 * p1[k] + h10 * m1[k] + h01 * p2[k] + h11 * m2[k]);
}

// modal_splat._ease
export function ease(x, kind) {
  if (kind === "linear") return x;
  if (kind === "in") return x * x * x;
  if (kind === "out") return 1 - (1 - x) ** 3;
  return kind === "smooth" ? x * x * (3 - 2 * x) : x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2;
}

// Python round(): half to even.
export function pyRound(x) {
  const f = Math.floor(x), diff = x - f;
  if (diff > 0.5) return f + 1;
  if (diff < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

// modal_splat.camera_at -> { c2w (4x4 OpenCV), fov (vertical deg), focus }
export function cameraAt(cam, t, up) {
  if (cam.type === "frames") {
    const i = Math.min(pyRound(t * cam.fps), cam.c2w.length - 1);
    const a = cam.c2w[i];
    const c2w = [a.slice(0, 4), a.slice(4, 8), a.slice(8, 12), a.slice(12, 16)];
    const fov = Array.isArray(cam.fov) ? cam.fov[i] : cam.fov;
    const fc = cam.focus ?? 3.0;
    return { c2w, fov, focus: Array.isArray(fc) ? fc[i] : fc };
  }
  const keys = cam.keys;
  const T = keys.map((k) => k.t);
  if (cam.ease) {
    const a = T[0], b = T[T.length - 1];
    const x = Math.min(Math.max((t - a) / Math.max(b - a, 1e-9), 0), 1);
    t = a + ease(x, cam.ease) * (b - a);
  }
  const pos = catmull(keys.map((k) => k.pos), T, t);
  const look = catmull(keys.map((k) => k.look), T, t);
  const fov = catmull(keys.map((k) => [k.fov ?? 50]), T, t)[0];
  const roll = catmull(keys.map((k) => [k.roll ?? 0]), T, t)[0];
  return { c2w: lookC2w(pos, look, up, roll), fov, focus: norm(sub(look, pos)) };
}

// modal_splat render_shot: up "auto:<run>" = normalized mean of -y (camera up) over the run's training cameras.
export function autoUp(camerasJson) {
  let s = [0, 0, 0];
  for (const c of camerasJson.cams) s = add(s, [-c.c2w[0][1], -c.c2w[1][1], -c.c2w[2][1]]);
  return normalize(s);
}

// OpenCV c2w (row-major 4x4) -> column-major 16 array for THREE.Matrix4.fromArray, as an OpenGL camera
// (x right, y up, looking down -z): M_gl = M_cv * diag(1, -1, -1, 1).
export function cvToGlColumnMajor(c2w) {
  const g = c2w.map((row) => [row[0], -row[1], -row[2], row[3]]);
  const out = new Array(16);
  for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) out[c * 4 + r] = g[r][c];
  return out;
}

export function projectCv(c2w, fovDeg, W, H, p) {
  // pinhole projection used by render_shot: fy = fx = (H/2)/tan(fov/2), principal point at the centre.
  const R = [[c2w[0][0], c2w[0][1], c2w[0][2]], [c2w[1][0], c2w[1][1], c2w[1][2]], [c2w[2][0], c2w[2][1], c2w[2][2]]];
  const d = sub(p, [c2w[0][3], c2w[1][3], c2w[2][3]]);
  const q = [0, 1, 2].map((k) => R[0][k] * d[0] + R[1][k] * d[1] + R[2][k] * d[2]); // R^T d
  const fy = H / 2 / Math.tan((fovDeg * Math.PI) / 360);
  return [fy * q[0] / q[2] + W / 2, fy * q[1] / q[2] + H / 2, q[2]];
}
