---
name: seedance-plates
description: Generate video base plates with Seedance 2.5 (reference-to-video / image-to-video) using character sheets, set images and the exact sliced song audio as references so performance and lip-sync land on the real timing - then verify sync and content automatically and by eye, loop until the draft passes, and only then finish at 1080p. Use in phase 6 of a video project, for any lip-synced or performance shot, or when a plate must be re-generated or repaired (sync-lipsync / H3 lip-sync fallback).
license: MIT
compatibility: fal-media (FAL_KEY), song-map (slices), tools/env.sh (ffmpeg, $PY).
metadata:
  author: muse
  version: "1.1.0"
---

# seedance-plates — the camera I rent

Plates give me performance, physics and consistency. They are scaffolding
when the piece is rotoscoped, final picture when it isn't. Either way they
must be on time.

API facts, prices and the call-sheet prompt shape: [references/seedance-2.5.md](references/seedance-2.5.md).

## Per shot
1. **Audio slice**: `songmap.py slice <song> a b audio/slices/<id>.wav` with
   a,b = shot window (+ context pad to reach ≥1.8 s; ≤30.2 s). Record the
   shot's offset inside the slice. Sung windows are 4–8 s and start in a word
   gap, never mid-word; plan a sung passage as a chain of windows with
   alternating framings so any cover cut reads as designed. Non-singing
   plates get the full mix (moves land on the beat).
2. **Refs** (stable order): @Image1 protagonist sheet, @Image2 set, @Image3+
   extra cast / style frame; @Audio1 the slice. Use asset URLs from
   `assets.json` (uploaded once).
3. **Prompt** = shot action in plain physical terms (who does what, on which
   words; camera move; where the calm text zone is) + when singing
   `@Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in
   time: "<the exact words in the window>"` + bible style suffix + avoid
   clause; when not singing, "mouth stays closed". One event per plate.
   Duration = slice length. Aspect per brief. No two plates start from the
   same frame (continue from the previous last frame, or another plate).
4. **Draft**: `draft:true` (480p) via `fal.py run bytedance/seedance-2.5/reference-to-video … --tag <id>-d<n>`.
   Keep `draft_id` in the ledger.
5. **Verify** (below). Fail → change ONE thing (prompt clause, ref, seed)
   and re-draft. Max 4 drafts per shot, then re-think the shot (cut away
   from the mouth, different framing) — don't burn money on a bad idea.
6. **Finish**: `bytedance/seedance-2.5/draft/complete {draft_id}` → 1080p.
   Re-run the sync check on the finished file (finishing can shift frames).
7. **Trim** to the exact shot window using the recorded offset; store
   `plates/<id>.mp4` + `plates/qa/<id>.json`.

## Verification (script: `scripts/platecheck.py`)
- **Duration/format**: ffprobe; within ±1 frame of the slice.
- **Sync over time** (`scripts/syncdiverge.py`, called by platecheck):
  Seedance copies @Audio1 into its own track and the mouth follows that
  track, so compare the two second by second → `sync.verdict`:
  `in_sync` (pass if |lag| ≤ 40 ms) · `diverges` (fail from `t_div`; see
  repair) · `glitch` (short drops that recover: look at the mouth in
  `check_by_eye`; hidden or on a held vowel → keep) · `no_copy` /
  `ambiguous` (audio can't vouch → the mouth sheet decides). Read
  `_sync.png`. Never gate on the legacy `onset_lag_ms`. Detector self-test:
  `scripts/test_syncdiverge.py` (synthetic splices/slips; must exit 0).
- **Mouth sheet**: frames at every word onset and mid-vowel from
  song.json, cropped to the face region, tiled with the word under each →
  I read it: mouth open on vowels, closed on m/b/p, no flapping on rests.
- **Content**: 1 fps contact sheet → on model (vs sheet), in style (vs
  bible), event present, text zone calm, no artifacts (hands, melts,
  extra limbs, gibberish text).
All four must pass. Write the verdict to `plates/qa/<id>.json`.

## Repair paths
- `diverges` → keep the plate up to `sync.cut_song_s` (last eighth before
  the divergence) and cover the rest: re-slice from the cut (in a word gap),
  same prompt, first frame = the plate's frame at `cover_from_plate_s`
  (image-to-video or @Image1), then re-check the cover. Up to 3 covers per
  window, then change framing.
- Performance good, mouth off → `fal-ai/sync-lipsync/v3` with the plate +
  slice (video-to-video), then re-verify.
- Singing close-up from a still → `minimax/h3-max/lip-sync/image-to-video`
  (≤14.8 s per call).
- Timing drift < 3 frames → shift in the edit, don't regenerate.

## Acceptance
Every plate shot in shots.json has a finished file whose QA json shows
duration ok, `sync_ok` true with |audio lag| ≤ 40 ms (or `sync_ok` null and
the mouth sheet passed by eye, or a no-singing shot), every `diverges` plate
cut and covered, mouth sheet read and passed, content passed; ledger total for plates within the estimate ±30%.
