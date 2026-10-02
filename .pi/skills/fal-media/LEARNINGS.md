# LEARNINGS — fal-media
One line per lesson, dated, as intent.

- 2026-09-26 Seedance 2.5 reference-to-video accepts audio refs only 1.8–30.2 s each (≤15 MB, MP3/WAV); slice songs per shot, never pass the whole track.
- 2026-09-26 seedance-2.5/draft/complete returns no duration, so finishes logged $0 (4 × $4.76 missed on pdoom-test); estimate() now ffprobes the output video when duration is absent — check the ledger total against n_seconds × rate after every finish.
- 2026-09-26 fal CDN URLs are PUBLIC by default. upload is for model inputs only — never a delivery channel for finished work. To pull an exposed file: PUT https://rest.fal.ai/storage/files/acl?url=<enc url> body {"default":"hide","rules":[]} (verified → 404). Raw DELETE is not supported with a normal key.
- 2026-09-26 The static ffprobe segfaults on https URLs: cost estimates probe the DOWNLOADED files (ElevenLabs and Sonilo lines were logged null before the fix and back-filled by hand).
- 2026-09-26 ElevenLabs Music on fal bills per STARTED minute (a 30 s cue costs $0.60, same as 60 s): ask it for up to 60 s and cut on the grid.
- 2026-09-26 A 422 from ElevenLabs on `audio_reference` (copyright screening of a commercial song) returned no result and no charge; fal.py logs nothing on failure.
- 2026-09-26 SAM 3 (`fal-ai/sam-3/image`, $0.005) returns the same mask URL as `image` and `masks[0]`; the img-unit estimate now counts unique URLs (it had logged $0.01 for one call).
