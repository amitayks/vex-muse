#!/usr/bin/env node
// cursor_track.mjs — agent-cursor motion whose clicks land on exact times (beats).
//
//   node cursor_track.mjs spec.json out.json      plan every cursor in spec -> track JSON
//   node cursor_track.mjs --selftest              6 shipped styles, click error must be < 1 ms
//   node cursor_track.mjs --styles                list style names (6 public + 82 lab ids)
//
// Motion comes from the vendored Cua motion lab (vendor/cua-motion-lab, MIT, never edited):
// plan(candidate, scene, seed) gives human-like timed points + events. This script re-times it:
// for each click it keeps the style's own move (shape AND speed), places it so the click event
// lands on the requested time, and fills the rest of the window with a still hold before the move
// (anticipation). A move that does not fit its window is compressed uniformly (shape kept).
//
// spec.json (times in seconds, coordinates in stage px):
// { "stage": {"w":1920,"h":1080},
//   "ptPerPx": 0.6667,                 // optional; lab tuning is in laptop points (1280 wide)
//   "cursors": [ { "id": "main", "start": {"x":960,"y":900}, "t0": 0,
//     "legs": [ { "style": "signature_arc", "seed": 3, "notBefore": 0.0,
//                 "clicks": [ {"at": 0.6, "target": {"id":"k3","x":800,"y":500,"w":120,"h":300}},
//                             {"at": 1.8, "target": {...}, "notBefore": 1.2} ] } ] } ] }
// A click entry may set "action": "hover" = arrive on the target at `at` (event 'arrive'), no click.
// A leg's style runs from the previous leg's last click (or t0) to its own last click.
// notBefore (leg or click) = the earliest time the cursor may start moving toward that click.
//
// out.json: { stage, cursors: [ { id, legs: [{style, labId, name, effects, heading, t0, t1, tShow}],
//   tShow = when the leg's look (colour, effects) should take over: its notBefore, else t0.
//   points: [{t,x,y,h,s,sq,o,p}], events: [{t,type,target,x,y,leg}], targets: {id: rect} } ]
//   labFx = the lab's raw fx (trail {ms, opacity}, squashPress, ...) for the player.
//   h = heading rad (add to the art's rest pose; art tip points up-left, -135 deg),
//   s = scale, sq = squash along velocity, o = opacity, p = 1 while pressed.
// Effects per shipped style follow cua-driver motion.rs default_effects().
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const LAB = process.env.CUA_MOTION_LAB || path.resolve(here, '../../../../vendor/cua-motion-lab');
if (!fs.existsSync(path.join(LAB, 'motion/plan.js'))) {
  console.error(`cua motion lab not found at ${LAB} (set CUA_MOTION_LAB)`);
  process.exit(2);
}
const imp = (f) => import(pathToFileURL(path.join(LAB, 'motion', f)).href);
const [{ plan, sampleAt }, { byId, candidates }] = await Promise.all([imp('plan.js'), imp('candidates.js')]);

export const STYLES = {
  signature_arc: { lab: 'dc-signature-arc', fx: { glow: 1, ripple: 1, squish: 1 } },
  spring_settle: { lab: 'dc-spring-settle', fx: { glow: 1, squish: 1 } },
  magnetic: { lab: 'dc-magnetic', fx: { magnet: 1, ripple: 1 } },
  comet_swoop: { lab: 'dc-comet-swoop', fx: { trail: 1, ripple: 1 } },
  adaptive: { lab: 'adaptive-auto', fx: { squish: 1 } },
  classic: { lab: 'dubins-glide', fx: {} },
};

function resolveStyle(name) {
  if (STYLES[name]) return { style: name, cand: byId[STYLES[name].lab], effects: STYLES[name].fx };
  const cand = byId[name];
  if (!cand) throw new Error(`unknown style "${name}" (run --styles)`);
  const fx = cand.fx ?? {};
  return { style: name, cand, effects: { trail: +!!fx.trail, glow: +!!fx.fog, magnet: +!!fx.magnet, shadow: +!!fx.shadow, ripple: 1, squish: 1 } };
}

