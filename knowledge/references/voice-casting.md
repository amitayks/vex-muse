---
kind: technique
tags: [speech, tts, casting, elevenlabs]
audience: studio-internal
half_life: 90
rights: safe
seen: 2026-10-10
summary: Speech is the studio's newest capability. Covers access to ElevenLabs v3/v4 voices (direct key vs fal), the v3 vs v4 vs v4 Turbo bench (v4 Turbo is the default; v4 and Turbo re-render library accents), voice replies in chat (latency, natural settings, Hebrew open-model test, prices), how to cast accented voices without ears, QC of every take by transcription, and the pacing math that fits a narrated script to a target length.
---
# Voice casting and narrated audio (ElevenLabs v3 / v4)

Before September 2026 the studio could make SFX, music, subtitles and video,
but no speech. It gained speech on the first narrated piece: "The Ladder",
a ~5-minute accented audio drama with a video, adapted from Harari's
*Special Operations in the Age of Chivalry*, ch. 2 (Antioch, 1098). Facts
below were measured on that project (`projects/antioch-1098/`) unless they
name the v4 bench ([[lab-voice]], `projects/lab-voice/`).

## Access: which key can speak with which voice
- **The direct ElevenLabs key is free tier.**
  - **Premade voices:** TTS works with `eleven_v3`, `eleven_v4` and
    `eleven_v4_turbo`.
  - **Library (shared) voices:** refused with 400 "You need to be on the
    creator tier or above to use this voice".
  - **Voice search:** `GET /v1/shared-voices` (search, accent, category)
    still works on this key.
- **Through fal, library voices work.** `fal-ai/elevenlabs/tts/eleven-v3`
  and `fal-ai/elevenlabs/text-to-dialogue/eleven-v3` both cost **$0.10 per
  1000 characters**. Word timestamps are available (`timestamps: true`).
  `fal.py` has no rate for TTS, so the ledger logs `est_usd: null`. Tally
  the cost by hand: characters × $0.0001 (v3), $0.00008 (v4) or $0.00004
  (v4 Turbo). `projects/lab-voice/tools/bench.py` carries these rates.
- **Language support.** These models list Hebrew:
  - `eleven_v3` and `eleven_v3_conversational` (74 languages);
  - `eleven_v4` and `eleven_v4_turbo` (85 listed, "90+" claimed).

  `multilingual_v2`, `flash_v2_5` and `turbo_v2_5` don't.
  - **This supersedes the older rule "use v3 for any Hebrew line".** On
    the bench's Hebrew line, the transcript WER was about the same on all
    three models (≈0.2), and most of the errors were the transcriber
    writing the spelled-out year as varying digits.
- **Cost:** a full 5-minute drama (108 takes of ~800 words, plus re-records
  and auditions) cost about $1.30 in TTS.

## Eleven v4 / v4 Turbo vs v3
Measured in `projects/lab-voice/` ([[lab-voice]]): the Antioch cast via fal,
7 lines × 2 takes × 3 models. Full tables: `outbox/eleven-v4-vs-v3.md`.

**v4 Turbo is the default for all speech** (voice replies and studio TTS),
by the principal's decision after a Hebrew A/B. The settings are
`{stability: 0.35, speed: 1.1}` (Hebrew 1.05). The voice is Will (premade)
until the principal chooses one. v3 is kept only for broad-accent library voices
that Turbo re-renders. Re-audition them before casting.

This replaces the bench verdict (v4 through fal for new work, Turbo for
drafts), because the principal heard Turbo as the best in the Hebrew A/B
(against v4 and Chatterbox).

