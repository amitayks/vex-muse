# lab-splats — gaussian-splat worlds with an exact camera

A splat world is a static, photoreal 3D asset. The camera in it is exact code, so no model invents
the motion (the Blender-first rule). One world gives many lenses: the 16:9 and 9:16 cuts are two
renders, not a crop. Findings, costs and gotchas: `knowledge/references/splat-field-notes.md`.
Lab record: `knowledge/projects/lab-splats.md`. First film on it: `knowledge/projects/splat-world-01.md`.

## Files
| Path | Job |
|---|---|
| `scripts/modal_splat.py` | The Modal farm (volume `muse-splats`): `capture` (video/photos -> COLMAP poses), `train_run` (gsplat 1.5.3 MCMC), `render` (film lens: motion blur, thin-lens DoF, antialiasing; dissolve / assemble / morph effects), `stats`, `url` (pull a PLY into the volume), `fetch` (research datasets, lab study only). Shot JSON schema in its docstring. |
| `scripts/marble.py` | World Labs Marble (World API) client, stdlib only: `gen`, `resume --op` (finish a paid run without a second charge). Key `WLT_API_KEY`. |
| `scripts/gen_worlds.sh` | Generate several Marble worlds from the project's own stills in parallel, then pull each PLY into the volume. |
| `scripts/build_chain.py` | Join several worlds into one unbroken camera move with dust-wave transitions; writes a `camera.type = "frames"` shot. Example input: `examples/chain.example.json`. |
| `scripts/reel.py` | Cut a labelled proof reel from clips. |
| `scripts/finish.sh`, `scripts/phone.sh` | Picture finish (grain, vignette, music tail); a two-pass phone copy under a chat upload cap. |
| `scripts/mix_splat_film.sh` | Example mix of the first splat film (score ducking, SFX by ebur128, one bed per world). |
| `mac/` | The $0 Mac side: Brush trainer runs, the Spark viewer (real-time fly-through and shot playback, parity with the Modal camera maths), the Blender camera bridge (`export_splat_camera.py`). |

## Typical run
```
source tools/env.sh
# one world from a still (or capture + train for a real place)
python3 projects/lab-splats/scripts/marble.py gen --name my-world --model marble-1.1-plus --image still.png --out worlds/w1 --ledger ledger.jsonl
$PY -m modal run projects/lab-splats/scripts/modal_splat.py::url --url "<ply_url from world.json>" --dest worlds/my/w1.ply
# plan the move (viewer, Blender or keys), then join worlds and render
python3 projects/lab-splats/scripts/build_chain.py chain.json shot.json --width 1920 --height 1080 --samples 8
$PY -m modal run projects/lab-splats/scripts/modal_splat.py::render --shot shot.json --out renders/film.mp4
```
Check frame 0's mean luminance against frame 1 on every chained render (a jump over ~2x is the
shutter-before-t=0 bug, fixed in `build_chain.py`).

Research captures (Mip-NeRF 360, Zip-NeRF) and World Labs demo worlds are for lab study only and are
never shipped or posted. No splat files, renders or recordings are in this repo.
