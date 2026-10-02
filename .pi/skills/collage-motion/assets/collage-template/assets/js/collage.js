/* collage.js — Muse collage-motion mechanics for HyperFrames (GSAP 3). No network, no DOM ids assumed.
 * Every effect is a pure function of composition time t, so parallel render workers can seek anywhere.
 *
 *   const K = Collage.init({ fps: 30, step: 15 });       // step = stop-motion rate for builds ("on twos")
 *   K.torn(el, { amp: 9, seed: 3, edges: "trbl" });      // torn edge (CSS polygon, px amplitude; measures el, ~9 px/point)
 *   K.enter(el, "drop", t, { rot: -2 });                 // drop | slap | slide | stretch | pop | rise
 *   K.stamp(el, t, { cps: 16 });  K.type(el, t, { cps: 30 });  K.draw(pathEl, t, 0.25);
 *   K.peel(wrapperEl, flapPolygonEl, gradEl, t0, dur, { w, h, dir: [-1, -0.8] });
 *   K.finish(masterTimeline, duration);                  // wires the stepped build clock + per-frame hooks
 * Builds (things being placed) are sampled at `step` fps; cameras, zooms and peels stay smooth at `fps`.
 */
(function () {
  const Collage = {};

  Collage.rng = function (seed) {
    let s = (seed * 2654435761) >>> 0 || 1;
    return function () {
      s = (s + 0x6D2B79F5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  /* Torn edge as a CSS polygon: points along each edge in %, depth in px, one point per ~`seg` px of the
   * element's size (w,h) so short edges don't turn into a saw. Low-frequency wander + fibre jag.
   * edges: any of "t","r","b","l" (others straight). */
  Collage.tornPolygon = function ({ amp = 9, seed = 1, edges = "trbl", w = 900, h = 900, seg = 9 } = {}) {
    const r = Collage.rng(seed), pts = [];
    const nW = Math.max(4, Math.round(w / seg)), nH = Math.max(4, Math.round(h / seg));
    const depth = (on, n) => {
      const out = [];
      let w = r();
      for (let i = 0; i <= n; i++) {
        w = 0.82 * w + 0.18 * r();
        out.push(on ? amp * (0.15 + 0.85 * w) + amp * 0.45 * (r() - 0.5) + amp * 0.5 : 0);
      }
      return out.map((v) => Math.max(0, v));
    };
    const T = depth(edges.includes("t"), nW), R = depth(edges.includes("r"), nH);
    const B = depth(edges.includes("b"), nW), L = depth(edges.includes("l"), nH);
    const f = (v) => v.toFixed(2);
    // corners are shared points at both edges' depth (a free corner would stick out as a spike)
    const TL = `${f(L[nH])}px ${f(T[0])}px`, TR = `calc(100% - ${f(R[0])}px) ${f(T[nW])}px`;
    const BR = `calc(100% - ${f(R[nH])}px) calc(100% - ${f(B[0])}px)`, BL = `${f(L[0])}px calc(100% - ${f(B[nW])}px)`;
    pts.push(TL);
    for (let i = 1; i < nW; i++) pts.push(`${f(i * 100 / nW)}% ${f(T[i])}px`);
    pts.push(TR);
    for (let i = 1; i < nH; i++) pts.push(`calc(100% - ${f(R[i])}px) ${f(i * 100 / nH)}%`);
    pts.push(BR);
    for (let i = 1; i < nW; i++) pts.push(`${f(100 - i * 100 / nW)}% calc(100% - ${f(B[i])}px)`);
    pts.push(BL);
    for (let i = 1; i < nH; i++) pts.push(`${f(L[i])}px ${f(100 - i * 100 / nH)}%`);
    return `polygon(${pts.join(",")})`;
  };

  /* Wobbly hand-drawn stroke (marker underline, arrow shaft) from (x0,y0) to (x1,y1). */
  Collage.wobble = function (x0, y0, x1, y1, { seed = 1, amp = 3, bow = 0 } = {}) {
    const r = Collage.rng(seed), n = 8, p = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n, x = x0 + (x1 - x0) * u, y = y0 + (y1 - y0) * u + Math.sin(Math.PI * u) * bow;
      p.push([x + (i && i < n ? (r() - 0.5) * amp : 0), y + (i && i < n ? (r() - 0.5) * amp : 0)]);
    }
    let d = `M${p[0][0].toFixed(1)},${p[0][1].toFixed(1)}`;
    for (let i = 1; i < p.length; i++) {
      const [ax, ay] = p[i - 1], [bx, by] = p[i];
      d += ` Q${ax.toFixed(1)},${ay.toFixed(1)} ${((ax + bx) / 2).toFixed(1)},${((ay + by) / 2).toFixed(1)}`;
    }
    return d + ` L${p[n][0].toFixed(1)},${p[n][1].toFixed(1)}`;
  };

  /* Half-plane clip of a polygon (Sutherland–Hodgman): keep points with (p-q)·n >= 0. */
  function clipHalf(poly, q, n) {
    const out = [], side = (p) => (p[0] - q[0]) * n[0] + (p[1] - q[1]) * n[1];
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length], sa = side(a), sb = side(b);
      if (sa >= 0) out.push(a);
      if ((sa >= 0) !== (sb >= 0)) { const u = sa / (sa - sb); out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]); }
    }
    return out;
  }

  Collage.init = function ({ fps = 30, step = 15 } = {}) {
    const K = { fps, step, build: gsap.timeline({ paused: true }), hooks: [] };
    const q = (t) => Math.floor(t * step + 1e-4) / step;       // stop-motion sampling of the build clock
    K.q = q;

    K.torn = function (el, opts = {}) {            // measures the box (explicit CSS size → exact at script time)
      const o = Object.assign({ w: el.offsetWidth || 900, h: el.offsetHeight || 900 }, opts);
      el.style.clipPath = Collage.tornPolygon(o); return el;
    };

    /* Entrances on the stepped build timeline. Elements are hidden until t, then placed in few frames. */
    K.enter = function (el, kind, t, o = {}) {
      const rot = o.rot || 0, d = o.dur;
      gsap.set(el, { rotation: rot, autoAlpha: 0 });
      K.build.set(el, { autoAlpha: 1 }, t);
      const B = K.build;
      switch (kind) {
        case "drop":   // falls onto the page, overshoots, settles
          B.fromTo(el, { y: o.from ?? -140, rotation: rot + (o.spin ?? 9), scale: 1.1 },
            { y: 0, rotation: rot, scale: 1, duration: d ?? 0.33, ease: "back.out(2)", immediateRender: false }, t); break;
        case "slap":   // thrown down flat: big to small, a little spin
          B.fromTo(el, { scale: o.from ?? 1.35, rotation: rot + (o.spin ?? -6) },
            { scale: 1, rotation: rot, duration: d ?? 0.2, ease: "power4.out", immediateRender: false }, t); break;
        case "slide":  // enters from an edge; o.dx / o.dy in px
          B.fromTo(el, { x: o.dx ?? 900, y: o.dy ?? 0, rotation: rot + (o.spin ?? 6) },
            { x: 0, y: 0, rotation: rot, duration: d ?? 0.4, ease: "back.out(1.3)", immediateRender: false }, t); break;
        case "stretch": // tape: unrolls from one end
          B.fromTo(el, { scaleX: 0, transformOrigin: o.origin ?? "0% 50%" },
            { scaleX: 1, duration: d ?? 0.14, ease: "power2.out", immediateRender: false }, t); break;
        case "pop":
          B.fromTo(el, { scale: 0 }, { scale: 1, duration: d ?? 0.25, ease: "back.out(3)", immediateRender: false }, t); break;
        case "rise":   // word rises out of its baseline mask (parent needs overflow:hidden)
          B.fromTo(el, { yPercent: 105 }, { yPercent: 0, duration: d ?? 0.3, ease: "power3.out", immediateRender: false }, t); break;
        default: throw new Error("unknown entrance " + kind);
      }
      return t + (d ?? 0.3);
    };

    function chars(el) {
      if (el._chars) return el._chars;
      const walk = (node) => {
        [...node.childNodes].forEach((c) => {
          if (c.nodeType === 3) {
            const frag = document.createDocumentFragment();
            [...c.textContent].forEach((ch) => {
              if (ch === "\n") { frag.appendChild(document.createElement("br")); return; }
              const s = document.createElement("span"); s.textContent = ch; s.style.display = "inline-block";
              if (ch === " ") s.style.whiteSpace = "pre";
              frag.appendChild(s);
            });
            c.replaceWith(frag);
          } else if (c.nodeType === 1) walk(c);
        });
      };
      walk(el);
      el._chars = [...el.querySelectorAll("span")].filter((s) => !s.children.length);
      return el._chars;
    }
    K.chars = chars;

    /* Headline stamp: letters land one by one (stop-motion), each a touch big then set. Returns end time. */
    K.stamp = function (el, t, { cps = 16, from = 1.25 } = {}) {
      const cs = chars(el).filter((c) => c.textContent.trim());
      gsap.set(el, { autoAlpha: 1 });
      cs.forEach((c, i) => {
        const ti = t + i / cps;
        gsap.set(c, { autoAlpha: 0 });
        K.build.set(c, { autoAlpha: 1 }, ti);
        K.build.fromTo(c, { scale: from, y: -6 }, { scale: 1, y: 0, duration: 1.5 / step, ease: "none", immediateRender: false }, ti);
      });
      return t + cs.length / cps;
    };

    /* Typewriter for mono notes, headers and captions (no scale). */
    K.type = function (el, t, { cps = 30 } = {}) {
      const cs = chars(el);
      gsap.set(el, { autoAlpha: 1 });
      cs.forEach((c, i) => { gsap.set(c, { autoAlpha: 0 }); K.build.set(c, { autoAlpha: 1 }, t + i / cps); });
      return t + cs.length / cps;
    };

    /* Marker / pen stroke drawing itself (SVG path with a stroke). */
    K.draw = function (path, t, dur = 0.25) {
      const L = path.getTotalLength();
      path.style.strokeDasharray = `${L} ${L}`;
      gsap.set(path, { visibility: "hidden" });                      // a round cap on a 0-length dash is a dot
      K.build.set(path, { visibility: "visible" }, t);
      K.build.fromTo(path, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: dur, ease: "power1.inOut" }, t);
      return t + dur;
    };

    /* Page peel: `wrap` (the outgoing layer, full frame w×h) is clipped by a fold line that travels from the
     * corner opposite `dir`; `flap` (SVG polygon) is the reflected back of the paper, shaded by `grad`
     * (an SVG linearGradient, gradientUnits=userSpaceOnUse). Smooth, not stepped. */
    K.peel = function (wrap, flap, grad, t0, dur, { w, h, dir = [-1, -0.8], ease = "power2.in" } = {}) {
      const m = Math.hypot(dir[0], dir[1]), n = [dir[0] / m, dir[1] / m];
      const corner = [n[0] < 0 ? w : 0, n[1] < 0 ? h : 0];
      const span = Math.abs(n[0]) * w + Math.abs(n[1]) * h;           // corner-to-corner along n
      const rect = [[0, 0], [w, 0], [w, h], [0, h]], E = gsap.parseEase(ease);
      K.hooks.push(function (t) {
        const u = Math.min(1, Math.max(0, (t - t0) / dur));
        if (u <= 0) { wrap.style.clipPath = "none"; flap.setAttribute("points", ""); return; }
        const s = E(u) * span * 2.05;                                   // x2: the flap must clear the frame too
        const qp = [corner[0] + n[0] * s, corner[1] + n[1] * s];
        const keep = clipHalf(rect, qp, n);
        const lifted = clipHalf(rect, qp, [-n[0], -n[1]]).map((p) => {
          const d = (p[0] - qp[0]) * n[0] + (p[1] - qp[1]) * n[1];
          return [p[0] - 2 * d * n[0], p[1] - 2 * d * n[1]];
        });
        wrap.style.clipPath = keep.length ? `polygon(${keep.map((p) => `${p[0].toFixed(1)}px ${p[1].toFixed(1)}px`).join(",")})` : "polygon(0 0,0 0,0 0)";
        flap.setAttribute("points", lifted.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" "));
        grad.setAttribute("x1", qp[0]); grad.setAttribute("y1", qp[1]);
        grad.setAttribute("x2", qp[0] + n[0] * 420); grad.setAttribute("y2", qp[1] + n[1] * 420);
      });
    };

    /* Seeded per-step jitter of a texture layer's position (grain boil). */
    K.boil = function (el, size = 512) {
      K.hooks.push(function (t) {
        const f = Math.floor(t * step + 1e-4), h = Math.sin(f * 12.9898) * 43758.5453, r = h - Math.floor(h);
        el.style.backgroundPosition = `${Math.floor(r * size)}px ${Math.floor(((r * 7.13) % 1) * size)}px`;
      });
    };

    /* One proxy tween drives the stepped build clock and every per-frame hook. Call last. */
    K.finish = function (tl, dur) {
      const clock = { t: 0 };
      tl.to(clock, {
        t: dur, duration: dur, ease: "none",
        onUpdate() { K.build.seek(q(clock.t), false); K.hooks.forEach((h) => h(clock.t)); }
      }, 0);
      K.build.seek(0, false); K.hooks.forEach((h) => h(0));
    };
    return K;
  };

  window.Collage = Collage;
})();
