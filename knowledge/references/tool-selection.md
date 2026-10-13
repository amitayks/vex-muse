---
kind: technique
tags: [tools, hyperframes, remotion, p5, seedance, svg, three, compositing, pipeline]
audience: all
half_life: 120
rights: safe
seen: 2026-10-11
summary: "Which engine makes which shot, how layers combine, measured speeds and box gotchas, and the tools desk-checked but not adopted."
---
# Tool selection — which engine makes which shot, and how they combine

Measured in `projects/lab-motion-tools/` ([[lab-motion-tools]]) on this box (2 CPU, no GPU, 6.5 GB RAM). Versions: HyperFrames
0.8.78 (Apache-2.0), Remotion 4.0.529 (free for individuals / ≤3-person companies, paid above),
GSAP 3.15 (all plugins incl. MorphSVG/DrawSVG/SplitText free), flubber 0.4.2 (MIT).

## Pick by the shot's one read
| The read is… | Engine | Why |
|---|---|---|
| Words, graphic ideas, UI, diagrams, HUD | **HyperFrames** (HTML/CSS/SVG + GSAP) | real type engine, masks, blend modes, SVG morph/draw, fastest here |
| A shape that becomes another shape; a line drawing itself; a reveal through a silhouette | **SVG transformation** inside HyperFrames (GSAP MorphSVG / DrawSVG, CSS `path()` clips) | see [[svg-transformation]] |
| Data-driven or many variants (lyrics from song.json, 16:9 + 9:16, per-language), spring physics, audio-reactive meters, React components | **Remotion** (`spring`, `interpolate`, `@remotion/paths`, `@remotion/media-utils`) → usually rendered as a transparent layer | pure function of frame + typed props |
| Hand-made world, a character that acts, ink/watercolour/boil, a story told in drawings | **p5 studio** (`studio/`, p5.brush) | the painted look (shfred0); ~75 s/frame here → full renders on Modal GPU |
| A real performance: singing, dancing, lip-sync, cloth/hair physics, camera through space | **Seedance 2.5 plate** (+ Nano Banana Pro / GPT Image 2 cast & sets; FLUX 3 for exact placement; Kling v3 Pro for real faces; MiniMax H3 Max camera-controls for buildings and rooms; see [[generation-field-notes]]) | only generation gives bodies; draft → verify → finish |
| Movement in a filmed scene: bodies, vehicles, smoke, water, cameras | **A Blender scene** (movement, geometry, cameras, run headless with `blender -b -P`); AI models only paint the look over its renders. The principal's rule. Blender runs on the principal's Mac through [[local-muse-mac-helper]]. Render in Cycles (Metal): on a scene with 362k tree instances it ran about 15× faster than EEVEE (6.8 vs 89–119 s/frame, 960×540, 64 spp); EEVEE suits flat-colour blockouts (0.25–0.35 s/frame). Settings, speeds per job and draft checks: [[blender-field-notes]]. Paint pass: [[render-repaint]] (Flux 3 edit-video leads on people; LTX render-to-real with a photoreal first frame for landscapes) | AI video moved bodies, smoke and water wrong in [[action-01]]; the shots that held were locked frames moved by code |
| Depth: point clouds morphing, chrome/iridescent objects, 3D type | **Three.js** inside HyperFrames (adapter) or `@remotion/three` | SwiftShader here: keep scenes light or render that chapter on GPU |
| Sound | ElevenLabs SFX / `js-scoring`; songs fetched or generated per [[music-tools]] | never touch the song master |
| A page of evidence being assembled: archival photos, cutouts, stickers, clippings, dates (history / origin story / explainer / nostalgia) | **collage-motion** in HyperFrames: generated archetype cutouts + procedural paper, DOM type, stepped builds, peel / zoom-through transitions | code-first beats the generated-page route on text, timing and rights; see [[paper-collage-explainer]] |
| An agent's cursor working a UI (agent demos, launch films, UI inserts) | **Cua motion lab** (vendored, MIT) via `code-motion/scripts/cursor_track.mjs` → `assets/cursor/cursor-fx.js` on a canvas in HyperFrames | 82 human-like motions (min-jerk, Fitts timing, springs); the adapter moves each click onto its beat (< 1 ms) and keeps the move's own speed. See [[lab-cursor-motion]] |
| A material is the read: glass, chrome, liquid metal, holographic foil, neon, voxels, water on a 3D shape; or a full-frame shader filter (halftone, dither, CRT, kaleidoscope, chromatic aberration, light beams) | **Shaders** (`shaders@4`, MIT, WebGPU) as a seekable layer in HyperFrames, skill `webgpu-shaders` | 23 raymarched materials × 20 SDF shapes, $0, frame-exact through the studio driver; renders only through `modal_hf.py --webgpu` here. See [[shaders-webgpu]] |
| One hidden object shown as a lawful series of shapes: turning inside out, slicing through (point → shape → point) | **SVG in HyperFrames** + `svg-transform/assets/nd4.js` | pure 4D math, $0, ~32 s per 8 s draft; see [[tesseract]] |