- **Published scoreboard** (Artificial Analysis, seen 2026-09-28):
  - **Provider-Voice arena Elo:** v4 1319 (#1), then Cartesia Sonic 3.6
    at 1276 ($49/1M chars) and Gemini 3.8 Flash TTS at 1267 ($16.5/1M).
    v3 has 1169 (#18).
  - **Controlled-Voice Elo:** v4 1157 (#2, behind Qwen-Audio-3.1-TTS-Plus
    at 1178), v3 1073.
  - **Pronunciation robustness:** v4 91.7%, v3 85.6%.
  - **ElevenLabs API list price:** v4 $80/1M chars. On our key,
    `/v1/models` shows Turbo at a 0.5× credit multiplier.
- **Direct-API latency** (free key, premade voice, streaming, n=7):
  - time to first byte: v3 0.83 s, v4 0.69 s, Turbo 0.22 s;
  - total for a 70-character line: 3.8 / 1.9 / 0.9 s.
- **Benchmark timing method.** Time generations against fal's synchronous
  `https://fal.run/<endpoint>`. The wall time from `fal.py` is quantised by
  its queue-poll backoff (×1.4, up to 20 s).
- **Access:** fal `elevenlabs/tts/eleven-v4` ($0.08/1k chars) and
  `elevenlabs/tts/eleven-v4-turbo` ($0.04) take library voice IDs. Direct
  free key: v4 works with premade voices only, same as v3. No v4 dialogue
  endpoint on fal yet (v3 `text-to-dialogue` is the only one).
- **Same timestamp schema** as v3 (per-character blocks), so it drops into
  `assemble.py` / `story.json`. New fal inputs: `seed`, `similarity_boost`,
  `output_format` (up to mp3 192k or PCM), IPA in `/slashes/`. 10k chars per
  request (v3: 5k).
- **Better than v3:**
  - generation speed: 2× (v4), 4× (Turbo);
  - mean WER: 5% vs 19%;
  - no hallucinated takes;
  - "Firuz" pronounced right without respelling;
  - `[whispers]` gives a true unvoiced whisper about 10 dB under the plain
    line (v3: −4.6 dB, one take not whispered at all).
- **Worse or different:**
  - **v4 re-renders library accents, unpredictably.** On the blind ear,
    Glaswegian fell from 7/10 to 0–3/10, while Scouse rose from 2/10 to
    7/10. Speaker identity held (same-speaker 0.94 or above).
    Re-audition every accented voice on v4 before casting.
  - It normalizes "3 June" to American "June third". Write British dates
    as words.
  - It reads short character lines 25–45% faster (Bohemond 109 → 145 wpm).
    Narrator pace is unchanged (~152 wpm).
  - Pitch spread on long narration is slightly lower (5.4 vs 6.0
    semitones). The ear preferred v3 on the long paragraph.
- **Turbo ≈ v4 on every proxy** at half the price: mean WER 7.6%, and the
  order-robust ear preference went Turbo 3–0.
  - **Turbo still needs WER QC.** On 1 of 2 takes of a two-sentence
    whisper line it dropped the second sentence (WER 0.63).
  - The principal's ear later made it the default (above).

## Casting accents without ears
- **Search the library by accent word:** scouse, glasgow, paisley,
  mancunian, yorkshire, posh, audiobook. Candidates exist for every region
  asked for.
- **Avoid the most-used "documentary" RP voices** (David, Nathaniel, George).
  They are the recognisable AI narrator sound. Prefer voices with a
  specific character (dry wit, 1960s BBC newsreader) and fewer total uses.
- **Blind accent ID works for casting, but not on short takes.**
  - **Where it worked:** in Antioch casting, an audio LLM (OpenAI
    `gpt-audio`, `ear.py`) named the Glaswegian and Scouse candidates with
    high confidence and without hints.
  - **Where it failed:** in the v4 bench, the same open-ended question on
    ~3 s character lines called the Glaswegian voice "RP/Southern
    English" on all 6 takes, v3 included. The same Scouse voice came back
    as General American, Mancunian or Geordie.
  - **What worked instead:** a targeted question per accent ("rate 0–10
    how strongly this sounds Glaswegian") separated the models cleanly.
    Use the targeted form whenever takes or models are being compared.
- **Absolute LLM quality scores don't discriminate.** Every narrator scored
  8–9.
- **Pairwise "which is better" has a strong first-position bias.** Run
  every pair in both orders and count only order-robust wins. The narrator
  was chosen that way (Grant, "BBC 1965").
- **Objective voice stats break ties** (numpy YIN; librosa is not
  installed):
  - words per minute: a 107 wpm voice inflates the runtime;
  - F0 spread in semitones: expressiveness;
  - the dB drop on a whispered line: most voices barely whisper;
  - F0 separation between characters who share scenes.
- **Final judgement stays human.** On music, the principal's ear overruled
  measurements that scored two takes the same ([[music-tools]]). Treat all
  of this as shortlisting.

## Recording and QC
- **Record 2 takes of every line,** then transcribe every take
  (`gpt-4o-transcribe`) and compute WER against the script. This catches:
  - hallucinated takes: "Psst! Are ye there?" came back as "Alifer";
  - short lines that turned into gibberish;
  - mispronounced names: *Firuz* was heard as "Farouz" or "Theroux".
- **Fix names with a phonetic respelling in the TTS text** ("Fee-rooz"),
  then re-check the transcript.
- **Ignore WER noise** from digits vs words and from exotic proper names the
  transcriber can't spell.
- **Re-record, don't splice, when a line is edited mid-sentence.** A cut at
  a comma keeps the wrong intonation. Three edited narrator lines were
  regenerated whole.
- **v3 tags** (`[whispers]`, `[sighs]`) work but should be used sparingly.

## Fitting a script to a length
- **Measured effective rate: ~119 wpm** including designed dramatic gaps.
  788 words assembled to 6:38 against a 5:00 brief.
- **Budget ~600 words for 5 minutes** of narrated drama with pauses.
- **Trimming order that worked:**
  1. Cut whole sentences that repeat a beat.
  2. Tighten the designed gaps.
  3. Speed only the narrator by 1.1× with rubberband.

  Result: 5:35 without audible artefacts.
- **Assemble on a timeline file** (`edl.json`: picks, gaps, per-role tempo)
  that emits the voice track plus a `story.json` of per-line and per-word
  times. That JSON becomes the spine for music cues, SFX and picture, like
  `song.json` for a music video.

## Voice replies in chat
- **Job:** turn an agent's final text answer into an audio file and send it.
  Skill `voice-reply` wraps it as the runline action `voice.say`; the agent
  sends the returned MP3 with `send_file` ([[lab-voice]]).
- **Scripts:** `projects/lab-voice/tools/voice_reply.py` (one streaming call)
  and `voice_reply_par.py` (sentence chunks in parallel, `previous_text` /
  `next_text` for prosody, ffmpeg concat with stream copy).
- **Direct free key, premade voice Roger, ~500 chars = ~33 s of speech:**
  - v4 Turbo streaming: first audio 0.35-0.5 s (one 1.4 s outlier), full file 5.1-6.3 s;
  - v4 streaming: first audio 0.7-0.9 s, full file 7.5-8.2 s;
  - v4 Turbo, parallel chunks: full file 3.6-4.1 s (2-4 workers; the free key queues them).
- **Transient 401 under parallel load:** two v4 runs with 4 workers failed with
  401. The same calls passed one minute later. Use 2 workers and retry.
- **WhatsApp delivery:** send MP3 (`audio/mpeg` plays inline as an audio
  bubble). `.ogg` becomes a file card on the Vex Baileys adapter. It is an
  audio bubble, not a push-to-talk voice note.
- **Fastest design:** TTS each sentence while the answer is still being written.
  The file is then ready ~1 s after the last sentence.
- **Natural delivery without tags (v4, direct API):** `voice_settings`
  `{stability: 0.35, speed: 1.1}` and a conversational premade voice
  (Will, Chris or Eric). Result: ~167-171 wpm, WER 0 on all three.
  - fal's v4 / v4 Turbo endpoints have `stability` but no `speed` or `style`.
    Use the direct API when the pace must change.
  - The blind pairwise ear picked the second clip in all 6 orders. It cannot
    choose between these voices. The voice is the principal's call.
  - Most of the human feel comes from the voice and from a script written
    for the ear: short sentences, no lists, no links.
- **Hebrew, open model vs ElevenLabs (one take each):**
  - ElevenLabs v4 (Will, `language_code: he`): CER 0.8%, F0 spread 4.8 st.
  - Chatterbox Multilingual via fal ($0.025/1k chars, 300-char cap):
    CER 26%, flat (2.8 st), and it dropped the last sentence.
  - The principal's ear: Chatterbox "reads each Hebrew word from its end to its
    start". This looks like an RTL defect, not only an accent.
  - v4 Turbo, same line (Will, stability 0.35, speed 1.05): CER 0.0%,
    F0 spread 5.1 st, 2.1 s to generate. The principal chose Turbo.
  - Open Hebrew TTS is not ready for team replies. Chatterbox is MIT;
    OmniVoice (600+ languages) is CC-BY-NC, so no commercial use.
- **ElevenLabs API pricing (seen 2026-10-06):** v4 $0.08/1k chars, v4 Turbo
  $0.04/1k. Plans: Starter $6, Creator $22,
  Pro $99, Scale $299. Each plan includes its price in characters at these
  rates. The free plan includes 10k v4 or 20k Turbo characters a month.
  When the studio's direct key had used its 10,000 free credits, every direct call
  (sound generation included) returned HTTP 401 `quota_exceeded`; fal still worked.

Related: [[music-tools]] (music beds under a voice, ducking), [[tool-selection]], [[gossip-goblin-trailer-case]] (trailer VO pacing and a speech-to-speech route).
