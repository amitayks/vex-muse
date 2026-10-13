# lab-splats / mac: the Mac side of the splat pipeline ($0)

Local Muse, task `splat-station`, 2026-10-10. Machine: MacBook Pro, Apple M5 Pro, 48 GB, macOS 27.0.1, Blender 5.2.2 LTS, Chrome 154.
Mac root: `~/muse-splats/`. No paid calls. Spend: $0.

## 1. Brush trainer: garden, images_4, 30k steps
| Metric | Value |
|---|---|
| Trainer | Brush `brush-cli 1.0.0`, built from main `1388f74` (2026-10-03) with cargo in 3 min 42 s. The newest release, v0.3.0, is 13 months older and is also downloaded. |
| Wall time | **2,088 s (34 min 48 s)** for the process. Brush reports 2,076 s of training. |
| Splats | **2,190,308** (1.57 M at 5k, 2.08 M at 13k; growth stops at 15k) |
| Peak memory | **6.46 GB peak memory footprint** (`/usr/bin/time -l`, includes Metal unified memory); max RSS 3.20 GB |
| Holdout PSNR / SSIM | **27.70 / 0.872** at 30k on 24 views (every 8th image by name, the standard split) |
| PSNR curve | 5k 26.55 · 10k 27.16 · 15k 27.43 · 20k 27.51 · 25k 27.50 · 30k 27.70 |
| PLY | `~/muse-splats/vol/runs/garden-brush1/ply/garden_brush1_30000.ply`, 516,914,306 B, sha256 `44aa05bd90ec92899fff485d5790ac311c1d41a19dcd5b9b906c4547391104f9`. Stays on the Mac. |
| Capture zip | `~/muse-splats/data/360_v2.zip`, 12,535,427,936 B, sha256 `77332bf4eba3b8ca0c7f70130849b1e394efdd60d8f20efa6f217081d08a8b2a`. Stays on the Mac. |

Command (`tools/train_brush.sh brush1 <bin> --total-train-iters`):
`brush ~/muse-splats/data/garden_i4 --total-train-iters 30000 --eval-split-every 8 --eval-every 5000 --export-every 30000 --export-path ... --export-name garden_brush1_{iter}.ply`

Gotchas:
- Brush looks up a COLMAP image by suffix and takes the alphabetically first match, which is `images/` (full resolution). To train at images_4, make a folder with `images/` = a copy of `images_4/` and `sparse/0`.
- The Brush PLY is in the **raw COLMAP frame**, not the gsplat `normalize=True` frame of the Modal runs. To use it in a gsplat-frame shot, set the layer `xform` to that Modal run's `cameras.json` `transform`.
- Do not trust Brush's PLY header "Vertical axis" (`-0.0089 -0.8822 +0.4707`). The z sign is wrong. The true up is `-0.0017 -0.8823 -0.4706`, which is the mean camera up and lies 0.42° from the normal of the camera ring. In shots, use `"up": "auto:garden-brush1"`.
- `vol/runs/garden-brush1/cameras.json` has the same shape as the one modal_splat writes: training cameras, OpenCV c2w, K at images_4, identity transform, auto_up. It is made by `tools/colmap_cameras.py` (stdlib).

## 2. Spark viewer: `viewer/` (see viewer/README.md)
Spark **2.3.1** (newest 2.x) + three.js r186, vendored. Spark inlines its worker and WASM, so the page makes no network request beyond 127.0.0.1.
`python3 viewer/serve.py` serves the page at `/` and `~/muse-splats/vol` at `/vol/` (the local mirror of the Modal volume).
- Free flight: `/?file=runs/garden-brush1/ply/garden_brush1_30000.ply&cams=runs/garden-brush1/cameras.json`. WASD, E/Q, mouse drag, wheel speed. K drops a shot key, P saves `shot.json`.
- Shot mode: `/?shot=shots/garden_orbit.json` plays `camera.type` "keys" (Catmull-Rom, ease, roll, `auto:<run>` up) and "frames" (Blender export).
  `shotcam.js` is a line-by-line port of modal_splat.py. The parity test against the Python functions gives a max error of 4.4e-16 over 390 samples.

