---
name: music-source
description: Get any song, beat, instrumental, soundtrack/OST, a cappella, loop or SFX as a first-class asset - search and fetch best-quality audio by URL or query (YouTube incl. ytsearch via the Modal route, SoundCloud, Bandcamp, X via xfetch), keep the source URL, make a loudness-normalised copy, pull synced lyrics (LRCLIB) and metadata (MusicBrainz, Deezer BPM hint, iTunes), search open libraries (Openverse/Jamendo/Freesound, Internet Archive, ccMixter) with licences, and keep Muse's small indexed music library (library/music/index.json with bpm, key, sections, hits, tags). Use when a video needs an existing song or beat, when the principal names a track or sends a link, when looking for type beats, official instrumentals or soundtracks, or when adding to / picking from the library.
license: MIT
compatibility: tools/env.sh ($PY with yt_dlp + essentia, ffmpeg, node for yt-dlp JS); MODAL_TOKEN_ID/SECRET for the YouTube route; no keys for LRCLIB/MusicBrainz/Deezer/iTunes/Openverse/Archive/ccMixter.
metadata:
  author: muse
  version: "1.0.0"
---

# music-source — any track, with its provenance

Songs are first-class material (the principal, personal non-commercial use). Limit I
keep: **no DRM circumvention** — public streams, his files, open libraries.
Encrypted streams (Spotify, Apple Music, Tidal, full Deezer) are out; if only
those have it, say so and offer a public upload or his own file.

Script: `scripts/musiclib.py` (run with `$PY`). Every fetch writes
`<slug>.<ext>` (untouched best stream), `<slug>.norm.mp3` (-14 LUFS / -1 dBTP,
two-pass) and `<slug>.source.json` (url, via, uploader, codec, fetched_at,
fallbacks tried). Put project audio in `projects/<slug>/audio/`.

## Find
- `search "<query>" --kind song|instrumental|beat|ost|acappella|extended`
  (YouTube + SoundCloud). Kind appends the pattern that finds that job:
  "official audio", "official instrumental", "type beat", "original
  soundtrack", "acapella", "extended mix". Ranked: official/Topic/VEVO up,
  live/cover/sped-up/nightcore/8D/bass-boosted down unless asked, 30 s
  SoundCloud previews out.
- Known song: get its album length first (`meta` or `lyrics`) and pass
  `--expect <s>`; it beats a music-video cut with skits or intros.
- Open/licensed material (loops, stems, SFX, CC tracks):
  `open "<query>" --src openverse|archive|ccmixter [--license cc0,by] --get I`.
  Keep the licence + attribution line from the result in source.json.

## Fetch
`fetch <url|"query"> [--kind K] [--expect S] --out projects/<slug>/audio`.
Route (automatic): local yt-dlp → YouTube bot wall → Modal container
(`song-map/scripts/modal_audio.py::fetch`, a new IP each try, 2 tries) →
next duration-matched candidate (other uploads, SoundCloud, Bandcamp).
A candidate louder than -5 LUFS is rejected (bass-boosted/clipped re-upload).
X videos: `reference-mesh/scripts/xfetch.py` (writes `video_audio.mp3`).
The principal's own file: copy it in and write the source.json by hand.

## Lyrics and facts
- `lyrics "<artist>" "<title>" --duration S --out DIR` → `lyrics.txt`,
  `lyrics.lrc`, `lyrics_lines.json` (LRCLIB line times). LRC times may belong
  to another edit of the song; `song-map` detects and applies the offset.
- `meta "<artist>" "<title>"` → MusicBrainz ids/lengths, Deezer bpm/gain/ISRC,
  iTunes genre. Every number there is a hint to verify with `song-map`.

## Library (`library/music/`)
- `add <audio> --title --artist --kind --tags a,b [--song song.json]` copies
  the normalised file, runs `song-map` (no words) unless a song.json is given,
  and indexes title, artist, kind, source, licence, duration, bpm, key, LUFS,
  sections, hits. `ls --kind beat --bpm 120-130 --key "A minor" --max-dur 60`;
  `rm <slug>`; `du`.
- Hard cap 1500 MB (disk law); stems and raw downloads are never library
  items. Add only what will be reused: beds, beats, stings, reference songs.

## Acceptance
The file plays (`ffprobe`), its duration is within 3 % of the expected
length (or the difference is explained: radio edit, extended mix), the
source.json carries the URL and route, the normalised copy measures
-14 ± 0.5 LUFS, and — for vocal songs — lyrics came with it or their absence
is noted. Library adds show up in `ls` with bpm and key.
