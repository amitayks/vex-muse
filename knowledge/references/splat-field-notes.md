---
kind: technique
tags: [gaussian-splatting, gsplat, marble, world-labs, triposplat, modal, rendering, lens, transitions]
audience: all
half_life: 60
rights: safe
seen: 2026-10-11
summary: "Gaussian splats in the studio: three routes to a world (capture → gsplat on Modal, World Labs Marble, TripoSplat objects), one lens renderer on Modal (motion blur, thin-lens DoF, effects), the dust-wave transition between worlds, measured speeds, costs and gotchas."
---
# Splat field notes — worlds, renderer, transitions

First built in [[lab-splats]] for the showcase film [[splat-world-01]]. Code: `projects/lab-splats/scripts/modal_splat.py` (Modal farm), `marble.py` (World API client), `projects/lab-splats/scripts/build_chain.py` (worlds joined into one camera move).

## Why splats fit the studio
A splat world is a static, photoreal 3D asset; the camera in it is exact code. It obeys the Blender-first rule ([[tool-selection]]): no model invents the motion. One world, many lenses: the 16:9 and 9:16 cuts are two renders, not a crop.

## Three routes to a world
| Route | Tool | Out | Cost | Notes |
|---|---|---|---|---|
| Generate a full world | **World Labs Marble** (`marble-1.1` / `marble-1.1-plus`), World API, key `WLT_API_KEY` | SPZ 100k/500k/full (~2M), free PLY export (~2M, SH degree 0, 68 B/splat → 136 MB), collider GLB, 2560×1280 pano | 1,580 credits = $1.26 per world from an image (1,500 world + 80 pano); Plus 1,580–3,080 credits; draft 230 credits | API credits are separate from Marble-app credits; $5 minimum; overage is billed after the month |
| Capture a real place | photos/video → COLMAP poses → **gsplat 1.5.3 MCMC** (`--antialiased`) on a Modal L40S | PLY with SH degree 3 | see Speeds | Mip-NeRF 360 / Zip-NeRF captures are research data: lab only, never posted |
| One object | **TripoSplat** (`tripo3d/triposplat`, fal) | PLY, 262k splats, SH 0, unit box, OpenCV axes (y down) | $0.05, ~110 s | full 3D from one 2K image; colours come out brighter and flatter than the source: grade it into the world |

## Marble from the studio's own stills (`marble.py`)
- **Field names:** `prepare_upload` returns `media_asset.media_asset_id` (not `id`); a finished operation's `response` carries `world_id` (also in `metadata.world_id`). If the client dies after a paid generation, `marble.py resume --op <operation_id>` finishes it without a second charge.
- **Cost per world (Marble 1.1 Plus, 2752×1536 PNG input):** alley 1,580 credits; crater 3,080 credits (the full variable charge, a huge world). The base 1,580 is taken at the start, so the balance drops before the world is done. A world started on a low balance overruns it: three Plus worlds (1,580 + 3,080 + 3,080) took 7,740 credits from a 7,000 balance, and the extra 740 became overage billed at the end of the month.
- **Time:** ~7 min per world; a large one (the roof, 3,080 credits) took over 18 min.
- **Scale:** `metric_scale_factor` alley 1.50 m/unit, crater 3.66 m/unit; `ground_plane_offset` 1.18 / 1.71 m. Raw ground height = offset ÷ scale (alley 0.79 units below the camera).
- **Travel holds far better than on the public examples:** the Plus alley held a 4.3-unit (6 m) climb up the steps; the crater held a 5.8-unit (21 m) float off the rim and over the crater. Raise the camera with the ground (steps), and lift it (y negative) when it leaves the rim.
- Downloads per world: pano 15 MB, full SPZ 29 MB, 500k SPZ 7.6 MB, collider GLB 1.5 MB; the free PLY export is 108 MB (alley, 1.92M splats) or 242 MB (crater, 4.32M) and goes straight into the Modal volume.

## Capture: video → poses (`modal_splat.py::capture`)
- Debian COLMAP 3.8 on a 16-CPU Modal container (`QT_QPA_PLATFORM=offscreen`, no GPU SIFT): ffmpeg frames (`--fps 3`, ≤ `--max-side` px) → `feature_extractor` (OPENCV camera, one camera) → `sequential_matcher` (overlap 20) → `mapper`; the biggest model becomes `sparse/0` for gsplat.
- Verified on 292 Mip-NeRF 360 bonsai images at 800 px: **292/292 registered**, reprojection error 0.45 px, 18k points; extract 189 s, match 72 s, map 103 s; **$0.08**.
- The gsplat example trainer imports the `rmbrualla/pycolmap` fork (a pure-Python reader named `pycolmap`), so COLMAP runs in its own image, not as the `pycolmap` wheel.