**Recording** `out/flight/garden_free_flight.mov`: 11.0 s on screen, 2560×1432 (window region), H.264, 57.5 MB.
The flight is driven by real input events (held W/D/E/S/A keys + mouse drag): an approach, an orbit around the table, a rise, a push-in, a pull-back.

| fps (2.19 M splats, SH3) | mean | median | 1 % low |
|---|---|---|---|
| On screen, 2560×1432 retina, **during the screen recording** | **34.2** | 34.4 | 10.6 |
| Headless, 2560×1432, no recorder | 35.1 | 59.9 | 10.0 |
| On screen, ~1906×1072 (1080p), orbit shot, no recorder | **43.1** | **58.5** | 11.9 |
| Headless, 1280×716, free flight | 60.0 (vsync cap) | 59.9 | 59.5 |
PLY load + init: 0.6–0.8 s from localhost.
At 1080p, Spark holds ~60 fps for most frames, but there are periodic ~100 ms hitches. At retina size it is fill-bound (~34 fps).
Open item: tune the hitches (Spark LOD / SPZ conversion / maxSh). An uncapped fps run with `--disable-frame-rate-limit` is invalid in headless Chrome, because rAF timestamps stop tracking GPU work. Do not use it.

## 3. Blender 5.2 bridge: `blender/` (see blender/README.md)
- **Add-on choice: KIRI 3DGS Render 5.1.0** (2026-08-26, supports 5.1/5.2, GPL, free). It shows real splats in EEVEE. Tested here: 2,190,308 splats imported and an EEVEE frame rendered headless in 7.4 s (19 s for the whole job).
  Installed in a separate profile (`BLENDER_USER_RESOURCES=~/muse-splats/blender/userres`). The principal's normal Blender profile did not change.
  Fallback: the point-cloud proxy in `proof_scene.py`. Next step: Blender 5.3 native splat import (alpha). There is no Blender add-on called "SplatForge".
- `export_splat_camera.py`: active camera -> `{"type":"frames","fps","c2w":[16 floats per frame, OpenCV, row-major, PLY frame],"fov":[vertical deg]}`.
  It works when the splat object is moved, rotated or scaled (the export applies `splat.matrix_world^-1`). The fov comes from Blender's own projection matrix. Lens shift is refused.
- **Proof** (`out/proof_garden_kiri/`): the splat object is translated, turned Z-up and scaled x2, and a 60-frame move is exported.
  At frame 30, 500 PLY points projected with Blender's `world_to_camera_view` and with the exported c2w + fov agree to **0.00016 px max** (5.6e-5 px mean).
  The KIRI EEVEE render and the Spark render of frame 30 from the JSON align: phase-correlation shift **0, 0 px**.

Frame 30 (t = 0.9667 s), c2w (OpenCV, PLY frame, row-major):
```
[0.9912191, -0.0029208, 0.1321978, 0.4970428,
 0.0410420, 0.9571754, -0.2865849, 2.7939434,
 -0.1256995, 0.2894941, 0.9488904, -2.5542891,
 0, 0, 0, 1]      vertical fov 31.4173 deg (lens 36.0 mm, 1280x720)
```
(The exact values are in `blender/proof/proof.json`. The block above is rounded to 7 digits.)

## Paths on the server workspace: `projects/lab-splats/mac/`
`README.md`, `viewer/**`, `blender/{README.md,export_splat_camera.py,proof_scene.py}`, `blender/proof/*`, `tools/*`, `tests/*`,
`results/{brush_garden.json,train_brush1_log_excerpt.txt,mem_brush1.tsv,cameras_garden-brush1.json,flight_stats*.json,bench_*.json}`,
`shots/{garden_orbit.json,proof_garden_blender.json}`, `media/{garden_free_flight.mov,flight_sheet.png}`.

## Stays on the Mac
PLY (517 MB), the 12.5 GB zip, the extracted garden, `out/proof_garden_kiri/proof_scene.blend` (542 MB), the Brush build, the KIRI profile.

## In this repo
Only the code and this record ship. The trained PLYs, the capture zips, the recordings, `results/`
and `media/` stay on the Mac (research datasets are lab-only). The viewer's vendored libraries are
fetched once (see `viewer/README.md`).
