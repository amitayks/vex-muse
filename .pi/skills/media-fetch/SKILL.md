---
name: media-fetch
description: Download a public video or its audio from YouTube (and the 1,800+ other sites yt-dlp supports) when the server is blocked - YouTube answers "Sign in to confirm you're not a bot" to data-center servers and data-center proxies, so the fetch runs in short-lived Modal containers on fresh addresses with a proof-of-origin token helper, first success wins - and lands the mp4/m4a plus info.json (title, channel, duration, chapters, description) and optional subtitles in a project folder. Use when someone sends a YouTube (or other video) link to analyze, transcribe, cut slides from, or reuse; when yt-dlp, ytdl-core, Steel or a proxy hit the bot wall; or when asked for "yt-dl" / "yt-dlp". Public media only.
license: Proprietary
compatibility: tools/env.sh ($PY with the `modal` package) and MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in the environment. No YouTube login, no proxy.
metadata:
  author: muse
  version: "1.0.0"
---

# media-fetch — public media from a fresh address

"yt-dl" = this skill. It wraps yt-dlp; it does not write extractors.

## Why the server fails and this works
- YouTube has two walls. **Bot wall:** blocks by IP; data-center servers, cloud browsers and
  data-center proxies all hit it. **PO-token wall:** even past the bot wall, formats need a proof-of-origin token.
- `scripts/modal_fetch.py` starts waves of 8 single-use Modal containers in 4 regions with 4 YouTube client
  modes. About 1 address in 10–20 passes the bot wall; the bgutil helper in the container mints the PO token;
  the first success wins and the rest stop. A 13-minute 720p lecture took about one minute and cost cents.

## Run
```bash
source tools/env.sh
$PY -m modal run .pi/skills/media-fetch/scripts/modal_fetch.py --url "<url>" --out projects/<slug>/source [--mode video|audio] [--height 720] [--subs he,en]
```
- Run it as a background execution (it can take 1–5 minutes) and wait on it.
- Read the last line `RESULT {...}` or `<out>/fetch-result.json`: `ok`, `files`, `meta.title`, `route`,
  `blocked` (addresses that hit the wall).
- Video default is the best ≤ 1080p mp4; use `--height 720` for analysis (smaller). `--mode audio` for
  transcription only. `--subs he,iw,en` saves YouTube's captions when they exist (auto captions are rough;
  the real transcript comes from a transcription service).

## After the download
- Check it: `ffprobe` duration ≈ `meta.duration`, a frame at the middle looks right.
- Songs and beats for a video: skill `music-source` (audio, library, lyrics); this skill is the fallback when its route hits the wall.
- Transcribe the audio with the transcription service you have.
- Slides from a filmed talk: scene-change frames (`ffmpeg -vf "select='gt(scene,0.3)',showinfo"`), then dedupe
  near-identical frames and read them.
- Disk: a 13-minute 720p video is about 120 MB. Delete the video when the work is done; keep transcript and frames.

## Limits
- Public media only: private, members-only or age-gated videos need a login (cookies from a separate,
  throwaway Google account - never a personal one). No DRM content (Netflix, Spotify music).
- If `ok:false` with every error a bot wall: run again (new addresses), or raise `--tries` to 48.
- If the error is about formats or "n challenge": update yt-dlp (the image installs the latest at build;
  bump the image by editing the script, e.g. a comment in `image`) and file a line in LEARNINGS.md.
- Respect copyright: fetch for analysis and work the person is entitled to; do not republish.

## Acceptance
`fetch-result.json` has `ok:true`; the file plays (`ffprobe`) and its duration is within 2 % of `meta.duration`;
the person gets the result of the work (transcript, slides, analysis), not a raw dump.
