# Muse — a music-video director agent for Vex

Muse takes a song (or any audio, or just an idea) and ships a finished, platform-native video:
concept, research, style bible, cast, sets, generated base plates, hand-painted JavaScript animation
drawn over them, kinetic lyrics, sound design, render, review, re-render — from a one-line ask.

This repo is a **forkable Vex workspace**: drop it into a workspace, add keys, and the agent runs.

## Fork it

1. Fork / use this repo as a template, then connect it to a Vex workspace (git sync) or copy the tree
   into `/data/workspaces/<name>/`.
2. In the workspace, set the keys in `.env.example` as **workspace variables** (never in files or chat).
3. First message to the agent: it runs `tools/bootstrap.sh` (rootless headless Chrome, ffmpeg, uv Python
   with numpy/scipy/opencv), fills `knowledge/principal.md` with you, and is ready for a brief.
4. Set `.github/render-farm.json` → `repo` to your fork for the GitHub-Actions CPU render fallback.
   Full renders go to Modal GPUs (~0.3 s per 1080p painted frame).

## What's inside

- `AGENTS.md` — the director's identity: how it thinks, where it breaks (M1–M8), rails, money.
- `.pi/skills/` — 23 skills; `mv-director` is the master workflow and routes to the rest.
- `.agents/skills/` (+ mirror in `.claude/skills/`) — 10 HyperFrames skills from
  [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (Apache-2.0), pinned in `.agents/.skill-lock.json`.
- `studio/` — Muse's fork of [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase)
  (p5.js + p5.brush painting engine; offline fonts, page renders, soft-GL fixes — `studio/FORK.md`).
- `vendor/` — pristine pinned upstream (see `vendor/PINS.md` for the refresh procedure).
- `projects/lab-*` — the capability labs the skills build on (motion tools, collage, music, voice):
  sources, recipes and measured results; generated media is not shipped.
- `knowledge/references/` — the reference compendium (music-video grammar, kinetic typography,
  anti-slop tells, tool selection, generation field notes, case studies).
- `.runline/plugins/` — `xpost` (optional X posting behind an exact-preview approval gate).
- `tools/` — `bootstrap.sh`, `killchrome.sh`, `x-callback/` worker, `fetch-vendor.sh`.

## Skills

- **cast-and-sets** — Design a video's cast and locations with image models so they stay on-model through every generation
- **code-motion** — Build motion graphics entirely in code
- **collage-motion** — Build mixed-media paper-collage motion
- **fal-media** — Call fal.ai generative models (image, image-edit, video, lip-sync, background removal, upscaling, music, stems, SFX) through Muse's stdlib c
- **js-scoring** — Compose and render music and musical sound design in JavaScript (WebAudio, rendered offline and deterministic in headless Chrome to WAV)
- **kinetic-lyrics** — Design and animate lyric typography as motion graphics inside a music video
- **music-gen** — Generate original music for a video
- **music-source** — Get any song, beat, instrumental, soundtrack/OST, a cappella, loop or SFX as a first-class asset
- **mv-director** — The master workflow for making a music video, lyric video, animated short or any audio-driven visual piece end to end
- **p5-paper-engine** — Paint and animate hand-made-looking 2D frames in JavaScript with Muse's studio (fork of ClaudeAnimationBase
- **reference-mesh** — Research and grow Muse's reference compendium
- **render-review** — Render a video from the studio (local previews or the render farm), encode it with the final audio mix, and review it like a stranger
- **rotoscope-paint** — Draw over generated video plates in JavaScript so only the painting is seen
- **seedance-plates** — Generate video base plates with Seedance 2.5 (reference-to-video / image-to-video) using character sheets, set images and the exact sliced s
- **shift-labs-design** — Make every Shift Labs (makers of Vex) deck, report, research note, dashboard or figure on-brand, honest and decision-ready
- **skill-authoring** — How a Shift skill is written, maintained, and bound — the one methodology
- **song-map** — Turn a song into song.json
- **sound-design** — Add sound design to a video without touching the song
- **storyboard** — Plan a music video shot by shot against song.json
- **style-bible** — Design and lock a video's visual style so every generated and hand-painted frame reads as one world
- **svg-transform** — Design and animate SVG transformations as storytelling
- **track-edit** — Edit music on its own bar grid, sample-accurate and click-free
- **x-post** — Secondary utility for posting a finished piece to X (Twitter)

## Rails that ship with it

- Talks to its principal only; never posts or sends anything without an explicit OK on that exact item.
- Keys by name only, requested through secure links.
- Draft → verify → finish; every paid call lands in `projects/<slug>/ledger.jsonl`; default cap $150/project.
- Finals delivered as full-quality files to the principal — never via public URLs.
- Disk law: frames are temporary; never let free space drop under 2 GB.

## Licenses

See `NOTICE.md`. Third-party components keep their own licenses.
