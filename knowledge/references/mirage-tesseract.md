---
kind: technique
tags: [tools, tesseract-engine, mirage, agent-video-tools, after-effects-like, hyperframes-comparison, field-notes]
audience: all
half_life: 45
rights: safe
seen: 2026-09-26
summary: Mirage's Tesseract, a local After-Effects-like engine driven by an agent through a CLI. What it is, how to run it on this box, the gotchas of v0.2.0, a same-piece benchmark against HyperFrames, and why it is not adopted.
---
# Mirage Tesseract: engine field notes (v0.2.0, tested 2026-09-26)

**Verdict: not adopted.** On code-drawn motion it gives the same picture as HyperFrames, but it is
**2.2× slower here** and has more friction, and it is a closed, early-preview engine. Its real
strengths are footage work, which this test did not touch. Retest those if a project is mostly live
footage, or when a version ≥ 0.3 lands. The name is branding only: the engine and its films contain
no 4D geometry (for the concept, see [[tesseract]]).

## What it is
- **An engine that runs on your own machine.** It is a local engine with a CLI (`tsrct`) that an
  agent drives, like After Effects without the UI. It is not a hosted service; the earlier
  "hosted" entry in [[tool-selection]] was wrong. It ships as a CLI ZIP for linux-x86_64,
  darwin-arm64 and Windows, with agent skills `tesseract-motion` and `tesseract-video` in
  `github.com/mirage-hq/Tesseract` (`npx skills add mirage-hq/Tesseract`) and a ChatGPT/Codex plugin.
- **Native model.** Everything lives in one editable `.tsrct` document:
  - layers, groups, keyframes (`setFxPropertyKeyframes`, easing on the destination key);
  - per-property `jsScript` animators (`layerTimeJsCode`, reading `input.time.seconds`);
  - adjustment layers, masks and track mattes, text animators;
  - about 40 native effects (glow, grain, blurs, pixel motion blur, chromatic aberration,
    corner pin…) and custom WGSL shaders;
  - flat layers arranged in 3D;
  - audio layers with gain envelopes.
- **Output:** H.264/AAC MP4, and ProRes 4444 MOV (transparent with `--fx-solo`).
- **CLI:** `project create|inspect|schema|checkout|commit`, `preview` (one PNG), `filmstrip`
  (labelled grid at `--timestamps-ms`) and `export`. `project schema` (actions, about 500 KB) and
  `project schema --document` are the real reference; the prose docs lag them.
- **Boundaries:**
  - One composition per document: use groups for scenes and Video layers for cuts.
  - No real 3D objects.
  - A new project defaults to 1080×1920 and 3.0 s, so set dimensions and duration first.
- **Telemetry is on by default.** Run `tsrct telemetry disable` first.

## Running it on this box (2 CPU, no GPU)
The box has glibc 2.41 (≥ 2.35 needed) and ships `libvulkan`, but it has **no Vulkan driver**. The
recipe that worked, all under `/tmp` because the shared `/data` disk is tight:
1. Download the pinned release ZIP and its `.sha256` from GitHub releases and verify the checksum.
   Unpack it with Python, since there is no `unzip`.
2. Install a software Vulkan driver (Mesa **lavapipe**) into an isolated sysroot. Run `apt-get download` with private
   `Dir::State`/`Dir::Cache` for `mesa-vulkan-drivers` plus its dependencies (`libllvm19`, libdrm,
   libxcb-*, libz3, libxml2, libicu76, …), then `dpkg-deb -x` each one. The sysroot is about 280 MB.
3. Write an ICD JSON pointing at the absolute `libvulkan_lvp.so`. Then export `VK_DRIVER_FILES`,
   `VK_ICD_FILENAMES`, `LD_LIBRARY_PATH` (the sysroot lib dir), and `XDG_DATA_HOME`/`XDG_CONFIG_HOME`
   (to isolate the install). Run `install.sh`.
4. A preview renders in about 1.5 s. The whole install needs about 0.5–0.6 GB of disk.

## Gotchas (each cost a render)
- **A throwing script silently kills the export.** A `jsScript` that throws (here a ReferenceError
  in one colour script) makes export drop the *whole* scripted graph after about 50 frames, at any
  fps: every scripted layer vanishes. `preview`/`filmstrip` still look right and nothing is
  reported. Check exports frame by frame (drawn-pixels and duplicate-frame counts), never only the
  filmstrip.
