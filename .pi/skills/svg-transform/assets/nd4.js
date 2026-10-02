/* nd4.js — pure 4D geometry for SVG motion (no deps, no DOM). Every function is a pure function of its
 * inputs, so a frame is a pure function of time: feed angles/offsets computed from t, redraw.
 *
 *   ND4.tesseract()                 -> {V:[16 x [x,y,z,w]] (±1), E:[32 x [i,j]], cells:[8 x {axis,sign,edges:[k..]}]}
 *   ND4.rot(v, i, j, a)             -> v rotated by angle a in the coordinate plane (i,j); axes 0..3 = x,y,z,w
 *   ND4.rotAll(V, [[i,j,a],...])    -> every vertex through the listed plane rotations, in order
 *   ND4.project4(v, d4)             -> 3D point: perspective from a 4D eye on the +w axis at distance d4 (> max |w|)
 *   ND4.view3(p, yaw, pitch)        -> 3D point turned by a camera yaw (about y) then pitch (about x)
 *   ND4.project3(p, d3, f, cx, cy)  -> [sx, sy, depth]: perspective to screen, f = focal px
 *   ND4.slice(V, E, cells, n, s)    -> faces of the 3D cross-section {x : n·x = s}: [{cell, pts:[[a,b,c]...]}]
 *                                      in hyperplane coordinates (orthonormal basis of n's complement)
 *   ND4.hull2(points)               -> convex hull (2D, CCW) — silhouette of a projected cell
 * Symmetry note: a 90° turn in any coordinate plane maps the tesseract onto itself (vertices permute), so
 * any rotation that ends on a multiple of 90° per plane lands on a pose identical to the start — a bar-locked
 * loop or cut point. A 180° turn in XW/YW/ZW swaps the inner and outer cube of the perspective view.
 */
(function (root) {
  const ND4 = {};
  ND4.tesseract = function () {
    const V = [];
    for (let k = 0; k < 16; k++) V.push([0, 1, 2, 3].map(b => (k >> b) & 1 ? 1 : -1));
    const E = [];
    for (let a = 0; a < 16; a++) for (let b = 0; b < 4; b++) { const c = a ^ (1 << b); if (a < c) E.push([a, c]); }
    const cells = [];
    for (let axis = 0; axis < 4; axis++) for (const sign of [-1, 1]) {
      const edges = [];
      E.forEach(([i, j], k) => { if (V[i][axis] === sign && V[j][axis] === sign) edges.push(k); });
      cells.push({ axis, sign, edges, verts: V.map((v, i) => v[axis] === sign ? i : -1).filter(i => i >= 0) });
    }
    return { V, E, cells };
  };
  ND4.rot = function (v, i, j, a) {
    const c = Math.cos(a), s = Math.sin(a), o = v.slice();
    o[i] = c * v[i] - s * v[j]; o[j] = s * v[i] + c * v[j]; return o;
  };
  ND4.rotAll = (V, planes) => V.map(v => planes.reduce((p, [i, j, a]) => ND4.rot(p, i, j, a), v));
  ND4.project4 = function (v, d4) { const k = 1 / (d4 - v[3]); return [v[0] * k, v[1] * k, v[2] * k, v[3]]; };
  ND4.view3 = function (p, yaw, pitch) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x = cy * p[0] + sy * p[2], z = -sy * p[0] + cy * p[2];
    const y = cp * p[1] - sp * z, z2 = sp * p[1] + cp * z;
    return [x, y, z2].concat(p.slice(3));
  };
  ND4.project3 = function (p, d3, f, cx, cy) { const k = f / (d3 - p[2]); return [cx + p[0] * k, cy - p[1] * k, p[2]]; };
  // orthonormal basis of the hyperplane perpendicular to unit n (Gram-Schmidt against the standard axes)
  ND4.basis = function (n) {
    const B = [n]; const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
    for (let k = 0; k < 4 && B.length < 4; k++) {
      let e = [0, 0, 0, 0]; e[k] = 1;
      for (const b of B) { const d = dot(e, b); e = e.map((x, i) => x - d * b[i]); }
      const L = Math.hypot(...e); if (L > 1e-6) B.push(e.map(x => x / L));
    }
    return B.slice(1);
  };
  ND4.slice = function (V, E, cells, n, s) {
    const L = Math.hypot(...n); n = n.map(x => x / L);
    const B = ND4.basis(n), d = V.map(v => v.reduce((a, x, i) => a + x * n[i], 0) - s);
    const hit = E.map(([i, j]) => {
      if (d[i] * d[j] > 0 || d[i] === d[j]) return null;
      const u = d[i] / (d[i] - d[j]), p = V[i].map((x, k) => x + (V[j][k] - x) * u);
      return B.map(b => b.reduce((a, x, k) => a + x * p[k], 0));
    });
    const faces = [];
    cells.forEach((c, ci) => {
      const pts = [];
      c.edges.forEach(k => { const p = hit[k]; if (p && !pts.some(q => Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]) < 1e-6)) pts.push(p); });
      if (pts.length < 3) return;
      const m = [0, 1, 2].map(k => pts.reduce((a, p) => a + p[k], 0) / pts.length);
      // in-plane frame from the first two non-collinear offsets
      const sub = (a, b) => a.map((x, i) => x - b[i]), cr = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
      const u = sub(pts[0], m); let nrm = null;
      for (let q = 1; q < pts.length && !nrm; q++) { const c2 = cr(u, sub(pts[q], m)); if (Math.hypot(...c2) > 1e-9) nrm = c2; }
      if (!nrm) return;
      const w = cr(nrm, u);
      pts.sort((a, b) => { const pa = sub(a, m), pb = sub(b, m);
        return Math.atan2(pa.reduce((s2, x, i) => s2 + x * w[i], 0), pa.reduce((s2, x, i) => s2 + x * u[i], 0)) -
               Math.atan2(pb.reduce((s2, x, i) => s2 + x * w[i], 0), pb.reduce((s2, x, i) => s2 + x * u[i], 0)); });
      faces.push({ cell: ci, pts, center: m });
    });
    return faces;
  };
  ND4.hull2 = function (P) {
    const p = P.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = [], hi = [];
    for (const q of p) { while (lo.length > 1 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
    for (const q of p.slice().reverse()) { while (hi.length > 1 && cr(hi[hi.length - 2], hi[hi.length - 1], q) <= 0) hi.pop(); hi.push(q); }
    return lo.slice(0, -1).concat(hi.slice(0, -1));
  };
  root.ND4 = ND4;
  if (typeof module !== "undefined") module.exports = ND4;
})(typeof window !== "undefined" ? window : globalThis);