// One leg: plan natively, then re-time piecewise so each click lands on its time.
function planLeg(leg, startPx, tStart, k) {
  const { style, cand, effects } = resolveStyle(leg.style);
  const marks = [];
  const wrapped = {
    ...cand,
    beforeMove(ctx) {
      marks.push(ctx.api.t);
      if (cand.beforeMove) cand.beforeMove(ctx);
    },
  };
  const toPt = (r) => ({ ...r, x: r.x * k, y: r.y * k, w: r.w * k, h: r.h * k });
  const scene = {
    id: 'track',
    start: { x: startPx.x * k, y: startPx.y * k },
    waypoints: leg.clicks.map((c, i) => ({ ...toPt(c.target), id: c.target.id ?? `t${i}`, action: c.action ?? 'click' })),
  };
  const nat = plan(wrapped, scene, { seed: leg.seed ?? 1, timing: leg.timing ?? 'native' });
  // anchor = the moment that must land on `at`: the click for clicks, the arrival for hovers
  const clickTimes = nat.events.filter((e) => e.type === 'click').map((e) => e.t);
  const nClicks = leg.clicks.filter((c) => (c.action ?? 'click') === 'click').length;
  if (clickTimes.length !== nClicks || marks.length !== leg.clicks.length)
    throw new Error(`${style}: planner gave ${clickTimes.length} clicks / ${marks.length} moves for ${leg.clicks.length}`);
  let cq = 0;
  const clicksN = leg.clicks.map((c, i) => ((c.action ?? 'click') === 'click' ? clickTimes[cq++] : nat.segments[i].t1));

  // pieces: [native a, b] -> [new a', b'];  'hold' pieces freeze the position.
  const pieces = [];
  const fit = [];
  let prevNat = 0;
  let prevNew = tStart * 1000;
  leg.clicks.forEach((c, i) => {
    const T = c.at * 1000;
    const notBefore = (c.notBefore ?? (i === 0 ? leg.notBefore : undefined) ?? -Infinity) * 1000;
    const postLen = marks[i] - prevNat; // previous click -> this move's start (idle, intro)
    const actLen = clicksN[i] - marks[i]; // move + dwell + press, ends on the click
    const W = T - prevNew;
    if (W <= 0) throw new Error(`${style}: click ${i} at ${c.at}s is not after ${prevNew / 1000}s`);
    const earliest = Math.max(prevNew, notBefore);
    let post = Math.min(postLen, Math.max(0, T - earliest - actLen), Math.max(0, W - actLen));
    let actStart = Math.max(prevNew + post, earliest, T - actLen);
    let act = T - actStart;
    if (act > actLen) { actStart = T - actLen; act = actLen; }
    if (act <= 0) throw new Error(`${style}: no room for click ${i} at ${c.at}s`);
    if (post > 0) pieces.push({ a: prevNat, b: marks[i], a2: prevNew, b2: prevNew + post });
    else pieces.push({ a: prevNat, b: marks[i], a2: prevNew, b2: prevNew, drop: true });
    if (actStart > prevNew + post) pieces.push({ hold: true, a: marks[i], a2: prevNew + post, b2: actStart });
    pieces.push({ a: marks[i], b: clicksN[i], a2: actStart, b2: T, scale: act / actLen });
    fit.push({ at: c.at, nativeMs: Math.round(actLen), placedMs: Math.round(act), speedup: +(actLen / act).toFixed(2) });
    prevNat = clicksN[i];
    prevNew = T;
  });
  pieces.push({ a: prevNat, b: nat.duration, a2: prevNew, b2: prevNew + (nat.duration - prevNat), tail: true });

  const inv = 1 / k;
  const conv = (q, t) => ({
    t: +(t / 1000).toFixed(5),
    x: +(q.x * inv).toFixed(2),
    y: +(q.y * inv).toFixed(2),
    h: +(q.heading ?? 0).toFixed(4),
    s: +(q.scale ?? 1).toFixed(4),
    sq: +(q.sq ?? 1).toFixed(4),
    o: +(q.opacity ?? 1).toFixed(3),
    p: q.pressed ? 1 : 0,
  });
  const pts = [];
  const add = (q, t) => {
    if (pts.length && t <= pts[pts.length - 1].t * 1000 + 1e-6) return;
    pts.push(conv(q, t));
  };
  for (const pc of pieces) {
    if (pc.drop) continue;
    if (pc.hold) {
      const q = sampleAt(nat.points, pc.a);
      add(q, pc.a2);
      add(q, pc.b2);
      continue;
    }
    const map = (t) => pc.a2 + ((t - pc.a) / Math.max(1e-9, pc.b - pc.a)) * (pc.b2 - pc.a2);
    add(sampleAt(nat.points, pc.a), pc.a2);
    for (const q of nat.points) if (q.t > pc.a && q.t < pc.b) add(q, map(q.t));
    add(sampleAt(nat.points, pc.b), pc.b2);
  }
  const mapEvent = (t) => {
    for (const pc of pieces) {
      if (pc.hold) continue;
      if (t >= pc.a - 1e-9 && t <= pc.b + 1e-9) {
        if (pc.drop) return pc.a2;
        return pc.a2 + ((t - pc.a) / Math.max(1e-9, pc.b - pc.a)) * (pc.b2 - pc.a2);
      }
    }
    return null;
  };
  const clickAt = leg.clicks.filter((c) => (c.action ?? 'click') === 'click').map((c) => c.at);
  let ci = 0;
  const events = [];
  for (const e of nat.events) {
    let t = mapEvent(e.t);
    if (e.type === 'click') t = clickAt[ci++] * 1000; // exact, no float drift
    if (t === null) continue;
    const ev = { ...e, t: +(t / 1000).toFixed(5) };
    if (e.x !== undefined) { ev.x = +(e.x * inv).toFixed(2); ev.y = +(e.y * inv).toFixed(2); }
    events.push(ev);
  }
  leg.clicks.forEach((c, i) => {
    if ((c.action ?? 'click') !== 'hover') return;
    const q = sampleAt(nat.points, clicksN[i]);
    events.push({ t: c.at, type: 'arrive', target: c.target.id, x: +(q.x * inv).toFixed(2), y: +(q.y * inv).toFixed(2) });
  });
  events.sort((a, b) => a.t - b.t);
  const lastClick = leg.clicks[leg.clicks.length - 1].at;
  return {
    meta: { style, labId: cand.id, name: cand.name, effects, labFx: cand.fx ?? {}, heading: cand.heading ?? 'fixed', t0: tStart, t1: lastClick, tShow: Math.max(tStart, leg.notBefore ?? tStart), fit },
    points: pts,
    events,
    endPos: sampleAt(nat.points, clicksN[clicksN.length - 1]),
  };
}