## Coordinate facts
- Marble and TripoSplat are **OpenCV**: x right, **y down**, z forward. Camera `up = [0,-1,0]`. Marble's source-image camera is at the origin looking +z.
- Marble's public example PLYs have no metric metadata; the eye is ~0.6–0.75 units above the ground (densest y layer under the origin). With the API, use `semantics_metadata.metric_scale_factor` and `ground_plane_offset` ([World Labs: rendering SPZ](https://docs.worldlabs.ai/api/rendering-spz)).
- Find the ground under any point with `modal_splat.py::stats --ply … --cx X --cz Z --radius 0.25` (percentiles of y).

## How far a camera can go in a Marble world
Measured on the lane and house examples (dolly stills, `projects/lab-splats/shots/g0_*_dolly.json`):
- **Rotation is free:** a full 360° pan at the origin holds everywhere.
- **Travel holds ~2 units** from the origin along the image's view axis (~1/3 of the way to the far wall); 3 units starts to smear; 4+ breaks into streaks or empty space.
- Close surfaces smear first: keep the lens > ~1 unit from walls and plants.
- So one world = **6–10 s of a slow push plus a pan**, not a walk. Long moves need several worlds joined (the chain below).

## Renderer (`render_shot`, Modal L40S)
- gsplat `rasterization`, `rasterize_mode="antialiased"`, packed mode. **gsplat 1.5.3 packed mode rejects a `[C,3]` background** (`assert backgrounds.shape == image_dims + (channels,)`): composite `rgb + (1-alpha)·bg` yourself.
- Film lens = accumulation: S stratified sub-samples per frame, each with its own shutter time (motion blur), lens point (thin-lens DoF: shift the camera inside the aperture and move the principal point by `fx·dx/F` so the focal plane stays put) and pixel jitter (antialiasing).
- Speed: **0.015 s/frame** for 4M splats at 960×540 with 2 samples; 720p with 6 samples: 240 frames in ~4 s of GPU (14 s wall incl. load). Cost per shot is under 1 cent: GPU time is not the constraint, design is.
- Aperture is in world units. On Marble worlds (unit ≈ 2.5 m) an aperture of 0.025 blurs everything at 1 unit; 0.004–0.007 gives a believable focus pull.
- Layers: `xform` (4×4, rotates quats; SH is not rotated), `grade` (DC colour mul/add), `crop`, `active: [t0,t1]` (skip off-screen worlds), `shadow` (procedural contact shadow: flat dark gaussians on the ground).

## The dust-wave transition (world → world)
Three parts, all pure functions of time (`effects` + `morphs` in the shot JSON):
1. **A dissolves far-to-near:** each splat's start time comes from its distance **rank** to the camera at the cut (not raw distance: a far sky dome stretched the wave so the visible scenery all went at once). The kept 3 % become small round motes (`mote` ≈ 0.0025 units); the rest thin out.
2. **Morph:** 55k splats sampled from A (opacity-weighted, in view) are paired with 55k from B by screen layout (equal-count rows by v, then u) and fly from A's surface to B's surface; launch when A's front passes them, land when B's front passes. Bowed toward the lens (`pull` 0.18), never closer than `rmin` 0.45, luminous in flight (`gain` 1.6 on their own colour).
3. **B assembles far-to-near**, starting ~0.45 s after A.

What failed on the way (`renders/fx1…fx4`): random per-splat turbulence read as a melt; near-first dissolve opened a black void for 1.5 s; 400k motes at 0.005 near the lens filled the frame like confetti; dark source colours made the dust read as static noise. What works (`fx5`): ~1.8 s total, the far end of the old world goes first, a band of warm dust sweeps toward the lens, the new world stands up behind it.

On the studio's own worlds (alley → crater, `renders/draft_alley_crater_v1…v3`) two more fixes were needed:
- **Black gaps.** Between A's going front and B's arriving front the frame showed the black background, and dark source walls (green shutters, shadow) made dark dust that smeared over the bright crater. Fix: **light behind the cut** (`bg_keys`: the background ramps to warm light `[1.0, 0.92, 0.78]` from `cut-pre` to `cut-pre+0.55`, holds to `cut+0.3`, back to black by `cut+post+0.4`) plus `gain` 1.4 on the dissolving and assembling dust, so it glows in its own colour. Now the old world opens into light and the new one forms out of it.
- The light suits the story: the alley's bright arch becomes the noon crater.

