---
name: video-critic
description: Let a multimodal model WATCH AND LISTEN to a whole video and answer as a film editor, DP and re-recording mixer - Gemini 3.1 Pro through fal's OpenRouter video route (FAL_KEY, no Google key) - to study a reference shot by shot (camera, pace, dialogue coverage, sound layers), to critique our own cut or a single plate take (acting, lip-sync, AI tells, pace, mix), or to pick the best of several takes. Use in reference study (phase 2), on every plate take before it is accepted, on every rendered cut before review, and whenever a judgement needs eyes and ears together rather than frame sheets alone.
license: MIT
compatibility: FAL_KEY; tools/env.sh (ffmpeg, $PY).
metadata:
  author: muse
  version: "1.0.0"
---

# video-critic — eyes and ears on the whole clip

Frame sheets see; they don't hear, and they miss motion quality. A model that takes the video WITH
its sound judges acting, lip-sync, pace and mix the way a viewer meets them.

## Call
`$PY .pi/skills/video-critic/scripts/watch.py <video> <prompt.md> <out.md> [--model M] [--max-height 540] [--public] [--ledger projects/<slug>/ledger.jsonl]`
- Default model `google/gemini-3.1-pro-preview` (reasoning is mandatory on this route; the script sends it).
  Cheaper second opinion: `google/gemini-3.8-flash`.
- Our own work goes **inline as a data URI** (default) — never a public CDN URL. `--public` (fal upload)
  only for third-party public clips too large to inline.
- The script re-encodes to ≤ `--max-height` px, ~1.2 Mbps with AAC audio. 30 s at 360p ≈ $0.06; a 4 min
  reference at 480p ≈ $0.3–0.6. Cost is logged from the route's `usage.cost`.

## Prompts (references/)
- `prompt-study-reference.md` — breakdown of a reference: source, shot list with size/position/move/speed,
  pace rule, multi-person dialogue coverage, sound layers, continuity, top techniques, what an AI
  pipeline would get wrong.
- `prompt-critic-cut.md` — strict critique of our cut: medium-speed moments, theatre vs. talk, lip-sync,
  mix, AI tells, top 5 fixes.
- Take selection: send each take and ask the same 3–5 scored questions (0–10) plus the one defect;
  compare scores across takes, never trust one absolute score.
Every prompt demands timecodes (mm:ss.s) for every claim.

## Trust rules
- Timecodes drift ~0.5–1 s and short names get misheard (it heard "Maeve" as "Moira"). Verify any claim
  you act on with a frame strip or the transcript before spending money on a fix.
- It samples video sparsely (~100 tokens/s at 360p). Sub-second events (a 3-frame grab, a flash) can be
  missed: pair it with `framestudy.py` for cut and motion numbers.
- It is a critic, not the director: its fix list is input. the principal's eye decides taste.

## Acceptance
The out file exists, has timecoded findings for every section asked, the cost is in the ledger, and each
finding you act on was confirmed on a frame strip, a transcript or a measurement.
