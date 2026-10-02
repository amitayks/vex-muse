---
kind: technique
tags: [tools, hyperframes, remotion, p5, seedance, svg, three, compositing, pipeline]
audience: all
half_life: 120
rights: safe
seen: 2026-09-26
---
# Tool selection — which engine makes which shot, and how they combine

Measured in `projects/lab-motion-tools/` ([[lab-motion-tools]]) on this box (2 CPU, no GPU, 6.5 GB RAM). Versions: HyperFrames
0.8.78 (Apache-2.0), Remotion 4.0.529 (free for individuals / ≤3-person companies, paid above),
GSAP 3.15 (all plugins incl. MorphSVG/DrawSVG/SplitText free), flubber 0.4.2 (MIT).

## Pick by the shot's one read
| The read is… | Engine | Why |
|---|---|---|
| Words, graphic ideas, UI, diagrams, HUD | **HyperFrames** (HTML/CSS/SVG + GSAP) | real type engine, masks, blend modes, SVG morph/draw, shader transitions, fastest here |
| A shape that becomes another shape; a line drawing itself; a reveal through a silhouette | **SVG transformation** inside HyperFrames (GSAP MorphSVG / DrawSVG, CSS `path()` clips) | see [[svg-transformation]] |
| Data-driven or many variants (lyrics from song.json, 16:9 + 9:16, per-language), spring physics, audio-reactive meters, React components | **Remotion** (`spring`, `interpolate`, `@remotion/paths`, `@remotion/media-utils`) → usually rendered as a transparent layer | pure function of frame + typed props |
| Hand-made world, a character that acts, ink/watercolour/boil, a story told in drawings | **p5 studio** (`studio/`, p5.brush) | the painted look (shfred0); ~75 s/frame here → full renders on Modal GPU |
| A real performance: singing, dancing, lip-sync, cloth/hair physics, camera through space | **Seedance 2.5 plate** (+ Nano Banana Pro / GPT Image 2 cast & sets) | only generation gives bodies; costs money: draft → verify → finish |
| Depth: point clouds morphing, chrome/iridescent objects, 3D type | **Three.js** inside HyperFrames (adapter) or `@remotion/three` | SwiftShader here: keep scenes light or render that chapter on GPU |
| Sound | ElevenLabs SFX / `js-scoring`; songs fetched or generated per [[music-tools]] | never touch the song master |
| A page of evidence being assembled: archival photos, cutouts, stickers, clippings, dates (history / origin story / explainer / nostalgia) | **collage-motion** in HyperFrames: generated archetype cutouts + procedural paper, DOM type, stepped builds, peel / zoom-through transitions | code-first beats the generated-page route on text, timing and rights; see [[paper-collage-explainer]] |
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
- HyperFrames with an image-heavy 9:16 collage ([[lab-collage]]):
  - The comp: 1080×1920 with ~15 large PNG cutouts, CSS masks and
    drop-shadow filters.
  - Speed: 535 frames @30 fps took 3 min 6 s to 5 min 16 s per draft with
    `--workers 2`. Capture dominates (2 min 46 s to 4 min 53 s). That is
    about 1.7–2.9 fps, against about 8 fps for the light reel.
  - The renderer fell back to screenshot capture: "BeginFrame did not run"
    on software GL.
  - Budget 10–18 s of wall time per second of such a comp. Check fixes
    with `hyperframes snapshot` before any re-render.
- HyperFrames on a long comp (`antioch-1098`):
  - The comp: 5:35 at 1080p30, 10,049 frames, 39 JS-built scenes, CSS
    masks and multiply layers.
  - Capture ran at **~1.8–3.4 fps with `--workers 2`**, about 50–95 min
    for the whole film.
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
      5 min on 25 containers, against ~96 min local capture.
    - **Parity with a local render:** PSNR against the local render was
      35–37 dB. An offset sweep ruled out timing: −1 frame scored the same,
      since the animation steps on twos, and −2 frames dropped to 24 dB.
      The diff image showed only uniform encoder noise (mean 2.5/255 on fine
      line work), so the output is visually identical.
    - **Encoding:** CRF 17 `slow`. Drop `-tune animation`, which pushed a
      grainy vellum test to 32 Mbps. The film came out 415 MB against
      690 MB for the local CRF 16 render.
    - **Stragglers:** one container can hang. The last chunk ran 7+ min with
      empty logs while the others took ~3 min. Re-render that frame range in
      fresh containers (it took 91 s, clean), join, then `modal app stop`
      the stuck app so it doesn't bill for up to an hour.
    - **Checks after joining:** check every seam for duplicate or dropped
      frames. `-shortest` trims to the audio (10,048 of 10,049 frames).
    - **Disk:** write chunks and the joined file to `/tmp`. It is a separate
      filesystem with ~20 GB free, and `/data` stays under the 2 GB floor
      otherwise.
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

**`hold_frac` counts duplicate frames as holds.** A render with stepped (on-twos) builds therefore
reads inflated: 0.71 on [[lab-collage]] against 0.175 on its reference. For stop-motion pieces,
judge holds from `motion.png` or at the step rate.

