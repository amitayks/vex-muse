---
name: performance
description: Act a character on camera without filming a person - write the actor's direction (blocking, eye-line, delivery, listening beats), generate an AI-actor driver performance (Veo 3.1 Fast text-to-video with voice, in a plain version of the set and costume), transfer it onto the cast still (Kling v3 Pro motion-control), re-voice the line with the character's cast voice (ElevenLabs voice changer, timing kept), cover conversations (speaker, listener, overlaps, intercom/radio) and audition voices. Use for every acted or speaking shot, for the actor station of a crew line, for voice casting of a character, or when a performance reads as theatre.
license: MIT
compatibility: FAL_KEY; tools/env.sh; ElevenLabs library voice ids via ELEVENLABS_API_KEY (search only).
metadata:
  author: muse
  version: "1.0.0"
---

# performance — the actor's job, done by models

Evidence and numbers: [[generation-field-notes]] (Performance transfer), [[voice-casting]], `lab-cinematic`.

## 1. Direction (write it before any call)
For each acted shot: who speaks, who listens, where each one looks (screen left/right, up/down — matched
to the reverse shot), the line, the subtext, the physical action, and what changes by the end. A
listener shot is a performance too: reaction, breath, a look away.

## 2. Driver (the AI actor)
- `fal-ai/veo3.1/fast` text-to-video, 6–8 s, 720p, audio on ($0.15/s). Prompt: a plain actor of the same
  age, build and costume, in a plain version of the set, same framing and eye-line as the cast still,
  "static camera on a tripod", the exact line in quotes, delivery words, pauses, and the action.
- Transcribe the driver (word times). Reject a take that changes the words or rushes the pauses.
- Gesture on the wrong side (cheek, hand)? Mirror the driver (`hflip`) and transfer with
  `character_orientation: image`.

## 3. Transfer onto the character
- `fal-ai/kling-video/v3/pro/motion-control` ($0.168/s): `image_url` = the cast start frame (cleaned,
  no bars), `video_url` = driver, `character_orientation` video (default) or image (mirrored drivers),
  `keep_original_sound: true`, prompt keeps face, costume, props and room "exactly as in the image".
- The output trims the driver's start: measure the lag on its audio copy against the driver and place
  the re-voiced line by it.
- Simple acting (one word, a look) may skip the driver: Veo 3.1 image-to-video with the line in the prompt.

## 4. Voice
- Cast voice = an ElevenLabs library voice id, chosen per character (accent, age, texture), auditioned on
  the character's real line, 3 candidates; record the choice in `assets.json` (`voice_id`).
- Re-voice: `fal-ai/elevenlabs/voice-changer` (`voice` = id, `remove_background_noise: true`). Timing stays
  within ~10 ms of the driver, so lips stay matched.
- Check every line by transcription (word times) and, for names, a targeted 0–10 ear question.

## 5. Conversations (never theatre)
- Coverage per exchange: speaker CU, listener CU, a two-shot or over-the-shoulder; drivers for the
  listener's silent reaction too. Eye-lines opposed across the cut.
- Overlaps and cut-offs are in the driver prompt; intercom/radio lines can stay off-screen.
- Mix (with sound-design): worldize each voice to its space (room, wind, radio band-pass, mask), never dry.

## Acceptance
Per acted shot: the direction note, the driver(s) with transcripts, the transferred take(s), the re-voiced
line(s) with measured lag, and the critic verdict on the take (crew `take.md` rubric) — lip-sync ≥ 7 and
acting ≥ 7 — or the reason it was re-made.
