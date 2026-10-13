---
kind: technique
tags: [blender, local-muse, rendering, field-notes]
audience: studio-internal
half_life: 90
rights: safe
seen: 2026-10-13
summary: "Blender on the principal's M5 Pro Mac: render settings and speeds per job, the numeric draft checks before a final, light and exposure fixes, water and mist as volumes, propeller blur math, camera solve by search, camera and event exports for sound design, and the clip spec for the paint pass. People and first-person cameras are in blender-people."
---
# Blender field notes — Mac renders, draft checks, look fixes

Observed on Blender 5.2.2 on the principal's M5 Pro Mac ([[local-muse-mac-helper]]) in the first Blender lab ([[lab-blender]]). S1 is a music-synced piece on the Alpenglow world. S2 is the [[action-01]] water drop, rebuilt as a base for the paint pass. The engine choice per shot is in [[tool-selection]] (Blender row). The paint pass over the renders is in [[render-repaint]]. People and the first-person camera are in [[blender-people]].

## Render settings and speeds
| job | settings | speed |
|---|---|---|
| Alpenglow world (362k instances), draft | Cycles Metal, 480×270, 16 spp | 1.53 s/frame |
| Alpenglow world, final | Cycles Metal, 1920×1080, 32 spp, adaptive threshold 0.02, OIDN, persistent data | 13.2 s on one cold test frame; mean 8.45 s/frame in the run (7.9–10.1 per shot); 432 frames in 61 min |
| Drop stage 2: terrain, water and mist volumes, 21 lights, motion blur | EEVEE, 1280×720, 32 samples, volume tiles 4 px, 96 depth samples, volume shadows on | mean 4.3 s/frame (1.7–8.9; the dense volume shots are slowest); 288 frames in 21 min |
| TOWER 42 look stills: city, lobby, lift, office, MPFB people | Cycles Metal, 1920×1080, 128 spp | 46–96 s/frame (exteriors fastest, the office slowest). On the dressed scene with an adaptive threshold of 0.015 and OIDN: 20–66 s/frame |
| TOWER 42 dressed scene, 70 MPFB people, 6 s test clips | Cycles Metal, 1280×720, 32 spp, OIDN | 8.3–11.0 s/frame on the test clips; 7.5–9.7 s/frame per chunk on the full 2,520-frame draft (6 h 17 min in all), after about 9 min of whole-film exposure metering. EEVEE (64 samples, 4 motion-blur steps) took 22.6 s/frame alone and 25–35 s/frame beside Cycles, so Cycles replaced it on this scene |

- Render one cold test frame before the final. Pick the sample count that meets the per-frame budget (32 spp gave 13.2 s against a 14 s budget).
- Two Blender jobs on the Mac share one GPU. The S1 final slowed while the drop tests ran, and Local Muse put a TOWER 42 draft slowdown (6.3 to 7.5 s/frame) on a side export that ran at `nice 19`. Run no other Blender job next to a long render. A Workbench preview started beside a Cycles GPU render waited on the Metal queue and never finished, so side jobs run GPU-free (Cycles CPU with CPU OIDN). At background priority a side job gets about 0.4 of a core, and `scene.ray_cast` walks every instance per ray, so a ray grid over the dressed city takes hours; keep side-job ray counts small.
- A closed lid stops a render: see [[local-muse-mac-helper]] (Health).

- **Cycles Metal can deadlock mid-render.** A render got no new frame for 30 min: the process sat at 0 % CPU in `ShaderCache::get_best_pipeline`, waiting for a kernel pipeline, while every compile thread sat idle. Memory was not the cause (85 % free). Kill it and resume from the first missing frame; frames on disk are kept. It struck twice in one 2,520-frame film. Run long renders under a supervisor that kills and resumes after 10 min with no new frame (at most 6 restarts, one report line each); the second hang cost 10 min instead of 30, with no help.
- **Memory follows the content in view, not the run time.** A lobby chunk with a strand-haired crowd took 22–25 GB of the Mac's 48 GB, against 11 GB for the drone chunk, and a fresh Blender on the same frames reached 23.6 GB in 2 min, so it was not a leak.

