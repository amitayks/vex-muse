---
name: rotoscope-paint
description: Draw over generated video plates in JavaScript so only the painting is seen - extract per-frame guides from a plate (subject mattes, traced contours, keyframe poses, camera motion, dominant colors), convert them to time-indexed JSON the p5 studio reads, and repaint characters and sets as boiled brush shapes that inherit the plate's performance and physics. Use in phase 7 when a shot's technique is plate+overlay, or whenever real motion should drive hand-painted animation.
license: MIT
compatibility: tools/env.sh ($PY with opencv/numpy, ffmpeg); fal-media for mattes (bria video background removal).
metadata:
  author: muse
  version: "1.1.0"
---

# rotoscope-paint — shoot first, draw over

The plate is reference, never picture (unless the storyboard says so). The
viewer sees brush, paper and ink; the plate lends timing, weight and
performance.

## Guides (script: `scripts/roto.py`)
1. Frames: `roto.py frames <plate.mp4> <dir> --fps 12` (paint on twos; 12
   fps guides are enough and halve cost).
2. Mattes: `fal.py run bria/video/background-removal/v3` on the plate →
   alpha video; `roto.py frames` it too. Per character when several: crop
   regions or run a second pass on a masked plate.
3. Contours: `roto.py trace <alpha_dir> <out.json> --eps 2.5 --min-area 400`
   → per frame: simplified polygons (outer silhouette + holes), bbox,
   centroid. Smooth across time (`--smooth 2`) so boil comes from my seed,
   not from matte flicker.
4. Motion: `roto.py flow <plate.mp4> <out.json>` → global camera
   translation/zoom per frame (to drive `camBegin`) and the subject's
   centroid path.
5. Colors: `roto.py palette <frames_dir>` → 5 dominant colors per shot,
   snapped to the bible palette.
6. Keyframes for acting: I read a 12 fps strip of the plate and write key
   poses (head tilt, arm angles, mouth shape on words) into
   `guides/<id>_keys.json` — the eye beats any detector on expression.

## Painting over (in the studio)
- Load guides as JSON (`fetch` in setup; frames stay pure: index by
  `floor(t*12)`).
- Silhouette → `paint()` with wash + ink; interior features (face, hair
  mass, costume blocks) from the character sheet placed relative to the
  contour's bbox/keys; limbs as `ribbon()` along traced medial lines when
  needed.
- Background: repaint the set from its set image as layered watercolor
  shapes (cached per shot), moved by the plate's camera path.
- Keep the plate hidden; turn it on at 20% opacity only for alignment
  checks (`?onion=1`), never in renders.

## Vector route (faster than brush)
The same per-frame contours can become simplified SVG paths animated in HyperFrames (skill
`svg-transform`: MorphSVG between key poses, seeded boil at 8–12 fps) — hand-drawn feel at
HyperFrames speed (~11 fps capture here) instead of ~75 s per painted frame.

## Acceptance
Per shot: guides JSON exist for every 12 fps frame; an onion-skin check
sheet shows the painting tracking the plate (silhouette within a few px,
mouth shapes on words); the final sheet shows no plate pixels; the
painted character is on model with the sheet.