- **Opacity units disagree with the docs.** Scripted opacity is **0–1 on shape layers** but
  **0–100 on text layers**; the docs say percent for both. A shape at "42" renders solid, and
  text at "1" is invisible.
- **Paths can only move by script.** Path keyframes are rejected ("invalid property keyframe data";
  in the document, "unsupported path values") through both the action API and a direct document
  edit. A morphing or moving shape must be a `jsScript` returning `{commands:[…]}`.
  Float keyframes work.
- **Fonts:**
  - A variable font is rejected ("invalid font registry"); cut static instances with fontTools.
  - Names don't round-trip. Import reports "Unbounded Medium/Regular", but a render only
    resolves `fontFamily: "Unbounded"` + `fontStyle: "Medium"`.
  - Text `tracking` is in 1/1000 em.
- **Export encoder.** The Linux build's bundled ffmpeg has **no H.264**. Use
  `export --encoder-backend external-ffmpeg-command --ffmpeg-path $(which ffmpeg)` (the studio
  ffmpeg from `tools/env.sh`).
- **No per-run text styling.** An underline under one word has to be a separate shape layer.

## Benchmark: the same piece in both engines
The 8.1 s tesseract "turn" test (`renders/tesseract_turn_v2.mp4`, [[tesseract]]) was ported
exactly: same math, beat, palette and captions. That came to 156 actions and 50 layers, with every
edge driven per frame by script.

| | HyperFrames 0.8.78 | Tesseract 0.2.0 |
|---|---|---|
| Render, 243 frames 1080p30 here | **33 s** (draft, 2 workers) | **74 s** (single process, lavapipe) |
| Match | reference | 0.79 % of pixels strongly different; pink fill slightly more saturated (median BGR 188/140/219 vs HyperFrames 188/160/231) |
| Runs out of the box here | yes | no (driver, static fonts, external encoder) |
| Editable afterwards | source HTML | `.tsrct` layers + keyframes |

Both engines render in software here, so the comparison is fair, but it is not either engine's best.
Files:
- `projects/lab-motion-tools/renders/tesseract_turn_tsrct_v3.mp4`
- `renders/engine_compare_hf_vs_tsrct.mp4` (side by side)
- `tsrct-test/`: the builder, checker and editable project

## Its method docs: what was worth taking
The skill docs mostly restate what `code-motion`, `storyboard` and `song-map` already do. Of three
candidate points, only one is new:
- **Eye-line continuity:** keep a performer's eyes at the same screen height across performance
  cuts. It is concrete and checkable, and it belongs as one line in the render-review cut check.
  **Adopted** (the principal approved this point only) in `render-review` 1.5.0, seams step. At every
  performer→performer cut, the eyes' midpoint must sit at the same screen height and near the same
  x in the last and first frame, judged on the final crop. A jump is fixed by reframing. A punch-in
  may change face size, but not eye height.
- **Skipped as duplicates:**
  - "choose how much graphics per moment" is already covered by technique-per-shot and text mode
    per line;
  - "time to real musical accents, not every peak" is already covered by song-map sections and
    energy-driven cut cadence.
- Also in their docs: **person-matte polarity.** A person-white matte with `lumaInverted` shows
  graphics *outside* the person, and `luma` shows them *inside*. Test it on a real frame.

## Their showcase film ("Opus 5.5 + Tesseract", @trymirage, 25 Sep 2026, 43 k views)
- **Claims (unverified):** "made in one shot… 1600+ layers and 3700+ animations", fully editable.
- **Measured:** 15 s, 17 shots, average 0.88 s, holds 9.6 % (our bar is 20–40 %), 5/16 cuts on the beat.
- **What it is:** a feature catalogue for a made-up "SPAM" photos app. The chapter labels name the
  effect on show ("trim paths", "3D tunnel", "parallax flyover", "procedural grid"), set against a
  synthwave sunset with a REC/timecode frame. Both are on the saturating list ([[anti-slop]],
  [[code-motion-showreels]]).
- **Craft read:** it shows range, but it has no event and no story. It is not a style to follow.
- **Name clash:** mirage.app has a "Tesseract for Muse" setup page. That is another agent product
  named Muse, not this studio.
