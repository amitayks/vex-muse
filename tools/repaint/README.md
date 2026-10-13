# tools/repaint — paint Blender renders into live-action

The Blender-first rule: a Blender scene gives the movement, the geometry and the camera; a model
only paints the look over the render. Method, model test and failure modes:
`knowledge/references/render-repaint.md`. Rules for the Blender base and the clips:
`knowledge/references/blender-field-notes.md`.

| Tool | Job |
|---|---|
| `paint_chunks.py` | Paint one chunk of a long one-take with a video-edit model (default Flux 3 edit-video, $0.03/s), with 8-frame handles from the neighbours of the same render version. Plan format: `plan.example.json`. `--dry` builds the source and the prompt with no paid call. |
| `assemble.py` | Join the painted chunks into one take. Each seam's 16 shared frames get a smoothstep cross-fade; `--cuts` makes a seam a hard cut. |
| `composite_display.py` | Put story text (a floor display, a sign) from the base render back over the painted frames through a frame-exact matte pass. |
| `ltx_paint.py` | One shot through LTX 2.3 render-to-real, with an optional photoreal first-frame anchor (Nano Banana Pro strict repaint). Converts landscapes; weak on crowds. |

## Order of work
1. Render the full draft in chunks (at most 15 s with handles; cut at whip peaks or where a near
   surface covers the view). Write the plan: one prompt per chunk, naming only materials, light and
   people. Every story beat must exist in the base; the model acts out what the prompt says.
2. `paint_chunks.py plan.json <k> --dry` for each chunk; read `meta.json` (pre/post handles).
3. Paint a test chunk first. Check people, clothes, on-screen text and the frame count.
4. Paint the rest. A chunk waits for its neighbour's final render before it takes handles from it.
5. `assemble.py out.mp4 chunks/c01_t1 chunks/c02_t1 ...`, then measure the frame-to-frame change at
   each seam against the source (a join in plain motion should track the source within ~2 grey levels).
6. If text carries the story, render the matte pass and run `composite_display.py`.

All tools need ffmpeg/ffprobe on `PATH` (`source tools/env.sh`) and the `fal-media` skill with
`FAL_KEY`. Each paid call lands in the ledger you pass with `--ledger`.
