/* cursor-fx.js — draw an agent-cursor track (from scripts/cursor_track.mjs) on a 2D canvas at time t.
 * Pure function of t: no clock, no state. Load with <script src>; exposes window.CursorFX.
 *
 *   CursorFX.draw(g, cursor, t, opts)   cursor = track.cursors[i]; g = CanvasRenderingContext2D in stage px
 *   CursorFX.sample(points, t)          {x, y, h, s, sq, o, p}, linear between samples
 *   CursorFX.velocity(points, t)        {x, y} px/s
 *   CursorFX.legAt(cursor, t)           index of the style leg active at t
 *
 * opts: { size: 56 (px, tip to tail), color: '#5b6cff' or (legIndex) => colour, stroke: '#fff',
 *         effects: override {trail, glow, magnet, ripple, squish, shadow}, unit: 1.5 (px per lab pt),
 *         opacity: 1 }
 * Effect maths is ported from the Cua motion lab renderer (vendor/cua-motion-lab/render.js, MIT).
 * The art is our own rounded arrowhead (not the Cua body mark). Tip = hotspot = (0, 0).
 */
(function (root) {
  'use strict';
  var ART_LEN = 28;
  var ART = 'M0 0 C1.1 0 1.8 .6 2.3 1.8 L11.1 25.2 C11.7 26.9 10.1 28.3 8.6 27.4 L1.3 23 C.5 22.5 -.5 22.5 -1.3 23 L-8.6 27.4 C-10.1 28.3 -11.7 26.9 -11.1 25.2 L-2.3 1.8 C-1.8 .6 -1.1 0 0 0 Z';
  var REST = -Math.PI / 4; // art points up (-90 deg); rest pose points up-left (-135 deg) like the lab art
  var path = null;
  function art() { return path || (path = new Path2D(ART)); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function easeOut(k) { k = clamp(k, 0, 1); return 1 - Math.pow(1 - k, 3); }
  function wrap(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }
  function rgba(hex, a) {
    var n = parseInt(hex.slice(1), 16);
    return 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + a + ')';
  }

  function sample(P, t) {
    var n = P.length;
    if (t <= P[0].t) return P[0];
    if (t >= P[n - 1].t) return P[n - 1];
    var lo = 0, hi = n - 1;
    while (hi - lo > 1) { var m = (lo + hi) >> 1; if (P[m].t <= t) lo = m; else hi = m; }
    var a = P[lo], b = P[hi], f = (t - a.t) / (b.t - a.t);
    var mix = function (k, d) { var x = a[k] == null ? d : a[k], y = b[k] == null ? d : b[k]; return x + (y - x) * f; };
    return { t: t, x: mix('x', 0), y: mix('y', 0), h: (a.h || 0) + wrap((b.h || 0) - (a.h || 0)) * f,
      s: mix('s', 1), sq: mix('sq', 1), o: mix('o', 1), p: a.p };
  }
  function velocity(P, t) {
    var a = sample(P, t - 0.012), b = sample(P, t + 0.012);
    return { x: (b.x - a.x) / 0.024, y: (b.y - a.y) / 0.024 };
  }
  function legAt(c, t) { // the leg whose look is on screen at t (tShow = its notBefore, else t0)
    for (var i = c.legs.length - 1; i >= 0; i--) if (t >= (c.legs[i].tShow != null ? c.legs[i].tShow : c.legs[i].t0)) return i;
    return 0;
  }
  function colorOf(opts, li) { return typeof opts.color === 'function' ? opts.color(li) : (opts.color || '#5b6cff'); }

  function drawTrail(g, P, t, col, sc, cfg) {
    var ms = (cfg && cfg.ms ? cfg.ms : 240) / 1000, op = cfg && cfg.opacity != null ? cfg.opacity : 0.45;
    var steps = 26, back = 0.55 * ART_LEN * sc, pts = [], len = 0, i;
    for (i = 0; i <= steps; i++) {
      var tt = t - ms + ms * i / steps, q = sample(P, tt), v = velocity(P, tt), sp = Math.hypot(v.x, v.y);
      var w = clamp((sp - 60) / 390, 0, 1);
      var p = sp > 1 ? { x: q.x - v.x / sp * back * w, y: q.y - v.y / sp * back * w } : { x: q.x, y: q.y };
      if (i) len += Math.hypot(p.x - pts[i - 1].x, p.y - pts[i - 1].y);
      pts.push(p);
    }
    var fade = Math.min(1, len / 90);
    g.save(); g.lineCap = 'round';
    for (i = 1; i <= steps; i++) {
      var k = i / steps, a = pts[i - 1], b = pts[i];
      if (Math.hypot(b.x - a.x, b.y - a.y) < 0.3) continue;
      g.strokeStyle = rgba(col, op * k * k * fade);
      g.lineWidth = (2 + 12 * k) * sc / 2;
      g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    }
    g.restore();
  }

  function pressK(events, t, depth) {
    var last = null;
    for (var i = 0; i < events.length && events[i].t <= t; i++)
      if (events[i].type === 'press' || events[i].type === 'release') last = events[i];
    if (!last) return 0;
    var age = t - last.t;
    if (last.type === 'press') return depth * Math.min(1, age / 0.05);
    return depth * Math.max(0, Math.cos(Math.min(1, age / 0.22) * Math.PI * 1.5)) * Math.max(0, 1 - age / 0.22);
  }

  function draw(g, c, t, opts) {
    opts = opts || {};
    var P = c.points, li = legAt(c, t), leg = c.legs[li], fx = Object.assign({}, leg.effects, opts.effects || {});
    var lab = leg.labFx || {}, col = colorOf(opts, li), unit = opts.unit || 1.5;
    var size = opts.size || 56, sc = size / ART_LEN, alpha = opts.opacity == null ? 1 : opts.opacity;
    var q = sample(P, t), v = velocity(P, t), sp = Math.hypot(v.x, v.y), spPt = sp / unit;
    if (alpha <= 0) return q;
    g.save(); g.globalAlpha = alpha;
    // magnet: target glow after a snap, 700 ms
    var evLeg = function (e) { return e.leg == null ? li : e.leg; };
    var evFx = function (e) { return Object.assign({}, c.legs[evLeg(e)].effects, opts.effects || {}); };
    c.events.forEach(function (e) {
      var age = t - e.t, r = c.targets[e.target], col = colorOf(opts, evLeg(e));
      if (e.type !== 'snap' || age < 0 || age > 0.7 || !r || !evFx(e).magnet) return;
      var k = 1 - age / 0.7;
      g.save(); g.shadowColor = rgba(col, 0.9 * k); g.shadowBlur = 40 * k; g.strokeStyle = rgba(col, 0.9 * k); g.lineWidth = 4;
      g.beginPath(); g.roundRect(r.x - 6, r.y - 6, r.w + 12, r.h + 12, 22); g.stroke(); g.restore();
    });
    if (fx.trail) drawTrail(g, P, t, col, sc, lab.trail === true ? null : lab.trail);
    // click ripples, 520 ms
    c.events.forEach(function (e) {
      var age = t - e.t, col = colorOf(opts, evLeg(e));
      if (e.type !== 'click' || age < 0 || age > 0.52 || evFx(e).ripple === 0) return;
      var k = age / 0.52;
      g.strokeStyle = rgba(col, 0.75 * (1 - k)); g.lineWidth = (4 * (1 - k) + 1) * unit;
      g.beginPath(); g.arc(e.x, e.y, (8 + 44 * easeOut(k)) * unit, 0, Math.PI * 2); g.stroke();
    });
    // speed glow ("velocity fog"): soft glow behind the body, against velocity, grows with speed
    var tipDir = (q.h || 0) + REST - Math.PI / 2; // world angle the tip points at
    var tail = { x: q.x - Math.cos(tipDir) * 0.5 * size, y: q.y - Math.sin(tipDir) * 0.5 * size }; // body centre
    if (fx.glow) {
      var off = Math.min(18, spPt * 0.009) * unit, ux = sp > 1 ? v.x / sp : 0, uy = sp > 1 ? v.y / sp : 0;
      var R = 34 * unit * (1 + Math.min(0.44, spPt * 0.00024)), A = Math.min(0.5, 0.12 + spPt * 0.00012) * (q.o == null ? 1 : q.o);
      var gx = tail.x - ux * off, gy = tail.y - uy * off, gr = g.createRadialGradient(gx, gy, 0, gx, gy, R);
      gr.addColorStop(0, rgba(col, A)); gr.addColorStop(1, rgba(col, 0));
      g.fillStyle = gr; g.beginPath(); g.arc(gx, gy, R, 0, Math.PI * 2); g.fill();
    }
    var depth = fx.squish === 0 ? 0 : 1 - (lab.squashPress || 0.88);
    var pk = pressK(c.events, t, depth);
    var body = function (a, dx, dy, fill, shadow) {
      g.save(); g.globalAlpha = alpha * a * (q.o == null ? 1 : q.o);
      g.translate(q.x + dx, q.y + dy);
      var sq = q.sq || 1;
      if (sq !== 1 && sp > 1) { var va = Math.atan2(v.y, v.x); g.rotate(va); g.scale(sq, 1 / sq); g.rotate(-va); }
      var s = (q.s || 1) * (1 - pk) * sc;
      g.rotate((q.h || 0) + REST); g.scale(s, s);
      if (shadow) { g.fillStyle = shadow; g.fill(art()); g.restore(); return; }
      g.shadowColor = rgba(col, 0.55); g.shadowBlur = 10;
      g.lineJoin = 'round'; g.lineWidth = 3.4; g.strokeStyle = opts.stroke || '#ffffff'; g.stroke(art());
      g.shadowBlur = 0; g.fillStyle = fill; g.fill(art()); g.restore();
    };
    if (fx.shadow) { var lift = Math.max(0, (q.s || 1) - 1); body(0.28, (6 + lift * 90) * unit / 1.5, (14 + lift * 140) * unit / 1.5, col, 'rgba(40,30,20,0.6)'); }
    body(1, 0, 0, col);
    g.restore();
    return q;
  }

  root.CursorFX = { draw: draw, sample: sample, velocity: velocity, legAt: legAt, ART: ART, ART_LEN: ART_LEN, REST: REST };
})(typeof window !== 'undefined' ? window : globalThis);
