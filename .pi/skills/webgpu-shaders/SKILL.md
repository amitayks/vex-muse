---
name: webgpu-shaders
description: Put GPU shader effects into a video, frame-exact, with the open-source Shaders library (shaders.com, npm `shaders`, 199 WebGPU components, MIT) - raymarched materials on 3D shapes (glass, chrome, liquid metal, holographic foil, neon, voxels, water, obsidian, frost, plastic), shader backgrounds (flowing/mesh gradients, aurora, light beams), full-frame filters (halftone, dither, CRT, kaleidoscope, chromatic aberration, repeater, glow, film grain) and shader transitions (iris, page peel, dissolves) - as a seekable layer in a HyperFrames comp, beat-synced, verified deterministic and rendered on Modal CPU containers (this box has no GPU). Use when a shot's read is a material or a shader look, when the principal names Shaders or shaders.com, asks for "glass / chrome / liquid metal / holographic" motion, a WebGPU effect, a shader background or filter, or when upgrading the shaders package.
license: MIT
compatibility: HyperFrames comp (skill code-motion), tools/env.sh (CHROME_PATH, $PY with Pillow), puppeteer-core in <workspace>/studio, Modal tokens for renders, npm for driver rebuilds. Full renders need skill render-review >= 1.6.1 (scripts/modal_hf.py with --webgpu --cpu); ship it with this skill.
metadata:
  author: muse
  version: "1.1.1"
---

# webgpu-shaders — a shader layer that is a pure function of t

Components, shapes, filters and what to avoid: [references/components.md](references/components.md).
How the driver works and why our own capture: [references/determinism.md](references/determinism.md).
Engine choice per shot: [[tool-selection]]. Comp craft (timeline, fonts, lint): skill `code-motion`.

## 1. Scaffold the comp
```bash
source tools/env.sh
python3 .pi/skills/webgpu-shaders/scripts/init_comp.py <src_dir> <comp_dir> --font <face.ttf> \
  --dur <s> --song <song.json> --t0 <song s>      # or --bpm <n> without a song
# put the cut mix at <comp_dir>/assets/audio/mix.wav (skill track-edit), then build:
python3 .pi/skills/code-motion/scripts/hf_build.py <src_dir>/index.src.html <comp_dir>
```
`<src_dir>/index.src.html` is the working source: one shader layer under DOM type, beats in
`window.BEATS` (comp seconds). Edit the source, never the built comp.

## 2. Design the look before the timeline
- Find components: `$PY .pi/skills/webgpu-shaders/scripts/catalog.py list|show <Name>|materials|safe`.
  Use only components that `safe` lists (no SIM, NET or INPUT).
- Compose a preset as JSON: generators first, filters wrap their `children`, every node has a
  stable `id`. Prove each look at small size before it enters the comp:
  `node .pi/skills/webgpu-shaders/scripts/material_grid.mjs <specs.json> <outDir>` → `_sheet.jpg`.
- A flat, contrasting field behind a material reads better than a busy one; switch fields hard on
  beats. Type is DOM, over the canvas (never the `Text` component).
- Photos and plates: `ImageTexture` with a **data: URL** (fetch cannot read `file://`, and a remote URL
  ties the render to the network). Cover-crop the image to the canvas size first, `objectFit: 'fill'`.
  Print filters (Halftone `cmyk`, Engraving, Tritone, Dither, Chalkboard) inked in brand colours turn
  any photo into an on-brand print, and they hide upscaling. Halftone's ink/paper colours apply only
  to `style: 'cmyk'`.

## 3. Wire it to time
- One `<canvas>` per preset. `const fx = HFShaders.mount(canvas, PRESET, {width, height})`.
  Several presets: pass one shared device (`opts.gpu`, created with the adapter's features), and let
  `frame` return only the layers visible at t (hidden canvases then cost nothing).
- `HFShaders.bindToHyperFrames(fx | [fx...], (t, layers) => layer.set(id, props))`, called
  synchronously at load. Per frame, `set` any prop as a pure function of t (shape pose, `scale`,
  `center`, filter strengths, `segments`, `opacity`).
- Keep every `speed` prop constant for the whole mount. Never change compile-time props mid-timeline
  (shape `type`, `visible`, select props): mount a second preset and swap canvases in the DOM.
- Beat sync: changes land on `BEATS[i]`; kicks as `exp(-(t - beat) * 9)` on a scale or a strength.
- Bound 3D poses near the readable angle (a torus face-on: rotX 90 ± 25, rotY and rotZ ± 18).

## 4. Look, then prove determinism
- Stills: `node .pi/skills/webgpu-shaders/scripts/webgpu_snap.mjs <comp>/index.html <outDir> t1 t2 …`
  (`hyperframes snapshot` cannot render WebGPU here). Read every still.
- Lint: `npx hyperframes lint <comp>` → 0 errors (keep libraries as external `<script src>`).
- Gate: `node .pi/skills/webgpu-shaders/scripts/check_determinism.mjs <comp>/index.html` → `PASS`.
  A FAIL means a stray clock: a changing `speed`, a SIM component, `Math.random`/`Date.now`, or
  per-frame code outside `frame(t)`.

## 5. Render on Modal
```bash
HF_COMP=<comp_dir> $PY -m modal run .pi/skills/render-review/scripts/modal_hf.py --comp <comp_dir> \
  --timeline main --duration <s> --out <mp4> --audio <mix.wav> --fps 30 --chunks 32 --webgpu --cpu 8
```
~2 min and ~$0.20 for 32 s of 1080p30 (60 fps: ~$0.45). Draft at 30 fps, master at 60 after the
review passes (skill `render-review`). If a run is cancelled, stop its app:
`$PY -m modal app list` → `modal app stop <id> --yes`.

## 6. Upgrade the library
`.pi/skills/webgpu-shaders/scripts/build_driver.sh <version>` rebuilds the bundle (temp dir, pinned
esbuild), then `catalog.py refresh`. Re-run `check_determinism.mjs` and `material_grid.mjs` on the
looks in use before any comp ships with the new bundle; copy the bundle into each comp's `assets/js`.

## Acceptance
- `check_determinism.mjs` prints PASS on the final comp; lint 0 errors.
- Every preset uses only `safe` components; no `speed` changes after mount.
- Stills read at every planned beat; the shader layer is visible (not blank) in the Modal render;
  every Modal chunk reports `errs: 0`.
