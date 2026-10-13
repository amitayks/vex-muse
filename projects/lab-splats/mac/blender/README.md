# Blender 5.2 splat camera bridge

## How to see a splat in Blender 5.2: the choice
| Option | State (2026-10-10) | Verdict |
|---|---|---|
| **KIRI 3DGS Render 5.1.0** (Kiri-Innovation/3dgs-render-blender-addon, GPL, free) | Released 2026-08-26; supports Blender 5.1 and 5.2. Imports the PLY through Blender's own PLY importer, so the object's local frame is the PLY frame (identity). Real splats in EEVEE (Geometry Nodes, camera-facing quads, sorter, dithered material), plus crop, relight, proxy rig. | **Chosen** for look-dev and for camera work on the real splat. Tested on this Mac (M5 Pro, Blender 5.2.2, EEVEE Metal): import + render work headless. |
| Point-cloud proxy (`proof_scene.py`, own code) | numpy PLY reader -> mesh points + GN Mesh to Points + emission colour. 1.5 M points load in seconds. | Fallback for heavy scenes and for fast camera layout. Not the splat look. |
| Blender 5.3 native splat import (File > Import > PLY / SPZ) | 5.3 is in alpha. Not in 5.2.2 LTS. | Move to it when 5.3 is released. Then re-test the bridge on that object. |
| "SplatForge" | No Blender add-on of that name exists: the repos with that name are a cross-platform trainer, a SuperSplat fork, a Python editor and an iOS app. | Not usable. |
| "Splats" (extensions.blender.org) | Makes multi-view training renders. Does not show splats. | Not for this job. |

KIRI on a Mac: the extension zip has no arm64 scipy wheel (x86_64 only). Its code does not import scipy, so
this has no effect. Install it in a separate profile so your normal Blender profile does not change:
```
BLENDER_USER_RESOURCES=~/muse-splats/blender/userres blender --command extension install-file -r user_default -e 3dgs_render_by_kiri_engine_5.1.0.zip
```
Headless renders: KIRI writes the view to its GN modifier from the 3D View. In `-b` mode there is no 3D View.
`proof_scene.py` writes the scene camera's view and projection matrices into `KIRI_3DGS_Render_GN`
sockets 2-35, with Socket_50 = 0 (camera updates on) and Socket_54 = True (use active camera).
If you do not do this, the render is black. In the UI, set "Enable Camera Updates" + "Use Active Camera" in the KIRI panel.

## Export the camera: `export_splat_camera.py`
```
blender -b scene.blend --python export_splat_camera.py -- --out cam.json --splat <splat object> [--shot template.json]
```
Or run it from the Text Editor (writes `//splat_camera.json`). It also adds File > Export > Muse splat camera (.json).
Output: `{"type":"frames","fps":30,"c2w":[[16 floats] per frame],"fov":[vertical deg per frame],"focus":[...]? ,"_meta":{...}}`
- c2w = OpenCV camera-to-world (x right, y down, z forward), row-major, in the PLY world frame:
  `normalize_scale(splat.matrix_world^-1 @ cam.matrix_world) @ diag(1,-1,-1,1)`.
  So the splat object can be moved, turned (for example Z-up) or uniformly scaled in Blender.
- The splat object is `--splat`, or the first object with the custom property `muse_splat = 1`. With neither, the Blender world frame is used.
- fov = vertical, from Blender's own projection matrix (sensor fit, sensor size, lens/FOV, render aspect).
- Refused: lens shift and non-perspective cameras. Warned: non-square pixels, scale that changes during the move.
- `--shot template.json` writes a complete render job (camera replaced, fps and duration set).

## Proof of the convention (`proof_scene.py`)
The splat object is translated, turned so that the capture's up = +Z, and scaled x2. The camera is animated
over 60 frames (dolly, truck, yaw, roll, lens 30 -> 42 mm).
At frame 30, 500 PLY points are projected two ways: (a) Blender's `world_to_camera_view`, (b) the exported c2w + vertical fov
through the pinhole that modal_splat.py uses. The disagreement is 0.0002 px max.
The same frame is then rendered by Blender (KIRI EEVEE) and by the Spark viewer from the exported JSON. The two framings match (see side_by_side / overlay).
