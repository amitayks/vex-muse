# lab-motion-tools
Engine tests for code-made motion (2026-09-26). Toolchains installed here: `node_modules/` (hyperframes 0.8.78,
gsap 3.15, flubber 0.4.2) and `rm/node_modules/` (remotion 4.0.529 + paths/shapes/noise/media-utils).

- `hf-src/` → `hf/` — HyperFrames lab reel (4 bars @128 BPM). Build: `python3 ../../.pi/skills/code-motion/scripts/hf_build.py hf-src/index.src.html hf`
- `rm/` — Remotion: `Reel` (flubber morph + words on beats), `Lyric` (transparent VP9 lyric layer from song.json props)
- `combo-src/` → `combo/` — Seedance plate (pdoom S1) through a morphing spark mask + Remotion alpha lyrics + HUD, composited in HyperFrames
- `morphlab/` — morph-algorithm comparison (naive / @remotion/paths / flubber / GSAP MorphSVG)
- `renders/` — hf_test_v1..v3, rm_test_v1, rm_lyric_alpha.webm, combo_v1 · `review/` — framestudy output per render
- `tesseract-src/` → `tesseract/` — the 4D cube as technique (2026-09-26, $0). `bash tesseract-src/build.sh turn|slice`
  (copies `svg-transform/assets/nd4.js`, then hf_build; one project dir, the two tests take turns).
  `turn`: true 4D rotation (build on beats → XW 180° → YW 180° → XY+ZW isoclinic), projected to SVG, depth = pen weight.
  `slice`: a tesseract crossing our space (point → tetrahedron → truncated → octahedron → back) beside a cube crossing a
  flat world. Renders `renders/tesseract_{turn,slice}_v1.mp4` (first draft, trend palette) and `_v2.mp4` (fixed);
  reviews in `review/tesseract-{turn,slice}/`. Notes: `knowledge/references/tesseract.md`.
