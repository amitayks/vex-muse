---
name: svg-transform
description: Design and animate SVG transformations as storytelling - shape morphs (logo/icon/glyph/silhouette becomes another), line draws, motif-shaped masks and iris reveals onto footage, text on paths, hand-boiled vector lines, transform-gizmo overlays and higher-dimensional moves (a 4D object turned inside out or sliced into a lawful sequence of shapes) - choosing the right morph algorithm (GSAP MorphSVG, flubber, Remotion paths) and timing each transformation on the beat grid. Use whenever something should turn into something else, a mark or motif threads a video, a transition should be shape-driven instead of a crossfade, footage should be revealed through a shape, or vector contours from a plate should be animated.
license: MIT
compatibility: HyperFrames project with gsap MorphSVGPlugin/DrawSVGPlugin (code-motion), flubber for non-GSAP hosts, $PY for sheets.
metadata:
  author: muse
  version: "1.1.0"
---

# svg-transform — "this becomes that", drawn in vectors

Knowledge: [[svg-transformation]] (moves, algorithm test, timing grammar). Build host: skill
`code-motion` (HyperFrames). Recipes with code: `code-motion/references/recipes.md`.

## 1. Decide the sentence
Write each transformation as `A → B because <meaning>` on a beat, e.g. "dot → iris → next world",
"spark → circle → window onto the idol on 'P(doom)'", "glyph m → heart on the word 'love'". If the
meaning is missing, it is decoration: cut it. Max one transformation per beat; the result holds ≥1 beat.

## 2. Author the shapes
- One coordinate system for every shape of a family (e.g. 400×400, centred 200,200), absolute path
  commands, primitives converted to paths, clockwise, similar start point (top centre).
- Compound shapes: split into matching islands; unmatched islands fade or scale to 0.
- Brand marks / glyphs: trace or export to path; simplify (≤ ~200 nodes) before morphing.
- Contours from plates (`rotoscope-paint` extractor) → simplified paths per keyframe pose.

## 3. Pick the algorithm
- HyperFrames: GSAP `morphSVG: { shape, shapeIndex: "auto" }` (`map: "complexity"` for hard pairs; set a
  numeric `shapeIndex` when it twists). Lines: `DrawSVGPlugin` or `stroke-dasharray/offset`.
- Remotion / p5 / node: flubber `interpolate(a, b, { maxSegmentLength: 3–4 })`, `separate`/`combine`
  for 1↔many. `@remotion/paths interpolatePath` only for same-structure paths.
- Verify hard pairs first: render a t = 0, .25, .5, .75, 1 strip (template:
  `projects/lab-motion-tools/morphlab/`) and read it — no tearing, mass stays centred, the middle frame
  is still a shape.

## 4. Animate
- Morph 0.28–0.4 s `power3.inOut`, midpoint on the beat; flat fill switches hard at the midpoint.
- Optional ghosts (2–3 outline copies lagging 2 frames, 35–45 % opacity) and a gizmo (box, handles,
  pivot, `ROT` readout) rotating with the shape.
- Masks onto footage/scenes: morph an off-screen path and rebuild the wrapper's CSS
  `clip-path: path()` every frame (url(#clipPath) references don't survive capture). Iris past the
  frame: scale so radius ≥ half-diagonal (1101 px at 1080p).
- Boil (hand-made line): seeded per-frame offsets of control points, redrawn at 8–12 fps.
- Anything custom per frame is a pure function of `t` (called from the proxy tween) — no pre-roll.

## 4b. Higher-dimensional moves (when one thing must become a *lawful* series of shapes)
`assets/nd4.js` (pure, no deps; copy into the project's `assets/js/`): tesseract data, rotation in any
of the 6 planes, perspective 4D→3D→2D, hyperplane slices, 2D hull. Knowledge: [[tesseract]].
- **Inside-out turn**: 180° in XW/YW/ZW carries the inner cell out to become the outer one. Any turn
  that ends on 90° multiples lands on an identical pose — a bar-locked loop or a hidden cut point.
  Turn for 3 beats, land on a beat, hold.
- **Slice**: a 4D object crossing our space shows point → shape → point; one step per beat, landmark
  shapes (e.g. octahedron) on downbeats; its size can follow the energy curve. Colour faces by the
  cell they come from so the viewer sees the object *change sides*.
- Depth into the 4th direction → stroke weight (ink), never glow. Pick the camera angle by numeric
  search so the landmark beat shows its structure. Never the look: no spinning neon hypercube.

## 5. Check (the gate)
Snapshot the beat before, the morph midpoint and the beat after for every transformation; in the
frame study the midpoint frame reads as a designed shape, the result holds ≥1 beat, the colour switch
is clean, the mask edge never shows the wrong layer, and the transformation lands on its beat (±1 frame).

## Acceptance
Every transformation in the storyboard has its sentence, verified strip or snapshots, beat-accurate
timing and a clean midpoint; hard pairs were tested before use; masks cover the frame exactly when
the reveal completes.
