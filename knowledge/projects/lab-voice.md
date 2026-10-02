---
kind: project
seen: 2026-09-28
tags: [lab, tts, elevenlabs, benchmark]
---
# lab-voice — Eleven v4 / v4 Turbo vs our v3 (Sep 2026)

**Brief.** On 2026-09-28 (22:47) the principal sent ElevenLabs' Eleven v4 launch
post (@tadaspetra) with "do compare from this to what we are using. All
stat". The comparison had two halves:
- **Published stats:** the Artificial Analysis arena, pronunciation and
  price figures, plus `/v1/models` and fal's pricing API.
- **Our own bench:** our real voice jobs run through our real route. That
  meant the Antioch cast (library voices) through fal, 7 lines × 2 takes ×
  3 models = 42 takes. The lines covered long narration, names, numbers
  and dates, a Scouse line, a Glaswegian line, a `[whispers]` line and
  Hebrew.

No cap was given, so the default $150 applied.

**What worked**
- **v4 is a drop-in on our pipeline.** It uses the same fal call shape, the
  library voice IDs work, and it returns the same per-character timestamp
  blocks. The findings are in [[voice-casting]].
- **The QC stack from `antioch-1098` could be reused for a model bench:**
  - WER against the script (`gpt-4o-transcribe`);
  - voice stats (wpm, F0 spread, whisper dB drop);
  - blind proxy ear (`gpt-audio`): accent, same-speaker, and order-robust
    pairwise preference.

  It now lives in `projects/lab-voice/tools/`:
  - `bench.py gen|qc`: generates the takes and scores them;
  - `ears.py`: runs the blind-ear passes.

  Any future TTS model can be benched by changing the `MODELS` table.
- **Timing against fal's synchronous endpoint** (`https://fal.run/<endpoint>`)
  gave clean generation times. Wall times from `fal.py`'s queue polling are
  quantised by its backoff.
- **A level-matched A/B file let the principal's ear decide.** Each line plays in
  the order v3 → v4 → Turbo, loudnormed to −20 LUFS; the whisper line is
  left at its raw level so its depth still shows. The file is 3:36.

**What didn't**
- **Open-ended blind accent ID failed on ~3 s lines.** It called the
  Glaswegian voice "RP" on every take, and the same Scouse voice came back
  as American, Mancunian or Geordie. A targeted 0–10 question per accent
  was needed (see [[voice-casting]]).
- **The proxy ear's preference flipped with play order** on 2 of 5 v3|v4
  pairs. Only the order-robust wins were counted.
- **QC crashed on system `python3` (no numpy).** Analysis scripts run with
  `$PY` after `source tools/env.sh`; ffprobe is also on PATH only after
  sourcing it.
- **A canvas pane could not be opened.** The canvas exists only while
  The principal has the web chat open. `send_file` is the reliable delivery.

**Spend.** $0.48 of the $150 default cap, all TTS: 6,498 characters in
total, split as v3 $0.22, v4 $0.17, Turbo $0.09. The transcription and
`gpt-audio` ear calls are not ledgered (cents). Ledger:
`projects/lab-voice/ledger.jsonl`.

**Final.** Delivered to the principal's web chat on 2026-09-28 (~22:58):
- `outbox/eleven-v4-vs-v3.md`: the full report, published and measured;
- `outbox/eleven-v3-v4-bench.png`: a six-panel chart;
- `outbox/eleven-v3-v4-turbo-AB.mp3`: the A/B listening file.

The takes are in `projects/lab-voice/takes/`. The measurements are in
`projects/lab-voice/review/` (`qc.json`, `ears.json`, `ears2.json`,
`direct_latency*.txt`). The lab is filed on spine matter `muse-studio`.

The verdict:
- v4 through fal becomes the default;
- broad-accent voices stay on v3 until each one is re-auditioned on v4;
- Turbo is for drafts and auditions;
- The principal's ear on the A/B file picks the model for finals.

The principal's A/B listen was still pending at the end of the session.

## How the principal works with this
- **A launch-tweet link with "compare to what we are using, all stat" asks
  for two things.** He wants the published numbers, and he wants a bench
  on our own jobs and route. Vendor claims alone don't answer it.
- **After a long report he asked "Bottom line?"** Every comparison should
  lead with a three-sentence verdict: what to switch to, the catch, and
  what is cheaper for drafts. Tables and caveats come after it.