## Draft checks before a final
Render a cheap draft with a burn-in of timecode, frame, marker and camera. Check it with numbers, then start the final:
- **Frames:** every frame is present, and the clock is linear (duration = frames ÷ fps).
- **Cuts:** the largest frame-to-frame changes fall exactly on the planned cut frames.
- **Light cues:** measure each lamp on its own pixels. Its first rise must land on the cue frame. A frame-wide "first jump" test flagged two cues 3–5 frames early, in an area that other lights already lit.
- **Colour hand-off:** measure the change as one number. For the Alpenglow summit, the pink was R−B of the upper highlights; the hand-off passes when it reaches 0 on the planned frame.
- **Look stills:** one full-size keyframe per shot (1920×1080, 32 spp) for the look review. Pick each still away from a whip: a mirror still on a mid-turn frame looked broken, though its motion blur was correct.
- **When fixes change more than about 60 % of the frames,** render the whole film again in the same chunk boundaries instead of splicing ranges, so the paint chunks map one to one. Decide this before any pixel probe: on the dressed city (6,046 buildings) the exact visibility probe ran 13 s/frame, about 4.5 h for the film.
- **A fix to one shot:** re-render only that shot's frames and splice them in. Then compare the evaluated scene state of the other shots on probe frames, before and after the fix; it must be identical.
- **Fold a late fix in before the first chunk where the changed object is in view.** A screen removed for the last chunk was in the camera frustum in 293 of 317 frames of the chunk before it, so the fold moved to the seam before that chunk, behind closed lift doors where nothing can pop. Test the object's frustum per frame across every earlier chunk before you pick the fold point. Swap the scene and the exposure curve together between chunks, and keep the originals.
- **Contact gate** (bodies on terrain), per frame and per body. FLOAT: the lowest point is more than 20 mm above the ground under it. SINK: any point is more than 2 mm below the ground. INTERSECT: a body triangle cuts the terrain or a rock (BVH overlap). Cast rays straight down from each body vertex onto the evaluated terrain.
- **Gates read the live scene camera.** After the end grew from 2,448 to 2,520 frames, the gates still read the old exported camera.json and skipped the new end. Point every gate at the scene camera and the full frame range.
- **A scripted render of a second scene takes the context scene's frame.** Set the frame on the scene you render: a variant sheet rendered at the hero frame came out with people keyed hidden and movers out of shot.
- **Never save a .blend under `/tmp` on macOS.** Blender stores texture paths relative to the .blend, and macOS resolves `/tmp` to `/private/tmp`. A scene saved there wrote 149 paths as `//../Users/...`, and all 149 were missing on load. Rebasing them to absolute paths fixed it (284 images, 0 missing). macOS also clears `/tmp` at boot. Save under the project folder, and run a missing-image check after every save and reload.
- **A gate on an empty mask proves nothing.** A crown-scalp metric projected its disc off the head and read 0 of 0 pixels as a pass. A hair-silhouette check found no pixels on strand hair and printed FAIL. Check the mask's pixel count before reading a gate. Muse's ruling: drop a dead metric instead of spending CPU on it; the eye pass replaces it.
- **Check a recolour by its colour in a render, not by its name.** A dark-felt material rendered light grey: its Principled Base Color was unlinked at the 0.8 default, and its two textures drove only roughness and the normal map. The patch's gate checked the material name, so it passed. The same patch first picked only faces near the panel's centre axis and missed the broad faces of the thick screen.
- **Ray hits on a mesh with a generating modifier return evaluated face indices.** On a desk mesh of 2,640 faces with a Bevel modifier, `scene.ray_cast` returned indices up to 23,760, and a script indexed past the mesh. Map each hit to the original face by position.

## Geometry decides the look
- **Procedural boxes render as a 3D render, whatever the materials.** On TOWER 42 the box city, the plain roof, the empty lobby walls and the stair-stepped chairs read as a game engine or a CAD view at 128 spp. Dress the base like real archviz before any look pass: real furniture, stone and timber, plants, depth behind glass, and varied neighbours. A paint pass cannot add what the base lacks ([[render-repaint]]).
- **Overlapping wall boxes render black in Cycles.** Make the walls butt, not overlap.
- **Small props need their real parts.** Keyboards made of slots with no separate keycaps read as heater grills in the draft.
- **Clear curtain-wall glass shows a false "dome".** From a camera diving down the façade, the lit core walls showed through the empty floors as a curved grey shape: its edge is a line of constant ray elevation. Reflective coated glass on the façade removed it and shows sky and city instead. Coat only the outside face: the same coating on the office windows reflected the room from inside and hid the city at his desk.


## Light and exposure fixes that worked
- **A thin refractive glass sleeve renders black with caustics off.** Cycles lit nothing inside a glass badge sleeve, so the card rendered as a solid black block. A thin clear film (Fresnel mix of transparent and glossy, no refraction) fixed it.
- **A practical light behind a solid wall does not read.** Move it to a window that the camera sees, and raise the power. The S1 table lamp went to 0.9 m inside a window at 160 W (from 40 W). The porch lantern went from 30 W to 90 W. Both then read on their beat.
- **Dusk with the sun under the horizon renders dark.** Set the exposure per shot, on the cut. S1 kept −2.0 EV on the sunset shot and used +2.0 EV on the cut into the aerial end. The opening shot was ~1.3 stops darker than the next one, so it read as night before dusk. A lift from −2.0 to −0.7 EV on its frames only fixed it. A +2.0 EV jump on one cut still shows as a hard exposure step.
- **Cheat a prop per shot.** Put a linked duplicate in one shot's foreground and hide the real object on those frames. This gave the S1 opening its boat bow and rope.
- **Nightfall after the last light:** halve the sky background (1.0 → 0.5) and the haze emission (3.2 → 1.6). Take the cloud emission to near zero (6 → 0.04) over ~4 s, and cool the sun from 2700 K to 1900 K.
- **A lower sun alone does not make alpenglow move.** On the Alpenglow world the summit dimmed evenly; no earth shadow climbed the mountain.
- **EEVEE haze needs a bounded volume.** A world volume is infinite, and it turned the sky and the sun black. A volume box works (drop: 5.2 × 5.2 × 1.25 km, density 0.0009 /m).