Default when unsure: HyperFrames. It is the compositor anyway.

## One master timeline, many layer makers
- **HyperFrames is the master**: it owns the song, the beat grid, the final encode, HUD/grain, and
  every transition. Other engines deliver *layers*, all authored against the same `song.json`.
- Remotion → transparent VP9 WebM: `npx remotion render src/index.ts <Comp> out.webm --codec=vp9
  --image-format=png --pixel-format=yuva420p` → `<video>` in HyperFrames. **Alpha verified** (lab combo).
- Seedance plate → `<video>` in HyperFrames, under masks/type/grain. Verified.
- p5 studio → PNG sequence or WebM alpha → `<video>`/image sequence in HyperFrames (not yet verified;
  verify before a project depends on it).
- HyperFrames can itself emit alpha (`--format webm|mov`) or `png-sequence` for other hosts.

## Combos worth building (the "extraordinary" moves)
1. **Plate through the motif** — the Seedance performance is only seen through the brand mark: a spark
   mask that grows on lyric onsets, morphs to a circle and irises past the frame (lab combo, 4 s).
2. **Showreel chapters** — each 1–2 bars a different engine (3D particles, SVG morph gizmo, painted
   insert, kinetic type), held together by one palette, one HUD, one grain, one motif
   ([[code-motion-showreels]]).
3. **Painted world + graphic type** — p5 scenes as layers, HyperFrames hero type in the bible palette
   on top, grain over both so they share a surface.
4. **Vector rotoscope** — plate → contours (`rotoscope-paint` extractor) → SVG paths → MorphSVG
   between poses + DrawSVG boil in HyperFrames: hand-drawn feel at HyperFrames speed.
5. **Data → motion** — Remotion props from `song.json` render the per-word lyric layer once per aspect
   ratio; HyperFrames composes each cut.

## Speed and cost here (1080p)
- HyperFrames: 243 frames @30 fps — capture 22 s, total 31 s (`--quality draft`); 82 s at `looks`.
- HyperFrames with an image-heavy 9:16 collage ([[lab-collage]]: ~15 large
  PNG cutouts, CSS masks, drop shadows) captured at only 1.7–2.9 fps with
  `--workers 2` (screenshot fallback on software GL). Budget 10–18 s of wall
  time per second of such a comp.
