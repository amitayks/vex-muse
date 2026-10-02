import { interpolatePath } from "@remotion/paths";
import flubberPkg from "flubber"; const { interpolate: flubber } = flubberPkg;
import fs from "fs";
const circle = "M200,20 C299.4,20 380,100.6 380,200 C380,299.4 299.4,380 200,380 C100.6,380 20,299.4 20,200 C20,100.6 100.6,20 200,20 Z";
const spark = (() => { let d = ""; const n = 11; for (let i = 0; i < n; i++) { const a = -Math.PI / 2 + i * 2 * Math.PI / n, a2 = a + Math.PI / n, R = 195 - (i % 3) * 16, r = 62;
  const p = (ang, rad) => `${(200 + rad * Math.cos(ang)).toFixed(1)},${(200 + rad * Math.sin(ang)).toFixed(1)}`;
  d += (i ? "L" : "M") + p(a - 0.09, R) + " L" + p(a + 0.09, R) + " L" + p(a2, r) + " "; } return d + "Z"; })();
// a lowercase "m"-ish glyph outline (bumpy, concave) vs a heart — the hard pair
const glyph = "M60,340 V150 H110 V175 C130,150 160,140 185,140 C215,140 235,155 245,178 C265,152 295,140 325,140 C370,140 390,170 390,215 V340 H335 V225 C335,200 325,188 305,188 C280,188 265,205 265,235 V340 H210 V225 C210,200 200,188 180,188 C155,188 140,205 140,235 V340 Z";
const heart = "M200,360 C120,300 30,240 30,150 C30,90 75,50 125,50 C160,50 185,70 200,95 C215,70 240,50 275,50 C325,50 370,90 370,150 C370,240 280,300 200,360 Z";
const ts = [0, 0.25, 0.5, 0.75, 1];
const pairs = { circle_spark: [circle, spark], glyph_heart: [glyph, heart] };
const out = {};
for (const [k, [a, b]] of Object.entries(pairs)) {
  out[k] = { a, b, remotion: ts.map(t => interpolatePath(t, a, b)), flubber: ts.map(t => flubber(a, b, { maxSegmentLength: 3 })(t)) };
}
fs.writeFileSync("../morphlab/paths.json", JSON.stringify(out));
console.log(Object.keys(out), out.circle_spark.remotion[2].slice(0, 80));