## Sound for a splat film (ONE DAY, measured)
- The dust-wave SFX (ElevenLabs SFX via fal: "glittering dust wave, airy whoosh, crystalline shimmer") put almost all energy above 2 kHz (−30 LUFS below 2 kHz, −13 between 2–8 kHz). **Level them by K-weighted momentary loudness (ebur128 `M`), never by RMS of a downsampled copy:** an 8 kHz-resampled RMS said they sat 2–5 dB under the score; ebur128 showed them 10–11 dB over the music body. Target: each SFX peak (M, 400 ms) ≈ the music body level, with the score ducked ~3 dB around it, and a high-shelf −4 dB at 7 kHz + low-shelf +4 dB at 300 Hz to give the whoosh body.
- One ambience bed per world (sea breeze, stone alley, desert wind, harbour water, night crickets), ~14 dB under the score, 1.2 s cross-fades across each cut. Text-to-SFX beds come back at very different levels (−33 to −58 LUFS); measure each and set its gain to a fixed target (−32 LUFS). Regenerate a bed that comes back near-silent (the first night bed: −58 LUFS) — gain on it raises only noise.
- Master once in the mix script (measure → linear gain to −14 LUFS → limiter). Do not run a second dynamic `loudnorm` in the picture finish; v1's double pass landed at −15 LUFS and flattened the swaps.
- Script: `projects/lab-splats/scripts/mix_splat_film.sh` (an example).

## Vertical (9:16) cut
Same chain, second lens: `build_chain.py … --width 1080 --height 1920 --fov-scale 1.45` (vertical fov 55° → 80°, about the same horizontal coverage). Tall arches and big skies read well; the lower third shows more floor, so tilt the aim up a little for vertical-first moves.