## Watched, not adopted (Sep 2026 launch wave, from [[whatships]])
| Tool | What it is (from its launch post/film) | For us |
|---|---|---|
| **Tesseract** (Mirage) | "After Effects + Premiere for agents": a **local** closed-source engine with a CLI (`tsrct`) and agent skills, editable `.tsrct` layers/keyframes/scripts, ~40 native effects, mattes, WGSL shaders, ProRes 4444 alpha (an earlier "hosted, nothing to install" read was wrong) | **tested 2026-09-26 (v0.2.0), not adopted.** The same 8 s piece came out pixel-equivalent but took 74 s vs HyperFrames' 33 s here. It needs a software Vulkan driver, static fonts and an external H.264 encoder, and a throwing script silently blanks the export. Retest only for footage-heavy work (effects, person mattes). See [[mirage-tesseract]] |
| **Code2Video Bench** (HyperFrames × Google DeepMind, Kaggle) | benchmark for code-to-video: pairwise human picks ("does it hold attention?", "does it match the brief?") + a trained judge model | its two questions are a good quick-review lens; dataset/judge access on Kaggle not checked |
| **Cube Motion** (cube-motion.dev) | SVG animation library drawn in JS; `rise` / `leave` / `morph` / `reveal`; React, Svelte, Solid, Vue adapters | dot-particle re-formations in SVG; our GSAP + flubber stack covers morphs, and the dot look is now saturating — not installed |
| **Glyph** (pmndrs) | GPU typography engine (bitmap / MSDF / Slug, shaping, bidi, CJK) for three.js, R3F, TypeGPU | only if type must live inside a 3D/WebGPU scene; DOM type in HyperFrames stays default; heavy on SwiftShader — not tested |
| **Higgsfield** (Higgsfield AI) | a paid generation front-end over third-party models. Its Claude MCP connector is "powered by Seedance 2.0, GPT Images 2.0, Marketing Studio and Cinema Studio"; its ChatGPT plugin adds Seedream 5.0 Pro and Kling 3.0. Also ships a "Supercomputer" cloud agent (research → script → storyboard → video), a Blender camera-blockout bridge and Genjutsu (acting + lip-sync transferred from an uploaded video onto a character). 21 launch entries in `research/whatships/videos.json` | **desk-checked 2026-09-27, not adopted.** Every model it wraps is live on fal (checked via fal's model search, 2026-09-27): Seedance 2.5, GPT Image 2, `bytedance/seedream/v5/pro/*`, `google/gemini-omni-flash/v1.1/*`. For Genjutsu-style performance transfer, fal has `fal-ai/kling-video/v3/{standard,pro}/motion-control` and `fal-ai/wan/v2.2-14b/animate/replace`. So it would add a second paid layer and a custom runline plugin (none in Vex's catalog), with no model we lack. What is Higgsfield-only: Cinema Studio camera presets (might help Seedance's weak framing, [[generation-field-notes]]), the Genjutsu pipeline itself, and the Supercomputer agent, which duplicates Muse. **Next move is on fal, not Higgsfield:** test performance transfer (Kling 3 motion-control vs Wan animate/replace) as a sync fix, since a real performance carries its own timing. Reopen Higgsfield only if camera control is still the bottleneck after that |

## Box facts that bite (fixes are in `code-motion`)
- Chrome here fails **URL font loads** (NetworkError even for `data:` URIs) → text in web fonts renders
  invisible. Register fonts from bytes: `FontFace(name, ArrayBuffer)` (`code-motion/scripts/hf_build.py`;
  Remotion: `fetch(staticFile()) → arrayBuffer → FontFace`). Re-confirmed 2026-09-27: 0/47 faces loaded
  from `file://`, from `http://localhost` and from `data:` URIs, even though every request returned 200.
  The same faces as base64 → `FontFace(ArrayBuffer)` loaded 21/21.
- No system fonts: `monospace`/`sans-serif` render **nothing**. Ship every face used.
- HyperFrames preview/Studio writes `data-hf-id` into project HTML; keep editable sources outside the
  project dir and build in.
- Parallel render workers seek at random: build the GSAP timeline synchronously (never inside
  `fonts.ready`); `fromTo` pre-renders its from-state before start (flashes, waves) — drive custom
  effects as pure functions of time from one proxy tween.
- `clip-path:url(#svgClip)` did not survive HyperFrames capture; CSS `clip-path: path()` rebuilt per
  frame did.
- **HyperFrames runs external `<script src>` files before `<body>` exists.** The page works in plain
  Chrome, but in HyperFrames DOM-building code hits `Cannot read properties of null
  (reading 'appendChild')` and snapshots come out blank. Inline the script at the end of the body at
  build time, and create and register the timeline in that same script (lint wants both together).
  When a snapshot is blank but Chrome renders the page, run `hyperframes validate`/`check` first:
  they report the runtime JS errors that snapshots hide.
- **Inlining JS or CSS into one HTML file breaks in two quiet ways** (found building a brand kit):
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
- **puppeteer-core resolves only from inside `studio/`** (or `projects/lab-motion-tools/`). An ESM
  script in `/tmp` fails with `ERR_MODULE_NOT_FOUND`, even when it is given an absolute path (an import
  of `…/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js` fails too). Either put the script in
  `studio/` as `_<name>_tmp.mjs` and `import puppeteer from 'puppeteer-core'`, or keep it in `/tmp`
  and resolve through studio with CommonJS:
  `import { createRequire } from 'module'; const require = createRequire('/data/workspaces/<workspace>/studio/x.js'); const puppeteer = require('puppeteer-core');`
  (the anchor file need not exist). The second form ran every render, measurement and alignment probe of
  `shift-labs-design` from `/tmp`. Either way, launch with `executablePath: process.env.CHROME_PATH`
  after `source tools/env.sh`.
