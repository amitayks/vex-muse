---
name: js-scoring
description: Compose and render music and musical sound design in JavaScript (WebAudio, rendered offline and deterministic in headless Chrome to WAV) - stings, risers, drops, loops, beds, full cues - including re-creating the feel of a reference track from its song map (tempo, key feel, arrangement energy). Use when a video needs original score or musical SFX, when there is no song yet, when a cue must be sample-accurate to the picture, or to prototype arrangement ideas; never to alter a provided song master.
license: MIT
compatibility: tools/env.sh (Chrome headless shell) + studio/node_modules (puppeteer-core); song-map for reference analysis.
metadata:
  author: muse
  version: "1.1.0"
---

# js-scoring — music as code, rendered like frames

A score is a pure function of time, like a frame: `score(ctx, T)` builds a
WebAudio graph on an `OfflineAudioContext` and schedules every event in
absolute seconds. Deterministic (seeded `T.rand`), sample-accurate, and it
renders on this box without a GPU.

## When code, when a model
Code is the only tool that puts an event on an exact sample: measured on a
30 s cue with impacts at 8/16/24 s, the js score hit them within 5 ms
(+8 dB each) while no music model placed a real hit within 100 ms. Use
code for hits, stings, risers, ticks, UI-beat beds and anything that must
match picture frames; use `music-gen` for rich arrangements and vocals, and
layer code hits over a generated bed (the best combination for trailers).

## Render
From the workspace root after `source tools/env.sh` (the script loads
puppeteer-core from `studio/node_modules` itself):
`node .pi/skills/js-scoring/scripts/score.mjs <score.js> <out.wav> --dur <s> [--sr 44100]`
Example: `assets/example-riser.js` (2-bar riser + impact at 128 BPM).
Then `tools/killchrome.sh` only if no other render is running.

## Compose from a reference
1. `song-map` the reference → tempo, bars, sections, energy curve.
2. Write the cue on that grid: `T.at(bar, beat)` for every event; tempo =
   the verified bpm. Match energy per section (density, register, filter
   brightness) rather than copying melodies.
3. Build from primitives: oscillators (+detune, unison), filtered noise,
   envelopes on gain/filter, `DynamicsCompressor` bus; samples can be
   loaded as data (decode an ElevenLabs one-shot and trigger it on the grid).
4. Render, then check: duration, peak ≤ -1 dBFS (`volumedetect`), onsets
   on grid (`songmap.py analyze` the render → beats vs grid < 10 ms).

## Rules
- The provided song master is sacred: scoring only ADDS cues under it
  (mixed by `sound-design`) or makes original music when there is no song.
- Keep scores small and readable: one file per cue, meta `{bpm}` at the top.
- Musical cues live on the song's grid; hits land on the picture's frames
  (convert with the project fps).

## Acceptance
WAV rendered, duration exact, peak ≤ -1 dBFS, onsets on the grid, and the
cue listened-for by proxy (onset table + spectrum) against its intent.