export function buildTrack(spec) {
  const stage = spec.stage ?? { w: 1920, h: 1080 };
  const k = spec.ptPerPx ?? 1280 / stage.w;
  const cursors = spec.cursors.map((cs) => {
    let start = cs.start;
    let t = cs.t0 ?? 0;
    const out = { id: cs.id, legs: [], points: [], events: [], targets: {} };
    cs.legs.forEach((leg, li) => {
      const r = planLeg(leg, start, t, k);
      const last = li === cs.legs.length - 1;
      const cut = r.meta.t1;
      for (const q of r.points) {
        if (!last && q.t > cut + 1e-6) break;
        if (out.points.length && q.t <= out.points[out.points.length - 1].t) continue;
        out.points.push(q);
      }
      for (const e of r.events) if (last || e.t <= cut + 1e-6) out.events.push({ ...e, leg: li });
      for (const c of leg.clicks) out.targets[c.target.id] = c.target;
      out.legs.push(r.meta);
      start = { x: r.endPos.x / k, y: r.endPos.y / k };
      t = cut;
    });
    out.events.sort((a, b) => a.t - b.t);
    return out;
  });
  return { stage, ptPerPx: k, source: 'vendor/cua-motion-lab (trycua/cua, MIT)', cursors };
}

// ---------------------------------------------------------------- checks
export function verify(spec, track) {
  const errs = [];
  spec.cursors.forEach((cs, ci) => {
    const tr = track.cursors[ci];
    const want = cs.legs.flatMap((l) => l.clicks.filter((c) => (c.action ?? 'click') === 'click').map((c) => ({ at: c.at, r: c.target })));
    const got = tr.events.filter((e) => e.type === 'click');
    for (const c of cs.legs.flatMap((l) => l.clicks.filter((c) => c.action === 'hover'))) {
      const q = at(tr.points, c.at), r = c.target;
      if (q.x < r.x - 1 || q.x > r.x + r.w + 1 || q.y < r.y - 1 || q.y > r.y + r.h + 1)
        errs.push(`${cs.id} hover at ${c.at}s: hotspot (${q.x.toFixed(0)},${q.y.toFixed(0)}) outside ${r.id}`);
    }
    if (got.length !== want.length) errs.push(`${cs.id}: ${got.length} clicks, want ${want.length}`);
    want.forEach((w, i) => {
      const g = got[i];
      if (!g) return;
      const dt = Math.abs(g.t - w.at) * 1000;
      if (dt > 1) errs.push(`${cs.id} click ${i}: ${dt.toFixed(2)} ms off`);
      const q = at(tr.points, w.at);
      const r = w.r;
      if (q.x < r.x - 1 || q.x > r.x + r.w + 1 || q.y < r.y - 1 || q.y > r.y + r.h + 1)
        errs.push(`${cs.id} click ${i}: hotspot (${q.x.toFixed(0)},${q.y.toFixed(0)}) outside ${r.id}`);
    });
    for (let i = 1; i < tr.points.length; i++)
      if (!(tr.points[i].t > tr.points[i - 1].t)) { errs.push(`${cs.id}: time not increasing at ${i}`); break; }
  });
  return errs;
}

