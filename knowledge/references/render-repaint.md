---
kind: technique
tags: [generation, blender, video-to-video, paint-pass]
audience: studio-internal
half_life: 60
rights: safe
seen: 2026-10-13
summary: "How the studio repaints Blender renders into live-action footage: the base sets the ceiling, a five-model video repaint test (Flux 3 edit-video leads), Flux 3 behaviour, the identity jump at chunk seams, and the LTX 2.3 render-to-real paint pass with a strict-repaint anchor."
---
# Render repaint: Blender renders to live-action

Blender gives the movement, the geometry and the camera. A model then paints the look over the render ([[tool-selection]], Blender row). Evidence: [[lab-blender]] (the [[action-01]] water drop) and the TOWER 42 one-take (tools in `tools/repaint/`). Rules for the Blender base and the clips: [[blender-field-notes]].

## The base sets the ceiling
- **A repaint keeps what the base has. It cannot add what the base lacks.** A Nano Banana Pro strict repaint of four Cycles stills made hair, a shirt, a sunlit lobby behind glass and a face in a lift mirror look photographed. A near-empty white lobby corridor and an office of block chairs barely changed. Dress the base first ([[blender-field-notes]], geometry). On the drone dive the plain roof became real gravel, but the box city blocks around it stayed boxes. After the blocks got window grids, street trees and cars in Blender, the same repaint gave real window grids, trees, cars and a glass façade that reflects the city. A green roof added in Blender came back as stained brown gravel, which still read as real.
- **Faults on people stay.** Helmet-shaped bob hair stayed a helmet, and a crumpled blouse shoulder stayed lumpy, while the floor display and his face in the lift mirror became real. Fix hair and cloth in Blender ([[blender-people]]). Once the base was fixed, a paint test of the mirror still made the people real, and the shoulder bulk left over from a corrective smooth read as cloth. To judge whether a fault survives the paint, paint a 3 s loop of the still (about $0.09 on Flux 3 edit-video).
- **The base carries the design; the repaint carries realism.** Layout, wardrobe and colours come from the base. Video edit models mostly keep the base colours, but they can re-dress people: Flux 3 kept a green shirt green in the lobby, and on the merge it turned crop tops into dark suits. Give the base a wardrobe that the model has no reason to change.

## Video repaint test
One 6 s Cycles clip: 1280×720, a first-person walk through a lobby, about 20 MakeHuman people, a hand on a turnstile. One prompt for all models: "turn this 3D render into real live-action footage … keep the camera, framing, timing, layout and every person's position and motion".

| model (fal) | price | result |
|---|---|---|
| `blackforestlabs/flux-3/edit-video` | $0.03/s; about 50 s wall | **Leader.** Real people, clothes, skin, stone and steel. The camera, the layout and each person's path stay. |
| `google/gemini-omni-flash/v1.1/edit` | $0.10/s at 720p; 1920×1080 out | The most photoreal, but it re-composes: it adds people, moves the lift doors and replaces a wall. Unsafe for a one-take. |
| `fal-ai/ltx-2.3-quality/render-to-real` with an anchor | about $0.45 per 6 s | Almost no change on people in motion. The CG crowd stays CG. |
| `fal-ai/kling-video/o3/pro/video-to-video/edit` | $0.168/s; about 5 min wall | Almost no change, and ghosting at the end. |
| `minimax/h3-max/3d-to-video` (on the merge clip) | $0.08/s at 768p, $0.16/s at 1080p, 5 s minimum, plus reference tokens | Made for Blender input: up to 15 s at a public HTTPS URL, with optional reference images. Muse's review says it re-generated the scene and changed the geometry; its first look said the output barely differed from the input. Either way, the people did not read as real. |

## Flux 3 edit-video behaviour
- **Inputs:** `prompt`, `video_url` and `safety_tolerance` only. There is no seed and no reference-image input. The input MP4 must be under 15 s and under 50 MB.
- **Output:** 1248×704, so a 1080p master needs an upscale pass ([[generation-field-notes]], video upscaling). The frame count can be one off either way (145 for 144 input frames, 253 for 254), with the alignment still at offset 0: pad or trim the last frame to the source count.
- **Shimmer:** the frame-to-frame change runs about 1.5× the source (median 13.2 against 8.4 on 0–255 grey).
- **Colour:** the output has a warm yellow cast. The prompt now asks for "neutral daylight white balance"; its effect is not yet measured.
- **It obeys "no numbers / no text" literally.** It erased the lift's floor counter, which is a story beat, and a roof helipad marking with its circle. Ban only stray signs and logos when on-screen text carries the story.
- **It recolours displays and clothes a little.** A black floor display with amber digits came back as a white panel with a black digit, and beige tops drifted to white. It can also re-dress a garment: a grey blouse came back as a black blazer, and rust, yellow and light-blue tops came back white across the painted film. A garment keeps its new colour inside one call, so the risk is a change of clothes at a seam. Naming the display's colours in the prompt ("a black glass panel with glowing amber digits") kept it black and amber on the retake.
- **Faces are invented per call.** In the lift mirror, the MakeHuman reflection became a real man with a face, a shirt, a lanyard and a cup. A second call can give the same man a different face.
- **It acts out the prompt.** "His hand puts a cup down" made it invent a hand and a cup on an empty desk (TOWER 42 desk clip). Every story beat must exist in the Blender base. The prompt names only materials, light and people.
- **High-floor window views go real.** The Cycles city behind the glass became a hazy real skyline, and the window frames stayed in place.

