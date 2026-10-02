# LEARNINGS — music-source
- 2026-09-26 YouTube stream fetches are bot-walled from the box IP on every player client; search still works. A Modal container fetch works most of the time (new IP per container) — retry once, then try another upload of the same song.
- 2026-09-26 A SoundCloud "official free version" re-upload measured -1.1 LUFS / +7.4 dBTP (bass-boosted, clipped, 114 s of a 200 s song): gate fallbacks on loudness and expected duration.
- 2026-09-26 SoundCloud refuses DRM-protected label tracks ("This video is DRM protected"): that is the no-DRM rail enforcing itself; move to another upload.
- 2026-09-26 The top YouTube hit for a song is often the music video (Blinding Lights 263 s with skits vs 200 s album): pass --expect with the album length from LRCLIB/iTunes.
- 2026-09-26 Name files after the candidate that actually downloaded; the first-ranked title mislabelled a vocal Levels as "levels-instrumental".
- 2026-09-26 MusicBrainz returns 403 to a generic browser User-Agent; send a descriptive one.
- 2026-09-26 yt-dlp has no PATH binary in tools/: call `$PY -m yt_dlp --js-runtimes node`.
