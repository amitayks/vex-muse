---
kind: project
seen: 2026-10-10
tags: [lab, gaussian-splatting, marble, gsplat, modal, local-muse, brush, spark]
summary: "lab-splats: the studio's gaussian-splat pipeline, built in one night - captured scenes trained with gsplat on Modal, full worlds from World Labs Marble, TripoSplat objects, a lens renderer with dust-wave transitions, and a $0 Mac station (Brush, Spark viewer, Blender camera bridge). About $13.1 of $40."
---
# lab-splats: gaussian splats, the real deal

**Brief.** the principal: "I want to start creating with gaussian splats. The real deal like the one used in rendering full worlds with realism presicion. We have the local agent that can use the Mac and all ours cloud tools. Let's create new projects for that. Give me fantastic results." Muse opened three projects:
- this lab, for the pipeline;
- [[splat-world-01]], the showcase film ONE DAY;
- `splat-capture-01`, a real place of his, which waits for his phone video.

Lab cap: $40. Method, measurements and gotchas are in [[splat-field-notes]].

**What worked**
- **Modal splat farm** (`projects/lab-splats/scripts/modal_splat.py`):
  - dataset fetch, gsplat 1.5.3 MCMC training on an L40S, and COLMAP poses from a video or an image folder;
  - `render_shot`, a film lens (stratified motion blur, thin-lens depth of field, pixel-jitter antialiasing) with per-splat effects (dissolve, assemble, morph, fade), layers and a planning map.
- **Rendering is cheap and exact:**
  - 0.015 s/frame for 4M splats at 540p;
  - 0.11–0.13 s/frame at 1080p with 8 lens samples;
  - a 46 s 1080p film renders in 35 s on 12 containers for $0.08.
- **Marble 1.1 Plus worlds** from the studio's own Nano Banana stills hold real moves: a 6 m climb in the alley, a 21 m float over the crater, 15 m on the roof, and a full 360° everywhere. The client `marble.py` generates worlds, resumes a paid operation and logs cost.
- **The world-swap wave:** both worlds change far-to-near at the same time, rank-ordered. The far part of the frame already shows the next world while the near part still shows the old one, and the dust glows in its own colour.
- **Captures (holdout PSNR):**

  | Scene | PSNR | Splats | Time | Cost |
  |---|---|---|---|---|
  | garden, factor 2 | 26.71 dB | 3.0M | 43 min | $1.41 |
  | indoor room | 32.78 dB | | 125 min | $4.06 |

  COLMAP registered 292/292 bonsai frames for $0.08.
- **Mac station by Local Muse ($0)** ([[local-muse-mac-helper]]):
  - Brush trains the garden scene to PSNR 27.70 in 35 min;
  - a Spark 2.3.1 viewer flies 2.19M splats at 43–58 fps in 1080p;
  - a Blender 5.2 camera exports to the Modal renderer with a proven OpenCV convention (0.00016 px).

**What didn't**
- **Berlin apartment** (Zip-NeRF, undistorted) failed at PSNR 8.6 with the plain COLMAP parser. The cause is not verified.
- **Modal image build** failed twice: `bdist_wheel`, then clang named as the compiler by the Python build. Both are fixed in the script.
- **First transitions** read as noise: random turbulence, near-first order, confetti motes, black gaps.
- **Marble API** field names differ from the docs' quickstart (`media_asset_id`, `world_id`).
- **The direct ElevenLabs key** is out of quota, so SFX go through fal.

The fixes are in [[splat-field-notes]].

**Spend.** About $13.1 of the $40 cap (`projects/lab-splats/ledger.jsonl`):
- Modal: about $12.9, for four 30k-step trainings at $1.4–4.1 each (one failed), COLMAP and the lab renders;
- fal: $0.20.

The showcase spend is in [[splat-world-01]].

**Final.** Lab reel: `projects/lab-splats/renders/lab_splats_reel_v1.mp4` (35 s, 1080p, 37 MB). Its phone copy went on WhatsApp. The master was over the WhatsApp cap, so `send_file` refused it there. The reel uses research datasets and World Labs demo worlds: it is for the lab only and must not be posted. The principal's verdict on the reel and the film: "That are fantastic results."

## How the principal works with this
- He gives open, ambitious briefs ("the real deal", "fantastic results") and expects Muse to choose the projects, routes and caps.
- He asks next whether the studio can replace generated video with its own scenes; see [[splat-world-01]] (How the principal works).
