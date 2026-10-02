---
kind: technique
tags: [speech, tts, casting, elevenlabs]
audience: studio-internal
half_life: 90
rights: safe
seen: 2026-09-28
summary: Speech is the studio's newest capability. Covers access to ElevenLabs v3/v4 voices (direct key vs fal), the v3 vs v4 vs v4 Turbo bench (v4 default, but it re-renders library accents), how to cast accented voices without ears, QC of every take by transcription, and the pacing math that fits a narrated script to a target length.
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

## Eleven v4 / v4 Turbo vs v3 (bench 2026-09-28)
Measured in `projects/lab-voice/` ([[lab-voice]]): the Antioch cast via fal,
7 lines × 2 takes × 3 models. Full tables: `outbox/eleven-v4-vs-v3.md`.

**Status (2026-09-28).** These are Muse's defaults:
- v4 through fal for new work;
- v3 kept for broad-accent voices until each one is re-auditioned;
- Turbo for drafts.

The principal's verdict on the A/B file (`outbox/eleven-v3-v4-turbo-AB.mp3`) was
still pending.

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
  - Use it for drafts and auditions. Finals are decided by the principal's ear.

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

Related: [[music-tools]] (music beds under a voice, ducking), [[tool-selection]].
