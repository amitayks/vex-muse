# LEARNINGS — sound-design
One line per lesson, dated, as intent.
- 2026-09-26 The ElevenLabs key is restricted: /v1/user/subscription returns 401 (no user_read), sound-generation works. `eleven.py usage` failing is not a dead key.
- 2026-09-26 ElevenLabs Music on our direct key is free-tier (402 paid_plan_required); fal-ai/elevenlabs/music works (prompt + music_length_ms + force_instrumental) but fal.py has no RATE for it — ledger logs est None; estimate by hand (~$0.8/min).
- 2026-09-26 Music models don't land hits on requested timestamps (lab: 40-650 ms off, mostly no level jump); design the hits on top of the bed.
- 2026-09-27 Our direct ElevenLabs key is free tier: TTS with library (shared) voices returns 400 `free_users_not_allowed`; the same voice ids work through fal `fal-ai/elevenlabs/tts/eleven-v3` ($0.10/1k chars) with character timestamps — use fal for any library voice.
- 2026-09-27 Accent casting without ears: gpt-audio blind accent ID separates Scouse/Glaswegian/Yorkshire/RP reliably; its absolute 1-10 "quality" scores are flat and its A/B picks have strong position bias — run both orders and trust only order-robust wins.
- 2026-09-27 v3 glitches are rare but real (a line came back in pseudo-Turkish, another as "Ai, Maria!"): transcribe every take and compare with the script before placing it; respell names that drift ("Fee-rooz").
