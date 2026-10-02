---
name: music-gen
description: Generate original music for a video - beats and loops at an exact BPM and length, cinematic cues and scores with hits on picture, full songs with sung lyrics Muse writes, and "something in the style/energy of <reference>" - by choosing the right generator per job (ElevenLabs Music v2.5 composition plans, Google Lyria 3.5, MiniMax Music 3, Stable Audio 3 incl. inpaint/extend/audio-to-audio, ACE-Step 1.5 open model on Modal (default singer), js-scoring for sample-exact hits), writing one brief JSON that every provider receives natively, drafting cheap takes, scoring them objectively (tempo, duration, key, hits, lyric intelligibility, style distance), and combining generate -> stems -> grid edit -> designed hits -> master. Use when a video has no song, needs a score, bed, sting or custom song, or when the principal asks for music "like X".
license: MIT
compatibility: FAL_KEY (fal providers, ledgered by fal-media); MODAL_TOKEN_ID/SECRET (ACE-Step 1.5, stems); OPENAI_API_KEY (lyric check); tools/env.sh ($PY, ffmpeg).
metadata:
  author: muse
  version: "1.1.0"
---

# music-gen — the song I need, made to measure

Scripts (`$PY`): `musicgen.py` (brief → provider input → file + ledger),
`musiceval.py` (objective score + table), `sheet.py` (spectrogram sheet),
`modal_acestep.py` (ACE-Step 1.5 on an L4), `modal_yue2.py` (YuE2 on an L40S). Brief format:
[references/briefs.md](references/briefs.md). Measured comparison and
prices: [references/generators.md](references/generators.md).

## Pick the generator by the job
| Job | Default | Why (lab, 2026-09-26) | Also good |
|---|---|---|---|
| Beat / loop / bed at exact BPM + length | **ElevenLabs v2.5** with a composition plan | 30.07 s, 128.0 BPM, full arrangement; $0.60 per started minute | Stable Audio 3 ($0.04, exact length + tempo); ACE-Step 1.5 (≈$0.01, obeys BPM + key + length as metadata, 1 of 2 takes ended early) |
| Score / cue with hits on picture | **generated bed at a BPM that puts the hits on bar lines + hits designed in `js-scoring`/SFX** | no model placed a real hit within 100 ms of 8/16/24 s (40–650 ms, mostly no level jump); code hit all three within 5 ms at +8 dB | ElevenLabs plan chunks give section changes near (not on) boundaries — fix with `track-edit` |
| Sung song with my lyrics | **ACE-Step 1.5** (Modal) — generate 3 takes, keep the one that passes duration + WER | the principal's ear (2026-09-26): cleaner, more human voice, natural across high and low notes vs ElevenLabs; WER 0.02, obeys BPM/key/length, ~$0.02/take; 2 of 5 takes ended early → always ≥3 takes and auto-reject short ones | ElevenLabs v2.5 plan when exact structure matters more than voice (WER 0.00, exact 48.0 s); MiniMax 2.6 / Lyria 3 Pro / Lyria 3.5 WER 0.00 with length/tempo drift; YuE2 WER 0.13 |
| Full-length song (2–4 min) | **Lyria 3.5** ($0.10) with `[m:ss - m:ss]` sections | cheapest full song, returns timed lyrics; ignores exact length (asked 30 → 62 s) | ElevenLabs plan up to 10 min, exact |
| "In the style of <song>" | **song-map the reference → describe it in words (BPM, key, instruments, energy) → Stable Audio 3 (instrumental) or ElevenLabs (with vocals)** | both hit 171 BPM and the key family; SA3 kept the drive for all 30 s, ElevenLabs built and faded. ElevenLabs rejects a commercial song as `audio_reference` (copyright screen, 422, no charge) but accepts our own audio | ACE-Step 1.5 with the audio reference; Stable Audio 3 audio-to-audio (closest texture — a remix) |
| Extend / fix a section | Stable Audio 3 outpaint / inpaint ($0.045), ACE-Step repaint | seam-free edits of generated audio | `track-edit loop` for pure repetition |
| Zero-cost, exact, simple | `js-scoring` | sample-accurate, deterministic, renders in seconds | — |

Avoid for timed work: MiniMax Music 3 instrumentals (stopped at 17 s of 30,
136 BPM for 128), Sonilo (ignored tempo), ACE-Step v1 on fal (smeared,
WER 0.33). Suno and Udio have no public API; don't use unofficial wrappers.

## Workflow
1. **Brief** → `projects/<slug>/audio/briefs/<id>.json`: style words, BPM
   chosen so picture hits fall on bar lines, key, exact duration (a whole
   number of bars), sections as cue points, lyrics I write (never someone
   else's lyrics, never an artist's name — Lyria/ElevenLabs block both).
2. **Draft**: `musicgen.py gen <provider> brief.json --out audio/gen/<id> --ledger projects/<slug>/ledger.jsonl --takes 2`
   on the default + one alternative. `musicgen.py input` first costs $0.
3. **Score**: `musiceval.py measure <take> brief.json --out … --spectro …`
   then `musiceval.py table`; sheet the spectrograms (`sheet.py`) and look:
   early endings, dropouts, smeared transients, a flat middle.
   Lyrics: judge WER on the **vocal stem** (`song-map` modal stems), not the
   mix — whisper drops whole verses on full mixes.
4. **Combine**: pick the take → stems (`song-map/scripts/modal_audio.py
   ::stems`, $0.01) if parts must move → `track-edit` (fit on bars, loop,
   re-arrange, remove vocals) → designed hits (`js-scoring` / SFX) on the
   exact frames → `track-edit master` (-14 LUFS).
5. Then `song-map` the final master; from here it is sacred.

## Rules
- Spend: draft on cheap providers, finish on the default; ElevenLabs bills
  per started minute — ask for ≤60 s and cut. Every call goes through
  `musicgen.py` (ledger). Report spend at the gate.
- Rights: ElevenLabs Music and Stable Audio 3 are trained/cleared for
  commercial use; Lyria carries a SynthID watermark; ACE-Step 1.5 is MIT
  (outputs mine). A "style of" track must not copy the melody: check
  `style.chroma_cos` and listen-by-proxy for a copied hook.

## Acceptance
A take is accepted when `musiceval` shows: duration within 0.5 s of the
brief (or fixed by `track-edit`), tempo within 1 % (octave-aware), key same
or relative, grid drift < 15 ms, true peak ≤ -1 dBTP after master, no
section of silence it didn't ask for, sung lyrics WER ≤ 0.15 on the vocal
stem, and every picture hit within one frame (designed hits) — and the
spectrogram sheet was looked at. Log the choice + numbers in the project.
