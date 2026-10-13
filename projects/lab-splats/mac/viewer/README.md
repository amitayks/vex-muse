# Muse splat viewer (Mac, $0)

Spark 2.3.1 (World Labs, `@sparkjsdev/spark`, MIT) on three.js r186, vendored in `vendor/`.
No CDN at run time: the Spark module inlines its sort worker and WASM.
Real-time view of PLY / SPZ / SPLAT / KSPLAT / SOG splats, WASD + mouse fly, and playback of Muse shot JSON.

## Run
```
python3 serve.py --vol ~/muse-splats/vol          # http://127.0.0.1:8765/ ; /vol/ = local mirror of Modal volume muse-splats
open "http://127.0.0.1:8765/?file=runs/garden-brush1/ply/garden_brush1_30000.ply&cams=runs/garden-brush1/cameras.json"
open "http://127.0.0.1:8765/?shot=shots/garden_orbit.json"
```
Paths without a scheme, `/` or `.` resolve against `?root=` (default `/vol/`), so a shot JSON for
`modal_splat.py` plays here unchanged when its PLYs exist under the same relative path.
You can also drop a splat file on the page.

## Free flight
| Input | Action |
|---|---|
| W A S D | fly forward / left / back / right |
| E or Space / Q or C | up / down along the world up |
| drag (left mouse) | look; arrows also look |
| wheel | fly speed |
| Shift / Alt | x4 / x0.25 speed |
| `[` `]` | jump to the previous / next training camera (needs `&cams=`) |
| `-` `=` | fov wider / narrower; `Z` / `Shift+Z` roll |
| K | add a shot key at the current pose (2 s apart); X clears |
| P | download `shot.json` (camera.type "keys", same schema as modal_splat.py) |
| R | reset; H toggles the HUD (fps, splats, pos, fwd, up) |

World up: `&up=x,y,z`, or the mean training-camera up from `&cams=` (same rule as `up: "auto:<run>"`),
else `0,-1,0` (OpenCV-style PLY).

## Shot mode `?shot=<file>`
Reads the shot JSON (schema: docstring of `projects/lab-splats/scripts/modal_splat.py`) and plays the
camera in real time. `shotcam.js` is a line-by-line port of `look_c2w`, `_catmull` (Catmull-Rom tangents
scaled by key durations), `_ease`, `camera_at` (keys and frames, Python round-half-even for frame index).
Parity test vs the Python functions: `node ../tests/parity.mjs` (390 samples, max error 4e-16).
- `camera.type: "keys"` (pos / look / fov / roll, `ease`, `up` incl. `auto:<run>` -> `/vol/runs/<run>/cameras.json`)
- `camera.type: "frames"` (OpenCV c2w per frame + vertical fov; the Blender export)
- `layers[].ply` + `xform` (row-major 4x4), `bg`, `width`/`height` (canvas aspect is locked), `fade` effects.
- Not previewed (render-only on Modal): `dissolve`, `assemble`, `crop`, lens blur / DoF / motion blur.
- Keys: Space play/pause, `,` `.` step one frame, Home restart, F take over with free flight.
- `&t=<sec>` freezes a time; `&still=1` renders exactly width x height at dpr 1 and sets
  `window.__still_ready` after the sort settles (used by `tools/still.mjs`).

## Measuring fps
`window.__viewer.resetFps()` then `window.__viewer.fpsStats()` -> mean / median / 1 % low fps, worst frame,
drawing-buffer size. The HUD shows a 1 s rolling fps.

## Files
`index.html`, `viewer.js`, `shotcam.js`, `serve.py`, `vendor/three/{three.module.js,three.core.js,addons/postprocessing/Pass.js}`,
`vendor/spark/spark.module.js`, LICENSE files.

## Vendor libraries (not in this repo)
The vendored builds (about 5 MB) are not committed. Fetch them once, at the pinned versions:
```
cd viewer && mkdir -p vendor/three/addons/postprocessing vendor/spark && T=$(mktemp -d)
(cd $T && npm pack three@0.186.0 @sparkjsdev/spark@2.3.1 >/dev/null && for f in *.tgz; do tar xzf $f && mv package ${f%.tgz}; done)
cp $T/three-0.186.0/build/three.module.js $T/three-0.186.0/build/three.core.js vendor/three/
cp $T/three-0.186.0/examples/jsm/postprocessing/Pass.js vendor/three/addons/postprocessing/
cp $T/sparkjsdev-spark-2.3.1/dist/spark.module.js vendor/spark/
```
Check the paths inside each package if a release moves them. Both libraries are MIT.
