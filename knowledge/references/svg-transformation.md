---
kind: technique
tags: [svg, morph, path, mask, line-draw, text-on-path, gsap, flubber, remotion, hyperframes]
audience: all
half_life: 365
rights: safe
seen: 2026-09-26
---
# SVG transformation — shapes that become other shapes

Vector transformation is how motion design says "this *becomes* that" — the cheapest, cleanest
metaphor machine we have, and it never looks generated. In the reference showreels it carries the
motif (dot → iris → full stop), the craft chapter (circle → square → triangle → spark under a transform
gizmo) and the transitions ([[code-motion-showreels]]).

## The six moves
1. **Morph** — one outline interpolates into another (logo ↔ icon ↔ glyph ↔ silhouette). Meaning: identity
   change. Put the midpoint on a beat; switch fill colour *hard* at the midpoint.
2. **Draw** — stroke grows along its path (`DrawSVGPlugin`, or `stroke-dasharray/offset`,
   `@remotion/paths evolvePath`). Meaning: making, tracing, connecting. Pair with an end-cap dot.
3. **Mask / clip reveal** — footage or a scene seen through a shape that grows/morphs (the motif iris).
   Meaning: "enter the world of X". In HyperFrames use CSS `clip-path: path()` rebuilt per frame.
4. **Text on a path** — `<textPath>` on circles/curves; rotate the ring, shrink it into the motif.
5. **Stroke boil / hand line** — tiny per-frame jitter of control points (seeded) at 8–12 fps: vector
   that feels drawn (vector rotoscope from `rotoscope-paint` contours).
6. **Gizmo layer** — bounding box, handles, pivot crosshair, `ROT 101.2°` readout rotating with the
   shape: the design-tool in-joke that tells designers "this is crafted".

## Which morph algorithm (tested, `projects/lab-motion-tools/morphlab/morph_compare.png`)
| Pair | naive index lerp | `@remotion/paths` interpolatePath | flubber | GSAP MorphSVG (`shapeIndex:"auto"`) |
|---|---|---|---|---|
| circle → 11-ray spark (convex → star) | ok | ok | ok | ok |
| glyph "m" → heart (concave, different topology) | tears, drifts off-axis | tears, collapses one side | clean, symmetric | cleanest; reads as "m" longest |
Rules:
- Default **GSAP MorphSVG** in HyperFrames (free since 3.13; `shapeIndex:"auto"`, `map:"complexity"`
  for complex pairs; tune `shapeIndex` by number when it twists).
- **flubber** when outside GSAP (Remotion, p5, node precompute): `interpolate(a, b, {maxSegmentLength: 3–4})`;
  `separate/combine` for 1→many (one dot → eight dots).
- Never naive/`interpolatePath` for pairs with different topology; fine for same-structure paths.
- Compound shapes (holes, multiple islands): split into matching sub-paths first; morph pieces, fade
  the leftovers.
- Author source shapes centred in one viewBox (e.g. 400×400 centred 200,200) so morphs don't drift.
- Convert primitives (`circle`, `rect`) to paths; keep point order clockwise for both ends.

## Timing grammar for transformations
- One transformation per beat at most; hold the result ≥ 1 beat before the next (the read must land).
- 0.28–0.4 s `power3.inOut` for the morph itself; the object may keep a slow rotation through it.
- Ghost outlines (2–3 copies lagging 2 frames each, 35–45 % opacity) sell speed without motion blur.
- Colour: flat fills switch at the midpoint; never tween hues through RGB mud.

## Where each engine stands
- **HyperFrames**: MorphSVG/DrawSVG/MotionPath/SplitText all available; timeline-seekable; best home.
- **Remotion**: `evolvePath`, `interpolatePath` (weak on hard pairs), `@remotion/shapes`; use flubber
  for real morphs. Good when the shape list comes from data.
- **p5 studio**: sample the flubber interpolator per frame into brush strokes → painted morphs.

## Recipes proven in the lab
- Dot mitosis 1→2→4→8 on beats, collapse, iris into the next scene's colour (lab reel bar 1–2).
- MorphSVG gizmo chain circle → rounded square → triangle → spark with ghosts and ROT readout (bar 3).
- Spark-shaped window onto a Seedance plate, growing on lyric onsets, morph to circle, iris past the
  frame edge (half-diagonal 1101 px ⇒ scale ≥ 6.2 for r=180) (lab combo).
