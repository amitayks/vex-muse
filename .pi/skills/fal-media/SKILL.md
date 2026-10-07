---
name: fal-media
description: Call fal.ai generative models (image, image-edit, video, lip-sync, background removal, upscaling, music, stems, SFX) through Muse's stdlib client - queue submit/poll/download, local-file upload, schema lookup, and the per-project cost ledger. Use for any paid generation (Seedance 2.5, Nano Banana Pro, GPT Image 2, Seedream, MiniMax H3 lip-sync, sync-lipsync, Bria matting, ElevenLabs Music, Lyria, MiniMax Music, Stable Audio, Demucs), to check a model's current input fields, or to account for spend.
license: MIT
compatibility: Env FAL_KEY; python3 (stdlib). Network to queue.fal.run and rest.alpha.fal.ai.
metadata:
  author: muse
  version: "1.3.2"
---

# fal-media — every paid pixel goes through one door

Client: `scripts/fal.py` (stdlib; run with `python3`). Never curl fal by hand —
the script is what writes the ledger.

## Calls
- Discover inputs first: `fal.py schema <endpoint>` (fal's live OpenAPI; field
  names move between versions — never guess).
- Run: `fal.py run <endpoint> in.json --out <dir> --ledger projects/<slug>/ledger.jsonl --tag <shot-or-asset-id>`.
  Local files inside `in.json` as `"@file:/abs/path"` are uploaded
  automatically. Outputs (every media URL) download into `--out`.
- Long jobs: run inside a background bash execution; don't block the turn.
  `--no-wait` returns ids; `status` / `result` resume.
- Upload once, reuse the URL: `fal.py upload <file>` for assets referenced by
  many calls (character sheets, set plates, audio slices). Keep the URL in the
  project's `assets.json`.

## Model menu (verify with `schema` + model page before a production run)
| Job | Endpoint | Notes |
|---|---|---|
| Character / set / style frames | `fal-ai/nano-banana-pro`, `/edit` | best identity lock across edits; multi-image reference |
| Alt look, typography-heavy frames | `openai/gpt-image-2`, `/edit` | strong text rendering, graphic design |
| Plates whose placement/scale must be exact (box layout) | `blackforestlabs/flux-3/text-to-image`, `/edit-image` | $0.024 per output MP; ≤10 `image_urls`, each ≤4 MP; caption with `<id>` tags + JSON rows inside `prompt`; edits re-tint and resize the frame — not for start/end pairs |
| Base plates with performance + audio timing | `bytedance/seedance-2.5/reference-to-video` | ≤30 images, ≤10 audio (1.8–30.2 s each), ≤10 videos; cite as @Image1/@Audio1/@Video1; `draft:true` → 480p + `draft_id` |
| Animate a still | `bytedance/seedance-2.5/image-to-video` | start + optional `end_image_url` for controlled transitions |
| Finish a draft at 1080p | `bytedance/seedance-2.5/draft/complete` | same account, within 7 days |
| Lip-sync repair on a still | `minimax/h3-max/lip-sync/image-to-video` | ≤14.8 s audio per call |
| Lip-sync repair on a clip | `fal-ai/sync-lipsync/v3` | video + audio; `sync_mode` |
| Mattes for rotoscope | `bria/video/background-removal/v3`, `fal-ai/bria/background/remove` | alpha per frame; isolated objects only (a busy scene comes back ~all foreground) |
| Text-prompted mask (subject inside a scene) | `fal-ai/sam-3/image` (`prompt`, `apply_mask:false`) | $0.005; binary mask PNG; used by `collage-motion/scripts/cutout.py --matte sam:<prompt>` |
| Music (songs, beats, cues) | `elevenlabs/music/v2.5`, `google/lyria-3.5`, `minimax/music-3`, `fal-ai/stable-audio-3/medium/*`, … | choose and call through `music-gen` (`musicgen.py`), not by hand |
| Stems | `fal-ai/demucs` (`htdemucs_ft`, 4 stems) | $0.0007 per input second; `song-map` Modal route is ~10× cheaper |
| Isolate any sound by text | `fal-ai/sam-audio/separate` | $0.05 per 30 s |
| SFX / voice isolation | `fal-ai/elevenlabs/sound-effects/v2`, `fal-ai/elevenlabs/audio-isolation` | $0.002/s, $0.10/min |
| Speech (TTS, library voice ids) | `fal-ai/elevenlabs/tts/eleven-v4-turbo` (default), `/eleven-v4`, `/eleven-v3` | $0.04 / $0.08 / $0.10 per 1000 input characters (`kchar` rate) |

Rates live in `RATES` inside the script (per second / image / call /
minute / started block; audio lengths are probed from the downloaded
files). Live prices: `GET https://api.fal.ai/v1/models/pricing?endpoint_id=<id>`
(auth `Key $FAL_KEY`); the catalog: `https://fal.ai/api/models?keywords=<word>`.
When a price changes, update `RATES` and add a LEARNINGS line.

## Money law
- Every call carries `--ledger` and `--tag`. `jq`-free total:
  `python3 -c "import json,sys;print(sum((json.loads(l).get('est_usd') or 0) for l in open(sys.argv[1])))" ledger.jsonl`
- Draft (480p / `draft:true`) → verify → complete. Never a 1080p first take.
- Stay under the brief's cap; report spend at every gate.

## Failure handling
- HTTP 4xx = my input is wrong: read the message, re-check `schema`.
- `FAILED` with content-policy text: rewrite the prompt (no real public
  figures' likeness, no brand logos as the subject), don't retry blindly.
- 429/5xx are retried by the script; persistent → back off and report.

## Acceptance
A generation step is done when the output file exists locally, opens
(`ffprobe` / image read), matches the requested duration/aspect, its ledger
line carries a cost estimate, and I have LOOKED at it (frame or contact
sheet) against the shot's intent.
