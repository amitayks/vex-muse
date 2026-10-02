# LEARNINGS — js-scoring
- 2026-09-26 OfflineAudioContext renders in chrome-headless-shell without GPU in seconds; the example riser rendered 5 s at -2.3 dBFS peak.
- 2026-09-26 score.mjs failed with ERR_MODULE_NOT_FOUND from studio/: ESM resolves packages next to the script, not the cwd. It now createRequire()s puppeteer-core from studio/.
- 2026-09-26 Lab cues (projects/lab-music/tests/js/): a 16-bar 128 BPM beat and a 90 BPM trailer cue with impacts exactly at 8/16/24 s rendered in seconds; hit error 5 ms vs 40-650 ms for eight music models. Master code cues (they render around -21 LUFS).
