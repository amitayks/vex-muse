# Seedance 2.5 on fal — facts and prompt shape (checked 2026-09-26)

## Endpoints
- `bytedance/seedance-2.5/reference-to-video` — prompt + up to 30 images
  (`image_urls`, cite @Image1..), 10 audio (`audio_urls`, @Audio1.., MP3/WAV,
  each 1.8–30.2 s, ≤15 MB), 10 videos (`video_urls`, @Video1.., MP4/MOV,
  1.8–30.2 s, ≤200 MB). `task`: reference | editing (modify @Video1) |
  extension (continue @Video1). `duration` 4–30 or auto. `aspect_ratio`
  auto/21:9/16:9/4:3/1:1/3:4/9:16. `resolution` 480p/720p/1080p.
  `generate_audio` (default true; same price). `draft` → 480p + `draft_id`.
  `bitrate_mode` standard|high. `seed`.
- `…/image-to-video` — `image_url` first frame, optional `end_image_url`
  last frame (controlled transitions between two designed frames).
- `…/text-to-video` — prompt only (use for abstract inserts / tests).
- `…/draft/complete` — `draft_id` → 1080p within 7 days, same account.
- Approx price: 480p w/ audio ≈ $0.22/s; 720p ≈ $0.28–0.47/s; 1080p ≈ $1.16/s.

## Prompt shape that works (write it like a shot on a call sheet)
```
[SHOT] medium shot, locked camera slowly pushing in; 16:9; subject right third, left third calm pale sky for text.
[WHO] @Image1 is the singer (match face, hair, costume exactly); @Image3 are the backup dancers.
[WHERE] @Image2 is the set; keep its palette and props.
[ACTION] on the first line she turns to camera and sings; on "FOOM" all dancers hit the same arms-up pose; she holds the last note with eyes closed.
[AUDIO] @Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in time: "<exact words in this window>". Mouth closed in the rests; movement on the beat of @Audio1.
        (not singing: "moving in time with @Audio1 … Her mouth stays closed, face expressionless.")
[STYLE] <bible style suffix verbatim>
[AVOID] <bible avoid clause>; no text, no logos, no extra people, no camera shake.
```
- One event per plate; name the words that trigger actions (from song.json).
- Keep image refs stable in order across a project (sheet=@Image1 always).
- For dance: reference a video (@Video1) of the move for motion, images for look.
- Non-singing inserts: `generate_audio:false` is not cheaper — keep it on
  and discard, or use it as a free SFX reference.