// Browser players use the same rule: linear between samples.
export function at(points, t) {
  if (t <= points[0].t) return points[0];
  const n = points.length;
  if (t >= points[n - 1].t) return points[n - 1];
  let lo = 0, hi = n - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (points[m].t <= t) lo = m; else hi = m; }
  const a = points[lo], b = points[hi], f = (t - a.t) / (b.t - a.t);
  return { t, x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f };
}

function selftestSpec() {
  const rect = (id, x, y) => ({ id, x, y, w: 140, h: 220 });
  const keys = [rect('a', 300, 500), rect('b', 1400, 380), rect('c', 760, 640), rect('d', 1600, 700)];
  return {
    stage: { w: 1920, h: 1080 },
    cursors: Object.keys(STYLES).map((s, i) => ({
      id: s,
      start: { x: 960, y: 980 },
      legs: [
        { style: s, seed: 3 + i, clicks: [{ at: 0.6, target: keys[0] }, { at: 1.8, target: keys[1] }] },
        { style: s, seed: 9 + i, notBefore: 2.4, clicks: [{ at: 3.0, target: keys[2], action: 'hover' }, { at: 3.6, target: keys[3] }, { at: 4.4, target: keys[0] }] },
      ],
    })),
  };
}

const args = process.argv.slice(2);
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (args[0] === '--styles') {
    console.log('shipped:', Object.entries(STYLES).map(([k, v]) => `${k} (${v.lab})`).join(', '));
    console.log('lab:', candidates.map((c) => c.id).join(' '));
  } else if (args[0] === '--selftest') {
    const spec = selftestSpec();
    const a = buildTrack(spec);
    const b = buildTrack(spec);
    const errs = verify(spec, a);
    if (JSON.stringify(a) !== JSON.stringify(b)) errs.push('not deterministic');
    for (const c of a.cursors) {
      const clicks = c.events.filter((e) => e.type === 'click').map((e) => e.t.toFixed(3));
      const moveStart = c.points.find((q, i) => i && (q.x !== c.points[0].x || q.y !== c.points[0].y));
      const sp = c.legs.flatMap((l) => l.fit.map((f) => f.speedup + 'x'));
      console.log(`${c.id.padEnd(14)} pts ${String(c.points.length).padStart(4)} clicks ${clicks.join(' ')}  first move ${moveStart?.t.toFixed(3)}s  speedup ${sp.join(' ')}`);
    }
    if (errs.length) { console.error('FAIL\n' + errs.join('\n')); process.exit(1); }
    console.log('PASS: every click within 1 ms of its time, clicks and hovers inside their targets; deterministic');
  } else if (args.length === 2) {
    const spec = JSON.parse(fs.readFileSync(args[0], 'utf8'));
    const track = buildTrack(spec);
    const errs = verify(spec, track);
    fs.writeFileSync(args[1], JSON.stringify(track));
    const n = track.cursors.reduce((s, c) => s + c.events.filter((e) => e.type === 'click').length, 0);
    console.log(`wrote ${args[1]}: ${track.cursors.length} cursor(s), ${n} clicks`);
    for (const c of track.cursors)
      for (const l of c.legs) {
        const worst = Math.max(...l.fit.map((f) => f.speedup));
        console.log(`  ${c.id} ${l.style}: speedup ${l.fit.map((f) => f.speedup + 'x').join(' ')}${worst > 1.5 ? '  <- rushed: widen the window or drop a click' : ''}`);
      }
    if (errs.length) { console.error('FAIL\n' + errs.join('\n')); process.exit(1); }
    console.log('PASS: clicks on time and inside targets');
  } else {
    console.log('usage: cursor_track.mjs spec.json out.json | --selftest | --styles');
    process.exit(1);
  }
}
