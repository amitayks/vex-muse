---
name: track-edit
description: Edit music on its own bar grid, sample-accurate and click-free - radio edits and cut-downs on downbeats, fit a track to an exact video length (best window, keep-intro-and-ending edit, or loop/extend a bed), loops, tempo and pitch change without artifacts (rubberband), stem remixes (instrumental, a cappella, drums-only, any gains), beat-matched DJ transitions with bass swap, mashups (vocal of one song over another, tempo- and key-matched), ducking music under a voice-over, and mastering to a LUFS target with verification. Use whenever a fetched, library or generated track must be shortened, lengthened, re-timed, re-keyed, remixed, combined or mastered before (or instead of) being mapped and cut to picture.
license: MIT
compatibility: tools/env.sh (static ffmpeg with rubberband/loudnorm/ebur128/sidechaincompress; $PY with numpy/scipy); song.json from song-map; stems from song-map/scripts/modal_audio.py or fal-ai/demucs.
metadata:
  author: muse
  version: "1.0.0"
---

# track-edit — cut music where music cuts

A cut lands on a downbeat or it is heard. Every edit here is planned on
`song.json` downbeats and joined with a 30 ms equal-power crossfade; fitting
to a length stretches at most 3 % (rubberband) so the last bar ends exactly
on the frame, or ends on a fade. Script: `scripts/trackedit.py` (`$PY`),
every command prints JSON (plan, spans, ratio, cut points) — keep it as the
edit log in `projects/<slug>/audio/edits.jsonl`.

## Order of work
1. Source (`music-source`) or generate (`music-gen`) the track.
2. `song-map` it (the beat_this grid + drum stem: downbeats must be right,
   check the click track) → `song.json`.
3. Edit here → `audio/edit.wav`.
4. `song-map` the EDIT again: that file is now the master every shot,
   lyric and plate is timed to. After lock the master is sacred
   (`sound-design` only adds under it).

## Recipes
| Job | Command |
|---|---|
| The best N seconds for a hook/teaser | `fit in out --song s --dur N --mode window --prefer chorus` (starts on a section boundary, ends on a bar) |
| Shorten but keep intro and ending (radio edit) | `fit ... --mode edit` (removes a whole middle span between section/bar boundaries) |
| Longer than the song (bed, extend) | `fit ... --mode loop` or `loop in out --song s --bars 17:24 --dur 60`; generative extension: `music-gen` (Stable Audio 3 outpaint / ACE-Step repaint) |
| Keep specific bars | `cut in out --song s --bars 1:8,17:24` |
| New tempo, same pitch | `tempo in out --from 116 --to 128` (≤ ±8 % sounds natural; beyond, re-generate) |
| New key, same tempo | `pitch in out --semitones -2` (formants preserved; ≤ ±3 st for vocals) |
| Instrumental / a cappella / drums-only | `stems out --dir stems/ --gains vocals=0,drums=1,bass=1,other=1` |
| Song A into song B | `xfade a b out --song-a sa --song-b sb --a-bar 25 --b-bar 21 --bars 8` (B tempo-matched, highs cross, bass swaps in one beat at the midpoint) |
| Vocal of A over B | `mashup vocals_A inst_B out --song-v sA --song-i sB [--v-bar --i-bar --bars]` (tempo + key matched, instrumental ducks 3 dB under the vocal) |
| Music under a voice-over | `duck music voice out --db 8` |
| Loudness for the platform | `master in out.mp3 --lufs -14 --tp -1` (X/YouTube/IG: -14; the result is re-measured and flagged `ok`) |

## Judgment
- Prefer edits over stretch, stretch over re-generation, and never stretch
  a vocal more than ~5 % or pitch it more than ~3 semitones.
- Transitions: cut or crossfade at phrase starts (every 4 or 8 bars), not
  just any bar; a transition needs the same tempo (auto) and compatible keys
  (same, relative, or a fifth apart — check `song.json.key`).
- Mashups need a clean a cappella: htdemucs_ft vocals bleed hi-hats; keep
  the instrumental's drums loud enough to mask it.
- Fits for picture: the video's length in frames is the target
  (`round(dur × fps) / fps`), and the last bar or the fade ends on it.

## Acceptance
`check out --dur D --lufs L --cuts t1,t2` passes: duration within one frame,
loudness within ±0.5 LU after `master`, no click at any cut point
(`spike_vs_context < 1.5`), and the edit re-mapped with `song-map` shows its
downbeats continuous across every cut (no half-beat jump in the grid).