- **Text that carries the story must come from the base.** With the display colours named, Flux 3 still painted invented floor numbers: Blender's 11 became 19 and 13 became 12, so the count ran backwards. The fix is to composite the Blender display back over the painted frames through a frame-exact matte (`tools/repaint/composite_display.py`; built, not yet run on the film).
  - **The matte render:** every light, the world and every other emission off; all shaders black and non-reflective, with their transparency kept; the mirror a white perfect mirror; each display pure emission in its own channel. Same camera, shutter and pixel filter as the film, 16 spp. On two test frames it sat exactly on the blurred panel, with 0 px spill. It costs 39 s/frame on CPU and slowed the film render beside it, so it runs on the GPU after the film.

## Seams between chunks
- **Separate calls re-dress the same people.** At the merge-to-lobby join, a pink top became a green tee, a black top became a cream blazer, and the timber wall changed. The mean frame change across the join was 55, against about 13–25 inside a clip.
- **A painted prefix does not carry identity.** A clip that starts with 1 s of already-painted frames gets that second repainted too (mean change about 40), and the jump stays (54 against 55).
- **Inside one call the motion stays smooth, so cut chunks at whip peaks.** Seam candidates come from the Blender camera track: view whips over 120°/s and frames where a near surface covers more than 60 % of the view (on TOWER 42, 23 whips and 10 covers gave 10 chunks). Paint each chunk with 8-frame handles from its neighbours and cross-fade the 16 shared frames with a smoothstep. Take the handles from the same render version as the chunk; a draft neighbour would put stale frames into the join, so a chunk waits for its next neighbour. A seam inside a head whip peaked at a frame change of 47 against 22 in the source, but it sits in motion blur and reads as part of the whip. On the final film's first two seams the joins tracked the source: 15.2 against 13.5 in plain motion, and 40.9 against 37.1 inside a whip. Scripts: `tools/repaint/paint_chunks.py` and `assemble.py`. Still untested: 15 s chunks, and joins behind a door that blocks the view.

## LTX 2.3 render-to-real paint pass
`fal-ai/ltx-2.3-quality/render-to-real` (720p, `strong-v2`) over Blender renders of the [[action-01]] drop. Script: `tools/repaint/ltx_paint.py` (anchor, render-to-real, rescale, `--trim`, `--no-anchor`).
- **Alone, it converts people and objects, not landscapes.** Seated mannequins became real pilots (helmet stripe, headset, hair) and kept their motion. Flame cards, terrain and particle water stayed CG. People walking in a crowd also stayed CG (see the test above).
- **A photoreal first frame as `image_url` makes the landscape real.** Nano Banana Pro edits the render's first frame; render-to-real then holds that look and the Blender motion. The edit prompt must say "strict repaint": no zoom, crop or camera move, every shape in the same pixel position. A loose prompt re-composed the frame (invented mountains, lost the foreground bank).
- **Describe only what is in the frame.** The full Tanker 92 text on wing-only and belly-only shots made both models paint a whole extra aircraft. "Only the wing / the hull underside is visible" fixed it.
- **The anchor frame must belong to the shot.** An anchor from a black head-handle frame invented the subject (a head-on plane). An anchor from a handle frame of the previous shot painted that shot. Trim each clip to start on its own content.
- Long clips drifted from the anchor by their out frame; 4-frame handles held.
- **A big fast mover against empty sky failed both ways.** With an anchor, the aircraft froze in place. Without one, it crossed correctly, then the model invented a second aircraft in the empty sky; the cut ends before that.
- Strong on people from behind, aircraft surfaces near the lens and the water slab pouring from the door. Weak on wide landscapes with a big empty sky, where a distant water curtain read as smoke and steam.
- `intensity: light` burned fake watermark text into one take; `strong-v2` did not.
- A 1280×720 input returns 1152×704, resized rather than cropped: scale it back. Frame counts are 8k+1.
- Billing: $0.0024075 per output video megapixel (about $0.08 for 41 frames at 720p); the anchor edit is $0.15.
