---
name: code-motion
description: Build motion graphics entirely in code - kinetic typography, graphic/showreel chapters, UI and HUD chrome, beat-synced montages, shape and particle chapters, and the final composite of a music video - with HyperFrames (HTML/CSS/SVG + GSAP, the default compositor) and Remotion (React, data-driven or transparent layers), authored on the song's beat grid and verified by frame study. Use for any shot whose read is words, graphics or design (not a filmed performance), when compositing plates/painted/Remotion layers into one cut, when a request references "Opus/Claude-made motion graphics", showreels, lyric videos, title sequences, or when choosing HyperFrames vs Remotion vs p5 vs generation.
license: MIT
compatibility: Node 22+ (hyperframes, remotion, gsap, flubber installed per project), tools/env.sh (ffmpeg, CHROME_PATH, $PY).
metadata:
  author: muse
  version: "1.2.0"
---

# code-motion — the frame is a function of time, and I write the function

Reference bar: [[code-motion-showreels]] — take its craft principles, never its look (fingerprint list
there; the look comes from `style-bible` → Divergence). Engine choice:
[[tool-selection]]. Shape work: skill `svg-transform`. Craft vocabulary: `references/craft.md`.

## 1. Brief the motion before any code
Fill `references/motion-brief.md` into `projects/<slug>/motion-brief.md` (or the storyboard's code
shots): the one feeling, tempo + bar count, motif and its three jobs (open / transition / end), palette
(4–5 hex + paper), type system (from the bible), chapter list (one craft per 1–2
bars), rhythm plan shaped by this song's energy, transition rule, texture, frame chrome (or none),
end card that rhymes with frame 1. A chapter without a named verb and event is not designed yet.

## 2. Choose the engine per layer
HyperFrames = master timeline and compositor (song, grid, transitions, HUD, grain, encode). Remotion =
layers that are data-driven, spring-physics or audio-reactive → transparent VP9 WebM. p5 = painted
layers. Seedance = performance plates. All layers read the same `song.json`.

## 3. Build (HyperFrames)
- Install once per project dir (pinned): `npm i -D hyperframes@0.8.78 gsap@3.15.0 flubber@0.4.2`;
  Remotion layers: copy `projects/lab-motion-tools/rm/` (package.json + src) and `npm i`.
  Working installs live in `projects/lab-motion-tools/` (`node_modules`, `rm/node_modules`).
- Project: `projects/<slug>/motion/<comp>/` created from `assets/reel-template/` — mechanics only; every visual in it is the study replica and gets replaced (copy
  `hyperframes.json`, `assets/js/*`, fonts). Editable source lives in `<comp>-src/index.src.html`
  (outside the project dir); build with
  `python3 .pi/skills/code-motion/scripts/hf_build.py <comp>-src/index.src.html <comp>` — it injects
  fonts as bytes (URL font loads fail on this box) and strips Studio ids.
- Time in beats only: `const B = 60/BPM, at = (bar, beat=0) => (bar*4+beat)*B`; lyric shots read word
  onsets from `song.json` (never retype).
- One paused `gsap.timeline`, registered synchronously on `window.__timelines[<composition-id>]`.
  `fromTo` for every entrance; custom per-frame effects (HUD, timecode, grain jitter, shockwaves,
  masks) are pure functions of `t`, called from one proxy tween spanning the whole duration.
- Recipes (iris from the motif, per-letter mask rise, bracket snap, whip-reflow, morph gizmo, dot
  landing as full stop, CSS `path()` window onto a plate, seeded shake, grain): `references/recipes.md`.
- Env for every CLI call: `source tools/env.sh; export HYPERFRAMES_NO_TELEMETRY=1
  HYPERFRAMES_BROWSER_PATH=$CHROME_PATH`. Never `publish`, never `feedback` (public channels).
- Loop: `npx hyperframes lint <comp>` (0 errors) → `snapshot <comp> --at <beat times>` → read the PNGs →
  fix → `render <comp> --quality draft --fps 30 --workers 2 -o renders/<n>.mp4` → frame study →
  final `--quality delivery --fps 60` only after the draft passes.

## 4. Build (Remotion layers)
`npx remotion render src/index.ts <Comp> out.webm --props=props.json --codec=vp9 --image-format=png
--pixel-format=yuva420p --browser-executable="$CHROME_PATH" --concurrency=2`. Fonts: `fetch(staticFile)`
→ `arrayBuffer` → `new FontFace` inside `delayRender/continueRender`. Frame = pure function of
`useCurrentFrame()`; times from props. Place the WebM in HyperFrames as a muted `<video>` clip.

## 5. Review like a stranger (the gate)
- `$PY .pi/skills/reference-mesh/scripts/framestudy.py renders/<n>.mp4 --fps 8 --out review/<n>` → read
  `motion.png`, every sheet, every transition strip.
- Compare against the bar: cuts on beats (≥ 60 % of cuts within 1 frame of a beat), holds 20–40 % of
  frames, no hold > 2 bars without an event, every text readable at 360 px wide, no text outside the
  title-safe zone, the motif present at open and close, zero invisible-text frames, no pre-roll ghosts.
- Moving objects never cross a text zone: the frame is f(t), so loop t over every frame in node and
  measure the object's screen bounds — beat snapshots miss mid-motion collisions.
- Anything failing goes back to the brief or the recipe that caused it, then re-render.

## Acceptance
Draft MP4 exists with the song; `framestudy` output read and the bar above met; lint 0 errors; every
chapter in the brief visible at its planned beat; fonts rendered (no fallback, no blanks); final
rendered only after the draft passed; engine per layer recorded in the storyboard.