- HyperFrames on a long comp (`antioch-1098`):
  - Capture of the 5:35 film (10,049 frames) ran at **~1.8–3.4 fps with
    `--workers 2`**, about 50–95 min.
  - **`--quality draft` does not speed this up.** It only swaps the
    encoder (ultrafast, CRF 28), and capture is the whole cost. Render long
    comps straight at `--quality looks` (CRF 16) so a passing review copy
    is already the master.
  - **Multi-worker MP4 dumps every frame to disk first** (~1 MB/frame,
    10.4 GB here), and the render died on disk space. Set
    `HF_CAPTURE_PARALLEL_STREAM=true` to stream frames into the encoder;
    disk then stays flat.
  - **`hyperframes snapshot` took ~40 s per frame** on this comp, while a
    direct puppeteer seek of the registered timeline took ~0.6 s. For
    spot-checking a long comp, seek and screenshot directly.
  - **Farming it out to Modal: verified on `antioch-1098` v2.**
    - **How it works:** a comp whose timeline is a pure function of time
      (no CSS `@keyframes`, no `Math.random`, `Date.now` or rAF loops) is
      captured frame-exact by seeking the registered GSAP timeline and
      screenshotting, in parallel Modal CPU containers
      (`render-review/scripts/modal_hf.py`). Each chunk is encoded with
      identical x264 settings, then joined with `-c copy`, and the master
      audio is muxed locally with `-shortest`.
    - **Speed:** ~0.35 s per frame per container. The 5:35 film took about
      5 min on 25 containers, against ~96 min local capture. A short film
      (a client brand film: 1440
      frames of 1080p60 on 24 containers) took 56
      to 81 s wall for about $0.06, so a full 60 fps master costs less than
      a local review strip.
    - **Frame size:** pass the comp's own size (`--width 1080 --height
      1920`) for every non-16:9 cut, or it comes out cropped. When every
      chunk fails, run a single-chunk 0.05 s test to read the full error.
    - **Parity with a local render:** PSNR 35–37 dB, with only uniform
      encoder noise in the diff, so the output is visually identical.
    - **Encoding:** CRF 17 `slow`. Drop `-tune animation`, which pushed a
      grainy vellum test to 32 Mbps. The film came out 415 MB against
      690 MB for the local CRF 16 render.
    - **Stragglers:** one container can hang. The last chunk ran 7+ min with
      empty logs while the others took ~3 min. Re-render that frame range in
      fresh containers, join, then `modal app stop`
      the stuck app so it doesn't bill for up to an hour. Cancelling the
      local render does not stop its app either: the containers kept billing
      until `modal app stop <app-id> --yes` ([[lab-shaders]]).
    - **Checks after joining:** check every seam for duplicate or dropped
      frames. `-shortest` trims to the audio (10,048 of 10,049 frames). It
      cost 3 frames when the duration was not a whole number of frames
      (17 bars at 140 BPM = 29.142857 s = 1748.6 frames at 60 fps: 1749
      rendered, 1746 muxed). Remux with `-c:v copy -t <dur>` and an audio
      fade instead, or pick durations that are whole frames.
    - **Disk:** write chunks and the joined file to `/tmp`, a separate
      filesystem, so render debris never lands on the shared `/data`.
- Shaders (WebGPU, SwiftShader-Vulkan): 1080p 4–19 s/frame here (stills only), 0.34–3.1 s/frame
  on Modal 8-CPU containers ([[lab-shaders]]).
- Remotion: 125 frames incl. bundle 38 s (mp4); 120 frames VP9-alpha 102 s (VP9 encode is the cost).
- p5 studio: ~75 s/frame locally → Modal (~0.3 s/frame) for anything longer than sheets/strips.
- Seedance 2.5: money, not CPU — see [[generation-field-notes]].

## Studying references (`reference-mesh/scripts/framestudy.py`)
One sequential decode pass (per-frame ffmpeg seeks on long-GOP 1080p60 took 5 min for 10 strips;
one pass is ~17 s per 15 s clip). Container fps ≠ animation fps: compare `nb_frames` with duration
(shfred0 is 8 fps drawing in a 60 fps file). Labels via PIL (the bundled ffmpeg has no `drawtext`).
X videos via `xfetch.py` (fxtwitter mirror, no API); what launched this fortnight and how it was cut via
`whatships.py` (`find` / `wall` / `fetch --study`, [[whatships]]). Vendor every JS library into the
project's `assets/js/` so renders never touch the network.

**Read framestudy's audio fields loosely on the studio's own renders.** Its `beat_phase` was 144 ms off a kick-band
onset fold, so `cuts_on_beat` read 0/4 for cuts that were frame-exact; blurred whips are not detected as
cuts. Check sync with an onset fold ([[generation-field-notes]], Timing QA).

**`hold_frac` counts duplicate frames as holds,** so stepped (on-twos) builds read inflated (0.71 on
[[lab-collage]] vs 0.175 on its reference); judge those from `motion.png`. It also rises on a 9:16
re-layout of the same timing, so compare it only between cuts of the same layout.

## Watched, not adopted (launches, many found via [[whatships]])
| Tool | What it is (from its launch post/film) | For the studio |
|---|---|---|
| **Tesseract** (Mirage) | "After Effects + Premiere for agents": a local closed-source engine with a CLI (`tsrct`), editable layers and keyframes, ~40 effects, WGSL shaders, ProRes 4444 alpha | **Tested (v0.2.0), not adopted.** The same 8 s piece came out pixel-equivalent but took 74 s vs HyperFrames' 33 s, with silent export failures. Retest only for footage-heavy work. See [[mirage-tesseract]] |
| **Code2Video Bench** (HyperFrames × Google DeepMind) | code-to-video benchmark with pairwise human picks | its two questions ("does it hold attention?", "does it match the brief?") are a good quick-review lens |
| **Cube Motion** (cube-motion.dev) | SVG dot-particle animation library with framework adapters | GSAP + flubber covers its morphs, and the dot look is saturating; not installed |
| **Glyph** (pmndrs) | GPU typography for three.js / R3F / TypeGPU | only if type must live inside a 3D scene; DOM type in HyperFrames stays default; not tested |
| **Higgsfield** (Higgsfield AI) | a paid front-end wrapping Seedance, GPT Image 2, Seedream and Kling, with camera presets, a Blender camera-blockout bridge and performance transfer | **desk-checked 2026-09-27, not adopted.** Every model it wraps is live on fal, so it adds only a second paid layer. Its performance-transfer lead was tested on fal instead ([[generation-field-notes]]). Reopen only if camera control is the bottleneck |
| **ffmpeg-skill** (kajisho5, MIT, 1.6k stars) | a generic agent skill: 42 stdlib-Python ffmpeg wrappers (cuts, captions, HDR→SDR, loudness, presets) for talking-head and social re-edits | **desk-checked 2026-10-04, not adopted.** It duplicates `track-edit`, `render-review`, `song-map` and `framestudy.py`. Taken: its vertical app-UI safe zones, now in [[kinetic-typography]]. Reopen only for real camera footage (phone HDR → SDR, VFR clips, multicam sync) |
| **PixelUMM** (NVIDIA + Waterloo, open weights) | one 15B Transformer that reads and writes raw pixels (no VAE, no vision encoder) for image and video | **desk-checked 2026-10-05, not adopted.** Capped at 512² and 4 s, with a 16-px grid on flat areas, non-commercial weights, not on fal. Reopen if a pixel-space model ships at ≥720p without the grid |
| **DistScene** (HKUST + TeleAI, arXiv 2610.06960) | one image → a decomposable textured 3D scene: an environment mesh plus up to ~20 object meshes (GLB), a LoRA on TRELLIS.2 | **desk-checked 2026-10-07, not adopted: nothing to run.** Code and weights are "coming soon"; no licence, nothing on fal. Its demos read as a tabletop diorama with errors ([[escape-velocity-case]]). For objects dropping onto a set, use `fal-ai/trellis-2` per object today. Reopen when the weights ship |
| **Unreal MCP** (Epic, UE 5.8, experimental) | an MCP server inside the Unreal Editor for placing actors, lights and materials; loopback only, no auth | **desk-checked 2026-10-09, not adopted yet.** It needs an open editor on a GPU machine and a tunnel with its own auth. It would add real-time renders, MetaHuman faces that lip-sync from audio and large ready-made sets. Reopen if speaking faces or large sets block a film |
| **Voyager** (Nullframe / Moda) | a desktop agent app (macOS first) with ~40 skills that drives Adobe apps, Resolve, Blender, Unity and Ableton on the same machine; the code is proprietary | **desk-checked 2026-10-09, not adopted.** A rival harness that drives a Blender beside it through the same headless route. Taken: body motion from a reference video onto a rig, a contact check (see TERRA), and the render-to-real paint pass above |
| **image-blaster** (neilsonnn, MIT) | skills + scripts: one image → clean plate → a World Labs **Marble** world of the empty set → a 3D mesh per object → SFX | **desk-checked 2026-10-09, repo not adopted.** Glue around models the studio already runs on fal. Taken: the order (clean plate first, objects as separate meshes). **The lead was Marble**, now in use for gaussian-splat worlds: costs, camera travel limits and gotchas are in [[splat-field-notes]] |
| **Qwen-Image-2.1 / 2.1-Turbo** (Alibaba Qwen, open weights) | a 7B text-to-image and edit model at 2K (Turbo: 8 steps) with native RGBA output, transparent-layer edits and up to 10 reference images | **desk-checked 2026-10-09, not adopted.** The research-only licence closes it to client work; it is not on fal. **The lead is native soft-edge alpha** (hair, smoke, glass), which the studio's still-image mattes lack. Reopen when it lands on fal (test against GPT Image 2 transparency). `alibaba/qwen-image-3` is on fal and untested |
| **Vivix W1** (Vivix Labs) | a real-time, streaming video model (8 s at 720p in ~8 s) driven by text, voice and motion; API + playground | **desk-checked 2026-10-11, not adopted.** $0.003/s is a launch discount to 2026-10-31 (vs Seedance 2.5 $0.231/s); all comparisons are the vendor's own, and the post that surfaced it was a paid partnership. The vendor admits gaps in cinematic fidelity, complex motion and dense scenes; camera control is by text, not a path. **The lead is price and speed for previz and live/interactive visuals.** Reopen for a cheap draft lane or a live piece; test one shot side by side first |
| **TERRA** (EPFL Mathis lab, Apache-2.0; its body models are research-only) | mocap → support terrain from foot contacts → a MuJoCo muscle body walked by one learned policy on stairs, ramps and beams | **desk-checked 2026-10-10, not adopted.** A biomechanics tool: mocap in, a muscle skeleton out (no Blender rig), Linux + CUDA only. Taken: its contact logic as the spec for the Blender contact check (a planted foot sits on a surface, a swinging foot and the body cut no geometry). Reopen only for simulated falls or impacts |

## Box facts that bite (fixes are in `code-motion`)
- Chrome here fails **URL font loads** (NetworkError even for `data:` URIs) → text in web fonts renders
  invisible. Register fonts from bytes: `FontFace(name, ArrayBuffer)` (`code-motion/scripts/hf_build.py`;
  Remotion: `fetch(staticFile()) → arrayBuffer → FontFace`). URL loads failed for every face even when
  the request returned 200; the same faces from bytes all loaded.
- No system fonts: `monospace`/`sans-serif` render **nothing**. Ship every face used.
- HyperFrames preview/Studio writes `data-hf-id` into project HTML; keep editable sources outside the
  project dir and build in.
- Parallel render workers seek at random: build the GSAP timeline synchronously (never inside
  `fonts.ready`); `fromTo` pre-renders its from-state before start (flashes, waves) — drive custom
  effects as pure functions of time from one proxy tween.
- `clip-path:url(#svgClip)` did not survive HyperFrames capture; CSS `clip-path: path()` rebuilt per
  frame did.
- **A proxy tween at position 0 runs one seek behind.** GSAP renders a timeline's children in
  start-time order, so a `tl.to(proxy, {onUpdate(){ frame(t) }}, 0)` fires *before* every
  later-starting tween on each seek. Per-frame code that reads values other tweens animate (camera,
  plate positions, clips) then draws the previous seek's state (a client brand film). Frame 0
  also comes out blank, because a seek to 0 on a fresh timeline fires no update.
  - Fix, verified in the renders: `tl.eventCallback('onUpdate', () => frame(tl.time()))`, which fires
    after all children have rendered. Pad the timeline with `tl.set({}, {}, DUR)`, and call `frame()`
    once on `load` so frame 0 is drawn.
  - The proxy pattern in `code-motion/references/recipes.md` is still fine when the effect depends on
    `t` alone (timecode, grain).
- **A `const` used before its declaration (TDZ) blanks every capture.** The throw happens before
  `window.__timelines` is set, so every snapshot and Modal chunk fails with "Cannot read properties
  of undefined (reading 'main')". Declare shared times at the top of the timeline script.
- **HyperFrames runs external `<script src>` files before `<body>` exists,** so DOM-building code
  fails (`reading 'appendChild'`) and snapshots come out blank. Inline the script at the end of the
  body, with the timeline created and registered in it. When a snapshot is blank but Chrome renders
  the page, run `hyperframes validate`/`check`: they report the JS errors that snapshots hide.
- **Inlining JS or CSS into one HTML file breaks in two quiet ways** (found building a client brand kit):
  - A literal `</script>` or `</style>` anywhere in the inlined source, even inside a comment, closes
    the element early.
  - A build marker string (for example `<!-- x:js -->`) that also appears in the inlined file's own
    comments gets replaced there first.

  Make the build fail if a kit file contains `</script` or `</style`, and keep marker text out of
  kit comments.
- **`mix-blend-mode: multiply` inside a transformed camera div** blends only within the camera's
  stacking context: white paper showed as a light box. Put the blend on the camera group itself.
- **Hide initial states outside the timeline.** A `tl.set(el, {autoAlpha: 0}, 0)` inside the paused
  timeline does not render at frame 0 (lint `gsap_timeline_set_initial_hide`). Put initial hides in
  `gsap.set` outside the timeline and use `tl.set` only for later states.
- **Close checks without a render:** `hyperframes snapshot <comp> --at <t> --zoom "x,y,w,h"
  --zoom-scale 2` renders a close crop, e.g. torn edges and corners.
- **procps is missing on this box:** `pgrep` and `ps` both return "command not found". Stop a
  runaway render with `execution_cancel` on its execution id (the process exits 143). Inspect
  processes through `/proc/*/cmdline`.
- No Docker (`--docker` renders unavailable); `/dev/shm` 64 MB (renderer flags cope).
- **Pillow lives only in the studio venv.** System `python3` has no PIL; use `tools/py/bin/python`.
  fontTools is not installed anywhere; put it (and PyMuPDF) in a throwaway `uv venv /tmp/pdfenv`, which
  keeps it off the shared volume ([[shift-labs-brand]]). `file` and `xxd` are missing: read magic bytes
  with Python (`open(f,'rb').read(8).hex()`).
- **puppeteer-core resolves only from inside `studio/`** (or `projects/lab-motion-tools/`); an ESM
  script in `/tmp` fails with `ERR_MODULE_NOT_FOUND` even with an absolute path. Resolve it through
  studio with CommonJS: `const require = createRequire('/data/workspaces/<workspace>/studio/x.js'); const
  puppeteer = require('puppeteer-core');` (the anchor file need not exist). Launch with
  `executablePath: process.env.CHROME_PATH` after `source tools/env.sh`.
- **A `<textarea>` kills the chrome-headless-shell renderer on this box** ("Navigating frame was
  detached" or "Target closed", no log line), and a live site's contact form crashes it the same way
  (a brand-book build). Bisect a crash by sections, then elements; draw field specimens as a
  static `div`. (`@font-face` with `data:` URLs fails too: see the font bullet above.)
- **Font metadata without fontTools:** `fontkit` is in `projects/lab-motion-tools/node_modules`
  (`openSync(f)` gives family, copyright, licence URL, `characterSet`, fsType); the studio Python has no pip.
