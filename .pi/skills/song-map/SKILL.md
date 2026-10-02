---
name: song-map
description: Turn a song into song.json - the timing spine every shot, cut, lyric and sync check hangs on - tempo, beats, downbeats/bars (beat_this on a Modal GPU, or the local tracker with the drum stem), key (Essentia EDMA), loudness, sections grouped and labelled, hits and drops, energy curve, and word-level lyric timings aligned to the real lyrics (LRCLIB-anchored, chunked whisper on the vocal stem); plus Demucs stems (Modal or fal), exact audio slices for video-model audio references, a click-track for sync QA and an eval command that scores a map against a reference. Use at the start of any music video, lyric video, beat-synced edit, after any track edit, or when cutting audio segments for Seedance/lip-sync.
license: MIT
compatibility: tools/env.sh (ffmpeg, $PY with numpy/scipy/essentia); MODAL_TOKEN_ID/SECRET for stems + beat_this (modal_audio.py); OPENAI_API_KEY for word timings; FAL_KEY for the fal-ai/demucs alternative.
metadata:
  author: muse
  version: "1.1.0"
---

# song-map — the song is the clock

Everything in a music video is timed to the song. `song.json` is the single
source of timing truth; nothing is timed by ear or by guess. Map the exact
file the final encode will use — after any `track-edit`, map again.

## Steps
1. **Lyrics**: `music-source/scripts/musiclib.py lyrics "<artist>" "<title>" --duration S --out audio/`
   → `lyrics.txt` + `lyrics_lines.json` (LRCLIB line times). No LRC: exact
   lyrics from the brief/artist page, one sung line per text line.
2. **Stems** (default Modal L4, ~40 s per 4-min song, ≈ $0.013):
   `$PY -m modal run scripts/modal_audio.py::stems --audio <song> --out audio/stems`
   (htdemucs_ft: vocals/drums/bass/other). Alternative: `fal-ai/demucs`
   via fal-media ($0.17 per 4 min). Never on this box's CPU (2 vCPU: 10 min).
3. **Grid** (default): `$PY -m modal run scripts/modal_audio.py::beats --audio <song> --out audio/beats.json`
   (beat_this, ~15 s, ≈ $0.004). Offline fallback: the local tracker with
   `--drums audio/stems/drums.mp3` (mix-only picks the wrong bar phase on
   four-on-the-floor songs).
4. **Analyze**:
   `$PY scripts/songmap.py analyze <song> --beats audio/beats.json --vocals audio/stems/vocals.mp3 --lrc audio/lyrics_lines.json --out audio/song.json`
   (`--lyrics lyrics.txt` instead of `--lrc` when there is no LRC;
   `--no-words` for instrumentals; `--bpm` to force a tempo).
5. **Verify tempo — never trust one estimator.** Octave errors are the
   classic failure (a 171 BPM song reads 85.5 on the local tracker and on
   Essentia; beat_this got 171). Check `bpm_candidates`, bar lines on
   lyric-line starts and section changes, and
   `songmap.py click song.json <song> audio/click.wav` against the drum stem.
6. **Verify words.** `lrc_check`: `lrc_shift_s` is the detected offset of the
   LRC's own edit (album vs radio edit, lyric video) — expect it; then
   `within_1s` ≥ 0.8 of heard lines. Spot-check the first word of every line
   on the vocal stem waveform; hand fixes get `"matched":"manual"`.
7. **Label sections**: `sections[].group` (A/B/C by similarity) and a
   `label` guess (chorus = the loudest repeated group). Confirm by lyric
   repetition; choruses are the video's recurring stage.

## Slicing audio for video models
`songmap.py slice <song> <t0> <t1> audio/slices/<shot>.wav` — exact, no fade.
Seedance audio refs must be 1.8–30.2 s: a shorter line gets context padding
(`--pad`), and the shot's own offset inside the slice is recorded in
`shots.json` so the plate is trimmed back to the exact window.

## Output contract (`song.json`)
`duration, bpm, bpm_candidates, bpm_tracked, grid_source, grid_resid_ms, beat,
beats[], downbeats[], key, key_confidence, key_source, key_candidates[],
chroma[12], lufs, true_peak_db, lra, sections[{t0,t1,bars,energy,group,label}],
hits[{t,strength}], energy_changes[{t,kind:drop|break,db}], energy_10hz[],
words[{w,t0,t1,line,matched}], lines[{i,text,t0,t1,lrc_t,heard}],
lyric_coverage, lrc_check, asr_offset`. Times in seconds from the start of
the file used in the final encode.

## Scoring a map
`songmap.py eval song.json --ref beats.json --lrc lyrics_lines.json --bpm-true 116 --key-true "F# minor"`
→ beat/downbeat F-measure at ±70 ms, median grid offset, tempo error
(octave-aware), key match / top-3, LRC line agreement.

## Acceptance
song.json exists; tempo passed the bar/section and click-vs-drums checks
(report the offset); downbeats agree with beat_this (F ≥ 0.9) or were
checked on the click track; every lyric line has t0/t1 with coverage ≥ 0.85
or the misses hand-fixed; sections labelled. Report tempo, key, sections
and word coverage in one line.