## Joining worlds into one move (`build_chain.py`)
Each world keeps its own local camera keys. At each cut the next world is placed so its local camera pose equals the current one: `P[i+1] = P[i] · C_i(cut) · C_{i+1}(cut)^-1`. The global camera follows world i before the cut and world i+1 after, blended over ±0.6 s. Output: a `camera.type = "frames"` shot (per-frame c2w; sub-frame times blend neighbours, so motion blur works).
- **Shutter before t = 0.** Motion-blur sub-samples of frame 0 sit at negative times. World 0's `active` window started at 0.0, so half of frame 0's samples saw an empty world: frame 0 came out at half brightness (mean 40 vs 85) and read as a black first frame — the critic's "dark noise" hook. Fix in `build_chain.py`: the first world's window starts at −10 s. Check frame 0's mean luminance against frame 1 on every chained render (a jump over ~2× is this bug).
- **Open out of haze, not out of black.** A far-to-near assembly leaves the near half of the frame on the background until the end of the build (v2: lower-half luma 4 at 0.0 s, 77 at 1.0 s; the critic called it "dark noise" twice). Set `open.haze` (an rgb near the world's sky, e.g. dawn `[0.5, 0.44, 0.45]`) and start the build before t = 0 (`t0` −1.6, `t1` 1.2): frame 0 already shows the place, and the near ground condenses out of the haze in the first second.

## Captured scenes: measured
| Scene | Trainer | Resolution | Steps / cap | Wall | Cost | Holdout PSNR / SSIM / LPIPS | Splats |
|---|---|---|---|---|---|---|---|
| garden (Mip-NeRF 360) | gsplat 1.5.3 MCMC, antialiased, Modal L40S | images_2 (2594×1680 → factor 2) | 30k / 3M | 43 min | $1.41 | 26.71 / 0.823 / 0.153 | 3.0M, SH 3 |
| garden | Brush (Mac M5 Pro, Metal) | images_4 (1297×840) | 30k | 35 min | $0 | 27.70 / 0.872 | 2.19M |
| bicycle (Mip-NeRF 360) | gsplat MCMC, L40S | factor 2 | 30k / 3M | 60 min | $1.96 | 25.08 / 0.751 / 0.207 | 3.0M, SH 3 |
| room (Mip-NeRF 360, indoor, 311 images) | gsplat MCMC, L40S | factor 2 | 30k / 3M | 125 min | $4.06 | **32.78 / 0.941 / 0.125** | 3.0M, SH 3 |
| berlin apartment (Zip-NeRF undistorted, 1,511 images) | gsplat MCMC, L40S | images_4 | 30k / 4M | 48 min | $1.57 | **8.58 — failed** | 4.0M |

- **Berlin failed** (loss stuck at 0.46, holdout PSNR 8.6) with the trainer's plain COLMAP parser; the run logged "image_path not found for reconstruction". Likely cause, not verified: the undistorted Zip-NeRF layout (its own image folders and camera sizes) needs gsplat's zipnerf benchmark settings, not the Mip-NeRF 360 defaults. Check that the `images_4` sizes equal the COLMAP camera size ÷ 4 before the next large-scene run.
- The two PSNRs are not comparable: factor 2 is scored on 4× the pixels. Both render as photoreal at 1080p from the capture path.
- Brush writes its PLY in the raw COLMAP frame (gsplat writes the normalised frame). Put the Modal `cameras.json` `transform` on the Brush layer as `xform`, and take `up` from the cameras ([[local-muse-mac-helper]] report, `projects/lab-splats/mac/README.md`).
- Orbit design from the capture: up = mean of the cameras' −y axes; focus = least-squares point nearest all optical axes; orbit at 0.8× the median camera radius and 0.85× the median camera height. Inside that envelope there are no floaters.

## Mac side (Local Muse, $0)
Built by Local Muse on the M5 Pro ([[local-muse-mac-helper]]); files and README in `projects/lab-splats/mac/`.
- **Trainer:** Brush (measured in the table above). Its PLY needs the alignment step above before it joins a Modal render.
- **Viewer:** Spark 2.3.1 with three r186, vendored, no CDN (`mac/viewer/`). WASD fly, keys saved as a shot JSON; `?shot=` plays the same camera maths as `modal_splat.py` (max error 4.4e-16). With 2.19M splats: 43 fps mean on screen at 1080p (58.5 median, ~100 ms periodic hitches still open); 60 fps locked at 1280×716.
- **Blender bridge:** the KIRI 3DGS Render add-on 5.1.0 works in Blender 5.2 headless (2.19M splats, 7.4 s per EEVEE frame). `export_splat_camera.py` writes a Blender camera move as OpenCV c2w frames in the PLY frame; Blender's projection and the JSON pinhole agree to 0.00016 px. So a camera move planned in Blender ([[blender-field-notes]]) becomes a `modal_splat.py` render job. Native splat import is in Blender 5.3 (alpha).

## Atlas (World Labs)
Early-access facts change fast: re-check them before any plan relies on them.
Source: [World Labs: Atlas](https://www.worldlabs.ai/blog/atlas) (2026-09-01); [atlasworldmodel.com](https://atlasworldmodel.com/) (independent site, not World Labs).
- **What it is:** an omni world model (multimodal autoregressive diffusion transformer). The inputs are text, images and depth, each at an explicit camera pose (a "spatial context"). The outputs are images, video (up to 1 min at 1440p), point clouds and gaussian splats in the same format as Marble.
- **Camera control is native:** the camera path is an input, not a text prompt. In World Labs' own human-rater test, Atlas followed the camera path better than Seedance 2.5 94 % of the time (MiniMax H3 75 %). A vendor test, not verified by the studio.
- **Space-time** means re-framing *existing* video: 3–5 phone cameras give bullet time and new angles. It does not show text- or rig-driven acting, lip-sync or crowd motion. Robot sim shows objects that move, not performances.
- **Access:** early access for select partners through a waitlist form (`form.typeform.com/to/zHFR4r3A`). The principal is on the list; World Labs emails when access opens. No public API and no price yet. World Labs announced it is joining AMD (2026-09-28): watch the roadmap. Hosted only; no weights.
- **Fit for the studio (hypothesis, untested):** Blender layout → a few photoreal painted key frames at known Blender camera poses → Atlas spatial context → Atlas video along the exact Blender camera path, or a splat for the studio's renderer. That is the Blender-first rule with a 3D-consistent paint pass. Atlas copies what it sees, so CG-looking inputs give CG-looking output: paint the key frames first. Acting and physical motion (people, water, smoke) still need the performance route ([[generation-field-notes]]) or Blender animation, composited in.

## Open questions
- Why the room took 125 min against 43–60 min for the outdoor scenes (more cameras, 311 vs 185–194, explains part, not all). Check GPU type and step time in the log before the next indoor run. An indoor scene trains to the best quality of the set (32.8 dB): small, bounded, evenly lit spaces are the easy case for capture.
