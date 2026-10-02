# Recipes (HyperFrames + GSAP), each proven in `projects/lab-motion-tools/`

Full working sources: `assets/reel-template/index.src.html` (lab reel) and
`projects/lab-motion-tools/combo-src/index.src.html` (plate + mask + Remotion alpha).

## Skeleton
```html
<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080" data-duration="8.1" data-fps="30">
  <audio id="bgm" data-start="0" data-duration="8.1" data-track-index="9" data-volume="1" src="assets/song.wav"></audio>
  <section id="sA" class="clip" data-start="0" data-duration="1.875" data-track-index="0">…</section>
</div>
<script>
const BPM = 128, B = 60 / BPM, at = (bar, beat = 0) => (bar * 4 + beat) * B;
const tl = gsap.timeline({ paused: true });
/* …tweens… */
window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;   // synchronous
</script>
```
Scenes are `.clip` sections; the root background equals the outgoing scene's field so a scene can end
on the motif alone and the next can begin with the motif expanding.

## Frame-pure proxy (HUD, timecode, grain, custom effects)
```js
const hud = { t: 0 };
tl.to(hud, { t: DUR, duration: DUR, ease: "none", onUpdate() {
  const t = hud.t, f = Math.round(t * FPS);
  tc.textContent = `TC 00:00:${String(Math.floor(f / FPS)).padStart(2, "0")}:${String(f % FPS).padStart(2, "0")}`;
  const h = Math.sin(f * 12.9898) * 43758.5453, r = h - Math.floor(h);           // seeded per-frame noise
  grain.style.backgroundPosition = `${Math.floor(r * 512)}px ${Math.floor((r * 7.13 % 1) * 512)}px`;
  wavesAt(t);                                                                    // any effect = f(t)
} }, 0);
```
Grain: 512² gaussian PNG, `mix-blend-mode:overlay; opacity:.08`, jittered per frame. HUD colour follows
the field (set a CSS var from `t`), never `mix-blend-mode:difference` (reads cyan on red).

## Iris from the motif (scene change in ~100 ms)
```js
tl.fromTo("#iris", { attr: { r: 14 } }, { attr: { r: 1150 }, duration: 0.16, ease: "expo.in" }, at(1));
tl.fromTo("#ring", { attr: { r: 18 }, opacity: 1 }, { attr: { r: 1180 }, opacity: .2, duration: .18, ease: "expo.in" }, at(1));
```
`#iris` is an SVG circle in the incoming scene filled with its field colour; half-diagonal of 1080p is
1101 px.

## Per-letter mask rise / arc-in / brackets / whip
```js
tl.fromTo(letters, { yPercent: 110 }, { yPercent: 0, duration: .34, ease: "expo.out", stagger: .028 }, t);
tl.fromTo(letters2, { yPercent: -140, rotation: -35, opacity: 0 }, { yPercent: 0, rotation: 0, opacity: 1, duration: .42, ease: "back.out(2.2)", stagger: .035 }, t + B);
tl.fromTo(".brk", { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 1, duration: .14, ease: "power3.out", stagger: .02 }, t + B + .3);
tl.fromTo("#line", { x: 0 }, { x: -46, duration: .18, ease: "power3.in" }, t + 2 * B - .1);  // whip out…
tl.to("#line", { x: 0, duration: .3, ease: "expo.out" }, t + 2 * B + .08);                   // …and settle
```
Mask = the word's wrapper with `overflow:hidden` and bottom padding for descenders (`.06em` grotesk,
`line-height:1.12` italic serif). Only the word clips, never the line (brackets live outside it).

## Push-in into the cut (velocity match)
`tl.fromTo("#block", { scale: 1 }, { scale: 2.3, duration: B * 1.4, ease: "power4.in" }, cutTime - B * 1.4)`
then hard cut on the downbeat: the fastest point of the push meets the cut.

## Dot lands as the full stop (motif payoff)
Measure the target every frame (font-safe), fly on a parabola, squash on the downbeat:
```js
tl.to(fly, { p: 1, duration: land - t0, ease: "none", onUpdate() {
  const [tx, ty] = target(), p = fly.p, e = gsap.parseEase("power1.inOut")(p);
  dot.setAttribute("cx", 960 + (tx - 960) * e);
  dot.setAttribute("cy", p < .6 ? 540 + (230 - 540) * gsap.parseEase("power2.out")(p / .6) : 230 + (ty - 230) * gsap.parseEase("power3.in")((p - .6) / .4));
} }, t0);
tl.to(dot, { scaleX: 1.5, scaleY: .6, transformOrigin: "50% 100%", duration: .06 }, land);
tl.to(dot, { scaleX: 1, scaleY: 1, duration: .35, ease: "elastic.out(1.2,.4)" }, land + .06);
```
Keep the flight short (≤ 1 beat): a dot drifting in the air for a bar reads as floaty (M2).

## Window onto footage (motif-shaped clip)
`clip-path:url(#clipPath)` does not survive capture; rebuild a CSS `path()` each frame from the
(morphing) SVG path, transformed to frame coordinates:
```js
const xform = d => { const a = T.r * Math.PI / 180, c = Math.cos(a) * T.s, n = Math.sin(a) * T.s, out = []; let buf = [];
  for (const tok of d.match(/[A-Za-z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g)) {
    if (/[A-Za-z]/.test(tok)) { out.push(tok); continue; } buf.push(+tok);
    if (buf.length === 2) { const x = buf[0] - 200, y = buf[1] - 200; out.push(`${960 + c * x - n * y},${540 + n * x + c * y}`); buf = []; } }
  return out.join(" "); };
mask.style.clipPath = `path("${xform(winPath.getAttribute("d"))}")`;   // call from every tween's onUpdate
```
(absolute M/L/C/Q/Z paths only — MorphSVG output qualifies).

## Seeded camera shake
`const h = n => { const x = Math.sin(n * 91.7 + 3.1) * 43758.5; return x - Math.floor(x) - .5; }` →
amplitude decays over 0.3 s, new offset every 1/9 of it; reset x/y with a `tl.set` after.

## Colour hard-switch in a morph
`tl.to(shape, { morphSVG: {...}, duration: .36 }, t); tl.set(shape, { attr: { fill: next } }, t + .16);`

## Remotion alpha layer in HyperFrames
`<video id="lyr" data-start="0" data-duration="4" data-track-index="2" data-volume="0" src="assets/lyric.webm" muted playsinline>`
positioned `inset:0` above the plate. Every `<audio>`/`<video>` needs an `id`; no `crossorigin`.