- **A dark shot can be the exposure, not the light.** The TOWER 42 lift cab had 490–860 lux at chest height, yet a 35 s ride read dark: the cached whole-film exposure sat at −2.41 EV there. (A light probe that read 0 lux sat inside his body.) The replacement meter: probes every 12 frames (16 spp, linear EXR, about 3.3 s each), the 10–90 percentile luminance to 18 %, a slew of at most 1 EV/s and at most 0.5 EV per 6 frames, and a 1.5 s ease through doorways. It set the cab at −1.40 EV, and the mirror and lobby stills passed Muse's eye check. After a late fix, re-meter only the changed range and keep the cached probes, so frames already approved keep their curve.

## Water, mist and steam
- Particles drawn as instanced spheres read as "a cloud of white balls" in review. The paint pass kept them CG ([[render-repaint]]).
- The drop stage-2 route feeds the same particle cache into geometry nodes:
  - **Spray:** Points to Volume, then dilate the density grid by 3 voxels and mean-filter it (2 passes, width 2). This gives a dense white core with thin, soft edges and no sphere outlines. Material: white aerated volume (`#EEEDE8`, forward scatter 0.45, density broken by noise).
  - **Solid water** (the slab in its first 0.5 s out of the doors, and the full curtain): Points to SDF Grid, SDF mean filter (4–10 iterations), then a mesh. Remove mesh islands under 400 vertices. Material: white, roughness 0.62, subsurface 0.35, never glassy. A solid wall inside a soft spray volume gives the paint model a clear shape with soft edges.
  - Set the voxel size and the point radius per shot: fine near the lens, coarse far away.
  - Mist and steam are volumes with the same blur.
- **EEVEE does not motion-blur volumes.** Only the meshed water gets the shutter blur.
- A camera that looks down on a falling curtain from 40 m makes it read as a diagonal wall, not a tall sheet.

## Camera and motion
- **Propeller blur:** sweep per blade in one exposure = rpm × 6 × exposure time (s), with exposure time = (shutter ÷ 360°) ÷ fps. At 1,050 rpm, 24 fps and a 180° shutter, each blade sweeps 131°. With 4 blades the disc is one even veil, so render a blur disc with a soft ring at the blade tips. Rendered blades show a frozen or strobing prop.
- Motion blur in the drop: 180° shutter (0.5 frame), centred.
- **Watch for quaternion sign flips on a keyed camera.** A flip between two keys spun the camera 360° in one move (a peak of 8,640°/s on the gaze gate). Keep consecutive keys on one hemisphere and gate the peak view rate.
- **Solve a camera by search when the framing goals fight the geometry.** Score each lens, tilt, roll and position against the goals as numbers: frame fill at the centre crossing, the crossing time before the cut, and the water landing after the cut. For the drop, 72 combinations ran, and only one met all three goals: 32 mm, tilt 14°, roll 30°. The brief's 24 mm gave at most 48 % fill, because a ground camera is at least 45 m from a 20.6 m aircraft.
- Brief frames are goals, not fixed positions. The built world can forbid a frame (in S1 the boat was moored on the wrong side for the brief). Local Muse changes what the geometry forbids and gives each change with its reason in the report.

## People and first-person cameras
Rigged humans, crowds, held props and the first-person camera gate are in [[blender-people]].

## Exports for sound design
The Blender scene, not the picture, places the sound ([[blender-people]] for the people it reads):
- **Camera track:** one row per frame with the world position, yaw, pitch, roll, focal length, horizontal field of view and the forward and up vectors. Sounds are panned by their angle to this camera and levelled by distance.
- **Event list:** heel strikes, doors, buttons, lift and cab events, each with a frame and a world position. Each heel strike gets its floor by a ray cast down from 0.30 m above the heel that skips characters. A strike on a shared edge needed a re-cast 2 cm inside. A detector on the evaluated foot bones matched all 54 planned strikes of the man (median offset −1 frame, max 2), so passers-by within 4 m of the lens get their strikes from the same detector.

## Clips for the paint pass
- One clip per shot: 1280×720, 24 fps, H.264 CRF 14, no burn-in. Clip frame 1 is the handle-in frame.
- **One render can be both the draft and the paint base.** On the dressed TOWER 42 scene, Cycles at 32 spp with OIDN was faster and better than EEVEE, so the full draft renders in Cycles at 1280×720 and goes straight to the paint pass, in chunks of at most 340 frames (under the 15 s limit of [[render-repaint]]).
- **Handles cross camera cuts.** The drop scene has one timeline with camera markers, so each 12-frame handle showed the neighbouring shot's camera. An anchor made from such a frame paints the wrong shot. Trim each clip to its own frames plus at most 4 handle frames before painting, or render the handles through the shot's own camera.
- Add a grey cut on film time, with black slugs for the shots that come from another source.
- 720p matches the paint model's limit, and one shot per call prevents the cross-cut fault ([[render-repaint]]).
- Drafts carry a burn-in. Finals and paint inputs do not.
