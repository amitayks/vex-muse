---
kind: project
seen: 2026-10-07
tags: [lab, shaders, webgpu, hyperframes, beat-sync]
---
# lab-shaders: Shaders (WebGPU) in the studio, and LEVELS

**Brief.** the principal sent the @npm_i_shaders post (x.com/npm_i_shaders/status/2107467668009963819): Shaders goes open source, with 200+ WebGPU components. His words: "That has to get in our tools. Let's learn how to use this. Do something amazing." No cap was given. Muse made **LEVELS**: 33.6 s, 1920×1080, 60 fps, on Avicii's "Levels" from 7.906 s (17 bars at 126 BPM, the intro lead into the first drop, plus 1.2 s of the chorus under a fade so the end card holds). One torus climbs 23 shader "levels".
- **Build:** one material per bar (Glass, Chrome, LiquidMetal, Plastic), then one per half-bar, then one per beat into the drop. Voxels lands on the last beat as an 8-bit nod.
- **Drop:** each bar is a world made by nesting filters on the same torus (Kaleidoscope, Halftone, Dither, Glass over a Prism beam, CRT, Repeater, Nebula), with a kick pulse on every beat. In bar 16, "MAX", the kaleidoscope gains segments on each beat (6 → 8 → 12 → 24).
- **End card:** the torus eases back to the exact pose and world of frame 1, with "ONE SHAPE. 23 LEVELS. ALL CODE."
- A HUD names the live component tree (`<Dither><Plastic /></Dither>`), so the piece also teaches the library.

After delivery the principal asked "cost?" and then "lets make it skill". The method became skill `webgpu-shaders`: a one-command scaffold on the song's beats, the driver, a catalog of all 199 components that blocks the 28 unsafe here, a small look grid, a determinism gate and the Modal render. A rebuild script reproduces the driver bundle byte for byte, so a Shaders upgrade is one command plus the checks. The principal's personal agent installed the skill and passed its local test. Its Modal render needs render-review's `modal_hf.py`, which the first copy did not carry; the skill now declares that dependency.

**What worked**
- The library is fast to learn. `llms-full.txt` lists every prop, and all 21 non-simulation shape materials rendered on the first try (`projects/lab-shaders/review/material-grid.jpg`).
- A 200-line driver (`src/hf-shaders.js`) makes the output frame-exact. It renders synthetic frames at absolute times and blocks the engine's own stray renders. Shuffled seeks give pixels identical to sequential seeks. The method is in [[shaders-webgpu]].
- Modal 8-CPU containers render it fast: 972 frames at 30 fps in 110 s wall, and the 2016-frame 60 fps master in 154 s over 48 chunks, with no page errors.
- Sync comes by construction: every level change sits on a `song.json` beat. The measured drop kicks land 23–29 ms after the grid, and 30 of 32 are within one frame.
- A flat colour field per level (ink, paper, red, plum, navy) plus a level-up ring makes each material change read as an event, not as a slideshow.

**What didn't**
- The HyperFrames Chrome flags (ANGLE-SwiftShader GL) give a white, empty WebGPU canvas. Only SwiftShader on Vulkan presents, and `hyperframes render` cannot render these comps here.
- The ring went edge-on twice. v1's full Y spin read as a "pill" about every 3.7 s. v2's "in-plane" Z spin did the same, because in shaders@4 the torus axis is +Y and every Euler angle tilts it. v3 keeps the pose near face-on (rotX 90±25, rotY and rotZ ±18).
- Other review faults: the HUD sat under the slides, Dither over dark Chrome lost the shape, and the HUD tag was too small for a phone. The opening grew from zero, so frame 0 (the thumbnail) was black. The end card held only about 1 s before the section ended. The audio cut clicked. The fixes: HUD z-index, Dither over white Plastic, a 40 px tag, a whole first scene at frame 0, 1.2 s more audio under a fade, and a 10 ms fade-in.
- Cancelling a local Modal render left its app running, and its containers billed about $0.40 until `modal app stop` ([[tool-selection]]).
- The frame study measures 5 % holds, because the hero object never stops moving. This is accepted here: the reads are the level changes on the beat, not still frames.

**Spend.** About $1.50 of Modal CPU time, $0 in generation; Shaders is MIT. The test and the v1–v3 drafts took about $0.60, the 60 fps master about $0.45, and the orphaned app wasted about $0.40. These are estimates from container time, not a Modal bill. One render of a piece this size costs about $0.20 at 30 fps and $0.45 at 60 fps. Ledger: `projects/lab-shaders/ledger.jsonl`.

**Final.** The master is `projects/lab-shaders/renders/levels_v4_master_1080p60.mp4`: 1920×1080, 60 fps, 33.6 s, 2016 frames, CRF 16, 37.5 MB, −13.7 LUFS. Reviews: `projects/lab-shaders/review/v3.md` and `v4.md`. The comp source is `projects/lab-shaders/motion/levels-src/`, built with `python3 projects/lab-shaders/build.py`. A 720p preview went to the principal on WhatsApp. The full master went to his web chat as the unchanged file with `send_file`, through a session prompt from the WhatsApp session. At 37.5 MB, it is below the web chat's 64 MB limit. Engine row: [[tool-selection]].

## How the principal works with this
- He sends a launch post with "That has to get in our tools… do something amazing". He wants the tool adopted and a showpiece that proves it, not only a verdict.
- After a delivery he asks "cost?". Answer with the total, the split per stage and any waste, and say whether the figures are estimates.
- When a new tool works, he says "make it skill": every adopted tool ends as a skill.
