# Generators — behaviour, prices, how to re-check (seen 2026-09-26, half-life 60 days)

Measured tables: `projects/lab-music/review/results.md`; the landscape and
analysis facts: `knowledge/references/music-tools.md`. Re-check before a
production run when this page is older than its half-life:

- Catalog: `curl -s "https://fal.ai/api/models?keywords=music&limit=100"` (also `song`, `audio-to-audio`).
- Prices: `GET https://api.fal.ai/v1/models/pricing?endpoint_id=<id>` with `Authorization: Key $FAL_KEY` → update `fal-media/scripts/fal.py` RATES.
- Inputs: `python3 .pi/skills/fal-media/scripts/fal.py schema <endpoint>`.
- Outside fal: Gemini API music page (Lyria 3.5 / Lyria RealTime, needs GEMINI_API_KEY), ElevenLabs music docs (direct API = paid plan), ACE-Step GitHub (new open versions), Suno/Udio (no public API as of this date).

## Behaviour per provider (lab evidence)
| Provider | Honors length | Honors BPM | Key | Vocals / lyrics | Structure control | Notes |
|---|---|---|---|---|---|---|
| ElevenLabs v2.5 (`eleven`) | yes (±0.1 s) | yes | 3/4 in family | excellent (vocal WER 0.00) | composition plan: chunk per section, exact ms | $0.60 per STARTED minute; 8–14 s; commercial-cleared; audio reference refuses copyrighted songs; seed only with plan |
| Lyria 3.5 (`lyria35`) | no (30 → 62 s) | yes | 0/4 | excellent (0.00), returns timed lyrics | `[m:ss - m:ss]` lines steer order, not exact time | $0.10; best price per full song; SynthID; no artist names |
| Lyria 3 / 3 Pro | ~30 s clip / ~46 s | yes | often off | excellent | prompt only | $0.04 / $0.08 |
| MiniMax Music 3 (`minimax3`) | upper bound; stopped at 17 s | no (136 for 128, 120 for 100) | off | excellent (0.00) | caption + tagged lyrics | lyrics required; slow (34–122 s) |
| MiniMax 2.6 (`minimax26`) | chooses (55 s) | yes | yes | excellent (0.00) | tagged lyrics | $0.15 |
| Stable Audio 3 medium (`sa3`) | exact | yes | 2/3 in family | none | prompt only; bars start at t = 0 so downbeats land on multiples of the bar | $0.04; inpaint/outpaint/a2a siblings; licensed data |
| Stable Audio 2.5 (`sa25`) | exact | yes | ok | none | prompt | $0.20 — no reason to pick over SA3 |
| Sonilo v1.1 | exact | no | off | none | prompt | $0.0025/s |
| ACE-Step 1.5 (`acestep15`, Modal) | exact file length; music may end early (2 of 5 runs) | yes | 5/5 (key is metadata) | very good (0.02) | caption + tagged lyrics + BPM/key/time-sig metadata; reference audio; repaint/cover | ≈ $0.02/call on L4; MIT, open weights; LoRA possible |
| YuE2 3B (`yue2`, Modal L40S) | no (lyrics set the length: 48 s brief → 60 s) | yes (100.4) | chooses its own (planned E major for "C major"); force with an `abc` score | good (0.13 — misheard "pencil", "ink and neon") | lyrics + style; editable ABC score; covers | ≈ $0.04/song, 30 s generation; weights free for personal creators |
| ACE-Step v1 (`acestep`, fal) | yes | no | off | poor (0.33) | tags + lyrics | cheapest; smeared — drafts only |
| js-scoring | exact | exact | exact | none | code: every event at a sample | $0 |

Key "in family" = same, relative or parallel key by Essentia EDMA; the detector itself misreads
our code-made cues by a relative/parallel step, so treat one-off misses as noise.

## Style-of-a-reference, ranked
1. song-map the reference → words (BPM, key, instruments, energy curve,
   production) → ElevenLabs or Stable Audio 3 (text). Legal-safe and matched
   tempo + key family in the lab.
2. ACE-Step 1.5 with `reference_audio` (open model, no copyright screen) —
   matched tempo/tonic; check the ending.
3. Stable Audio 3 audio-to-audio from the reference (init 0.75): closest
   texture — it is a transformation of the source, treat as a remix.
Never: artist names in prompts, copyrighted lyrics, a commercial song as an
ElevenLabs audio reference (refused).
