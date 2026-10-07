---
name: voice-reply
description: Answer with a spoken voice note. Turn the final reply into an MP3 with the voice.say runline action (ElevenLabs v4 Turbo, 1-5 s, synchronous) and send it in the same turn with send_file. Use when the user asks for a voice answer, a voice note, an audio reply, "say it" or "let me hear it". Do not use by default.
license: MIT
compatibility: Runline plugin `voice` (bundled in vex/plugins/voice/, live in .runline/plugins/voice/); a channel that carries audio files.
metadata:
  author: muse
  version: "0.1.0"
  vex-secrets: "ELEVENLABS_API_KEY"
---

# voice-reply

## Steps
1. Write the reply for the ear.
   - Use short sentences and plain words, in the user's language.
   - Do not use lists, tables, links, code or markdown.
   - Write numbers the way a person says them.
   - Keep it under 60 seconds (about 900 characters).
2. Speak it in `execute_actions`:
   `return await voice.say({ text, language: "he" })`.
   - `language` is optional (ISO 639-1). Leave it out to auto-detect.
   - `voice` (an ElevenLabs voice ID) and `speed` (0.7-1.2, default 1.1)
     are optional.
3. Call `send_file` with the returned `path` in the same turn. Do not add a caption.
4. Send text after the voice note only for content that the user must read
   or copy, such as a link, a code or an exact figure.

## Rules
- The call is synchronous. Do not put it in a background job, a schedule
  or a sensor.
- Send one voice file for each answer. Do not split one answer into many notes.
- If `voice.say` throws (quota, key), send the reply as text. Add one
  line to say that the voice failed.

## Acceptance
- `voice.say` returned a `path` and `seconds > 0`.
- `send_file` returned "Sent <file>".
- The spoken text contains no markdown symbols, links or lists.

## Install on another agent
1. Copy this skill folder to `.pi/skills/voice-reply/` in that workspace.
2. Copy `vex/plugins/voice/` to `.runline/plugins/voice/` in that workspace.
3. Make the secret `ELEVENLABS_API_KEY` available to that agent.

The plugin loads on the next agent run. Verify with
`vex.actions.catalog.get({ plugin: "voice" })`: the result must show `loadError: null`.
