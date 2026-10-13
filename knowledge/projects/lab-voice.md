---
kind: project
seen: 2026-10-06
tags: [lab, tts, elevenlabs, benchmark, voice-reply]
---
# lab-voice: Eleven v4 / v4 Turbo bench and the voice-reply skill

**Brief.** The lab has two parts.

- **v4 bench.** the principal sent ElevenLabs' Eleven v4 launch post (@tadaspetra) with "do compare from this to what we are using. All stat". The answer had two halves. The first was the published stats: the Artificial Analysis arena, pronunciation and prices, plus `/v1/models` and fal's pricing API. The second was a bench on our real voice jobs through our real route: the Antioch cast (library voices) through fal, 7 lines × 2 takes × 3 models = 42 takes. The lines covered long narration, names, numbers and dates, a Scouse line, a Glaswegian line, a `[whispers]` line and Hebrew. The default $150 cap applied.
- **Voice replies.** the principal asked how fast an agent can answer with a voice file, not live speech, once its text answer is final. He wanted this as a skill for any agent. He then asked about cost, a free local model, the cost for about 10 team members, and a more human, slightly faster delivery without extra tags. He asked for "a very short skill, just a runline tool". After the build he said: "No need to post auto, set the agent to do so". He also asked for an install on an agent of another deployment, with its own ElevenLabs account.

**What worked**
- **v4 is a drop-in on our pipeline.** It uses the same fal call shape, the library voice IDs work, and it returns the same per-character timestamp blocks. All model findings are in [[voice-casting]].
- **The QC stack from `antioch-1098` works as a model bench.** It measures WER against the script (`gpt-4o-transcribe`), voice stats (wpm, F0 spread, whisper dB drop) and a blind proxy ear (`gpt-audio`). It lives in `projects/lab-voice/tools/`: `bench.py gen|qc` and `ears.py`. To bench a new TTS model, change the `MODELS` table.
- **Timing against fal's synchronous endpoint** (`https://fal.run/<endpoint>`) gives clean generation times. Wall times from `fal.py`'s queue polling are quantised by its backoff.
- **A level-matched A/B file lets the principal's ear decide.** Each line plays v3 → v4 → Turbo at −20 LUFS. The whisper line keeps its raw level, so its depth still shows.
- **A voice reply is fast.** v4 Turbo made 43 s of speech in 3.9 s, and short replies take 0.6–1.0 s. The latency table is in [[voice-casting]].
- **`voice.say({ text, language? })`** is a runline action in `.runline/plugins/voice/`. It uses v4 Turbo, the Will voice and the tuned settings, and returns an MP3 path. The call is synchronous, so the agent sends the file with `send_file` in the same turn. No background job wakes the agent again. Each call logs its cost, and files are deleted after 7 days.
- **The skill `voice-reply`** (about 40 lines) says when to use voice, how to write a reply for the ear, and to fall back to text if the voice fails. It carries a copy of the plugin in `vex/plugins/voice/` and declares `vex-secrets: ELEVENLABS_API_KEY`. It passes `vex.skills.validate`. It is not the default: an agent speaks only when a person asks for it.

**What didn't**
- **A runline plugin cannot post audio into a chat.** Vex gives plugins only `sessions.messages.send`, which takes text. File delivery goes through `send_file` and the channel renderer. The principal decided that the agent sends the file, so no Vex change is needed.
- **The runtime loads plugins only from `.runline/plugins/`.** A skill's `vex/plugins/` folder is an install package. This workspace keeps both copies, and they must stay identical.
- **Muse cannot reach another deployment's agents.** They are not in `vex.teammates.available`. A secret link made here saves the key to Muse's workspace, not to theirs. The handoff is a zip that the principal forwards, and the other agent makes its own `ELEVENLABS_API_KEY` link. A platform-level key serves every agent on that deployment.
- **Open-ended blind accent ID failed on ~3 s lines.** It called the Glaswegian voice "RP" on every take. A targeted 0–10 question per accent was needed ([[voice-casting]]).
- **The proxy ear's preference flipped with play order** on 2 of 5 v3|v4 pairs. Only order-robust wins count.
- **Free Hebrew TTS is not ready.** Chatterbox dropped a sentence and read Hebrew words backwards. OmniVoice's licence blocks business use. This 2-CPU box is also too slow to run either model fast.
- **The direct key cannot read its own credit balance**, so free-quota use is an estimate.

**Spend.** The bench cost $0.48 of the $150 default cap: 6,498 TTS characters (v3 $0.22, v4 $0.17, Turbo $0.09). The voice-reply work cost $0 in cash. It ran on the free direct key's monthly credits, plus one Chatterbox take on fal (300 characters, under $0.01). Ledger: `projects/lab-voice/ledger.jsonl`.

**Cost of voice replies.** A 30 s reply is about 500 characters: about $0.02 on Turbo or $0.04 on v4. The free plan covers about 40 Turbo replies a month. For 10 people at 3 replies a day, the cost is about $13 a month on Turbo ($26 on v4), and the $22 Creator plan covers Turbo. At 10 replies a day each, the cost is about $44 on Turbo ($88 on v4), inside the $99 Pro plan. Plan prices are in [[voice-casting]].

**Final**
- **Bench:** `outbox/eleven-v4-vs-v3.md` (report), `outbox/eleven-v3-v4-bench.png` (six-panel chart) and `outbox/eleven-v3-v4-turbo-AB.mp3` (A/B), sent to the principal's web chat. Takes are in `projects/lab-voice/takes/`, measurements in `projects/lab-voice/review/`.
- **Voice replies:** scripts `projects/lab-voice/tools/voice_reply.py` and `voice_reply_par.py`, the skill `.pi/skills/voice-reply/` and the plugin `.runline/plugins/voice/`. `outbox/voice-reply-skill.zip` holds both in workspace-root layout, with install steps for the other agent in the caption. It went to the principal on WhatsApp.
- **Verdict:** v4 Turbo is the default for all speech, by the principal's ear: "v4 turbo is the best. Let's use it from now." Broad-accent library voices stay on v3 until each one is re-auditioned.

## How the principal works with this
- A launch-tweet link with "compare to what we are using, all stat" asks for the published numbers and a bench on our own jobs and route. Vendor claims alone don't answer it.
- After a long report he asked "Bottom line?". Lead every comparison with a three-sentence verdict: what to switch to, the catch, and what is cheaper for drafts.
- He judges voices by ear on an A/B file, and his ear decides the model.
- He wants new capabilities as short skills that other agents can install, and he prices them for his team of about 10 people.
- The team voice is his call. The blind test could not separate Will, Chris and Eric, so Will stays until he picks one.
