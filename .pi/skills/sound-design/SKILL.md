---
name: sound-design
description: Add sound design to a video without touching the song - spot SFX cues from shots.json (whooshes on whips, impacts on slams, risers into choruses, UI blips on inserts, ambience beds), generate them with ElevenLabs (sound effects, music stings, voice isolation), place them on beat, and mix under the master with ducking so the vocal is never masked, to a loudness target. Use in phase 8 of a video project, or whenever a cut needs SFX, transitions sounds, a sting, or an isolated vocal.
license: MIT
compatibility: Env ELEVENLABS_API_KEY; tools/env.sh (ffmpeg).
metadata:
  author: muse
  version: "1.1.0"
---

# sound-design — the song stays sacred

The song master is never edited, re-timed or re-mastered. Sound design sits
under it and serves the picture's hits.

## Spot
From shots.json (`sfx[]` + transitions + hero-text slams) list cues:
`t (snapped to a beat or a visual hit) · kind · prompt · dur · gain_db`.
Prefer few, meaningful cues: every transition that moves space, every text
slam, every insert, chorus risers (2 bars), a final tail. Silence is a cue
too.

## Generate
`scripts/eleven.py sfx "<precise physical description>" audio/sfx/<cue>.mp3 --dur <s> --ledger projects/<slug>/ledger.jsonl --tag <cue>`
(direct key works for SFX; the same model is `fal-ai/elevenlabs/sound-effects/v2`, $0.002/s, via fal-media).
Measure each SFX file's onset/peak offset and cue by the peak, not the file start.
Prompts are physical and specific ("paper sheet whipped fast past the mic,
dry, short tail"), matching the medium of the picture (paper world → paper,
ink, pencil, stamp sounds). Generate 2 variants for hero cues; pick by ear-
proxy (spectrum/length check) and context. Reuse cues for recurring motifs.

## Music under picture (no song, or a bed under voice)
The bed comes from the library, `music-source`, or `music-gen`; it is cut
to length on its bars with `track-edit fit` BEFORE the picture is timed to
it. Picture hits that the music must land on are added as designed hits
(js-scoring or SFX) on top of the bed, never trusted to the generator.
Voice-over: `track-edit duck music voice out --db 8`.

## Mix (ffmpeg, one filter graph, written to `audio/mix.sh`)
- Each cue: `adelay` to its t, `volume` to its gain.
- Sum cues → `sidechaincompress` keyed by the vocal stem (or the master)
  so cues duck ~4–6 dB under singing.
- Master + ducked cues → `alimiter` → `loudnorm` two-pass to the brief's
  target (default -14 LUFS integrated, -1 dBTP).
- Output `audio/mix.wav`; the render muxes this, never the raw song, once
  sound design exists.

## Checks
- `ebur128` report: integrated within ±0.5 LU of target, true peak ≤ -1.
- Vocal clarity: loudness of the mix minus the master during sung words
  ≤ +1 dB (cues never sit on top of words).
- Sync: cue onsets within 1 frame of their visual hits (strip check).

## Acceptance
mix.wav exists, loudness report attached to review, every cue in the spot
list placed and logged, song timing unchanged (duration and first onset
identical to the master).
