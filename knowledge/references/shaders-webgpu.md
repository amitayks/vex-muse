---
kind: technique
tags: [tools, shaders, webgpu, typegpu, hyperframes, materials, sdf, field-notes]
audience: all
half_life: 60
rights: safe
seen: 2026-10-07
summary: "Shaders (npm `shaders`, MIT, WebGPU) as a seekable HyperFrames layer: what the library is, the Chrome flags and capture route that make it render on a GPU-less box, the driver that makes it frame-exact, rules for deterministic output, the shape and material catalogue, and speeds."
---
# Shaders (shaders.com, npm `shaders`) — WebGPU materials as a seekable HyperFrames layer

**Verdict: adopted.** It is the fastest route to raymarched materials (glass, chrome,
liquid metal, holographic foil, neon, voxels …) on any SDF shape, plus full-frame shader filters
(halftone, dither, CRT, kaleidoscope, chromatic aberration). It renders on this GPU-less box, and the
output is frame-exact through our driver. Lab: [[lab-shaders]] (`projects/lab-shaders/`). Method: skill
`webgpu-shaders`. Engine choice: [[tool-selection]].

## What it is
- `shaders@4.0.0` (Shader Effects Inc.). Open source since 2026-10-06: the engine, all 199 components
  and the framework bindings are MIT. The design editor, the 1,000+ Pro presets, the "sections", the
  MCP server and watermark-free video export stay paid (Pro). We use only the MIT package.
- WebGPU only (no WebGL fallback). It is built on TypeGPU. Components are a JSON tree:
  `{components:[{type, id, props, children}]}`. A component with `requiresChild` is a filter on its
  children; the others generate pixels. Universal props: `opacity`, `blendMode`, `maskSource`,
  `transform`, `boundingBox`.
- Agent docs: `shaders.com/llms.txt` (index) and `shaders.com/llms-full.txt` (all props, defaults,
  ranges; 249 KB). The prop list there is complete; the shape types are not (see below).
- Custom components: `defineShader` from `shaders/std` (WGSL body or std primitives). Not tested yet.

## How it runs here (the facts that bite)
1. **Chrome flags.** Only SwiftShader on Vulkan presents a WebGPU canvas on this box:
   `--enable-unsafe-webgpu --enable-features=Vulkan --use-vulkan=swiftshader
   --use-webgpu-adapter=swiftshader --use-angle=swiftshader`. With the ANGLE-SwiftShader GL flags
   that HyperFrames uses, the device dies ("A valid external Instance reference no longer exists")
   and the canvas stays empty. The page must be a secure context: `file://` or `localhost`, not
   `about:blank`.
2. **`hyperframes render` cannot render it here.** In software mode HyperFrames adds the WebGPU flag
   only for `data-requires-webgpu`, and then it rejects every fallback adapter (SwiftShader is one).
   So we render WebGPU comps with our own capture: `render-review/scripts/modal_hf.py --webgpu`
   (Modal) and `projects/lab-shaders/tests/snap.mjs` (local stills). Both seek the GSAP timeline,
   then await `window.__hfShadersSeek(t)`, then screenshot.
3. **The public API has a wall clock.** `createShader` runs its own requestAnimationFrame loop
   (wall-clock deltas, gated 1–60 fps) and exposes only pause/resume. It also starts telemetry
   beacons. Our driver `projects/lab-shaders/src/hf-shaders.js` (bundled to
   `assets/js/hf-shaders.iife.js`, global `HFShaders`) mounts the same tree on the engine's
   renderer, without telemetry, and seeks to an absolute time:
   `dt = T − renderer elapsed; renderSyntheticFrame(dt)`. Elapsed time and every per-node
   `_animTime` are linear in dt, so a negative dt is exact: random seek order gives identical pixels.
4. **Stray renders.** Each prop update or structural change calls the engine's `requestRender()`,
   which schedules one rAF render with a wall-clock delta. A screenshot then caught a frame 0.03 s
   late. Fix in the driver: during the synchronous mount, rAF is a stub that never fires, so the
   engine's pending-render id stays set and every later `requestRender()` returns early. Verified:
   idle drift 0 over 3 s; shuffled seeks and seeks after idle hash-identical to sequential seeks.
5. **HyperFrames seek protocol (useful beyond Shaders).** The runtime dispatches a `hf-seek`
   window event `{time, waitUntil(promise)}` on every seek and awaits the promises
   (`window.__hfWaitForSeekCompletion`) before capture. `bindToHyperFrames()` uses it.

6. **Hidden canvas sizing.** A preset mounted on a `display:none` canvas measures 0×0, so the engine
   keeps the canvas attribute size (300×150). It applies resizes in a rAF callback, which the driver
   starves. Size-normalised effects (Dither cells, Halftone dots) then come out about 3× coarse. The
   driver sets the canvas attributes and the renderer size synchronously at mount.
7. **Images.** `ImageTexture` loads with `fetch`, which cannot read `file://`, so pass a `data:` URL.
   It decodes after the first frames; the driver waits for each image's natural size before `ready`.

## Rules for frame-exact output
- Keep every `speed` prop constant for the life of a mount (animated time = speed × elapsed).
- Animate any other prop per frame with `layer.set(id, props)` as a pure function of t. Measured:
  shape sub-props (`rotX/rotY/rotZ`), `scale`, `center`, `segments`, `strength` update without a
  recompile (~130 ms per 480×270 frame).
- Do not change compile-time props mid-timeline (shape `type`, `visible`, select props). Use
  `opacity`, or mount a second preset.
- Do not use simulation components in a parallel or random-seek render (state carries from frame
  to frame): `Particles`, `SmokeFill`, `ReactionDiffusion`, `TimeTrail`, `DataMosh`, `Smoke`,
  `SmokeFlow`, `InkFlow`, `FlowField`, `Boids`, `ParticleFlow`, `Liquify`, `Shatter`, cursor effects.
- Do not use auto-animate drivers on shape sub-props (their phase reads the wall clock).
- No `Text` or `Ascii`: they load Google Fonts over the network. Type stays in the DOM.
- One canvas per preset; mount lazily (a Modal chunk then compiles only its own presets). Pass one
  shared device (`opts.gpu`). Swap presets by DOM, never by `updatePreset` (swap-when-ready is async).

## Shapes and materials
- Halftone's ink and paper colours apply only to its `cmyk` style; `classic` keeps the source colours,
  so a classic halftone hook came out pale and low-contrast (a client print piece).
- 23 "shape effect" materials take the same `shape` prop: BrushedMetal, CarbonFiber, Chrome,
  Crystal*, Emboss*, Frost, Glass*, Goo, Heatmap, Hologram, Holographic, Irradiance, LightEdge,
  LiquidMetal, Nebula, Neon, Obsidian, Particles (sim), Plastic, SmokeFill (sim), ThinFilm, Voxels,
  Water (* = needs a child to refract or emboss).
- Shape types (from `SHAPE3D_TYPES` in the engine, not in llms-full): sphere3D, cube3D, torus3D,
  octahedron3D, cylinder3D, capsule3D, cone3D, pyramid3D, prism3D, ellipsoid3D, diamond3D, link3D,
  gem3D, helix3D, metaballs3D, dodecahedron3D, hemisphere3D, ribbon3D, blob3D, gyroscope3D, plus
  `svgExtrude3D` (an SDF `.bin`; the vendor's free generator is an anonymous endpoint, so build the
  field locally instead — see "Findings from a brand-mark build" below; nothing leaves the box).
- Pose: a torus's axis is +Y (rotX 0 = edge-on, rotX 90 = face-on). Every Euler angle tilts that
  axis, rotZ included, so a free spin on any axis goes edge-on; bound the angles near face-on
  (rotX 90±25, rotY and rotZ ±18 kept the LEVELS ring readable).
- Test grid of all 21 non-sim materials on one torus: `projects/lab-shaders/review/material-grid.jpg`.
  Weakest: Irradiance (35 s compile, dark), Emboss (needs a busy child to read).

## Speed and cost (SwiftShader, CPU)
- 480×270: 0.5–3 s per material frame (Irradiance 35 s first frame = compile).
- 960×540: LiquidMetal + MeshGradient ~1.5 s per frame.
- 1920×1080 on this box (2 CPU): 4–19 s per frame (simple material ~5 s; two layers in an iris or a
  filter stack ~16–19 s).
- Modal numbers: see [[lab-shaders]].

## Links
Repo `github.com/shader-effects-inc/shaders` · announcement `shaders.com/updates/shaders-is-open-source`
· HyperFrames (HeyGen) said on 2026-10-06 that it adds Shaders to HyperFrames Studio; recheck its
WebGPU render path when that ships — it may remove the need for our own capture.

## Findings from a brand-mark build
Found building a brand book. The principal rejected the extruded, turning brand mark ("a strong logo and u make it a toy"), so ask before extruding or turning a client's mark; the techniques below still hold. The approved alternative, a WebGL2 sky whose smoke wraps the flat mark, is in the brand's dossier (not in this repo).
- **svgExtrude3D without the vendor service.** The engine reads `shapeSdfUrl`: a 512 × 512 signed distance
  field, float32 (1 MB) or uint16 (`v/32767.5 − 1`), row 0 = top, units = texture widths (the grid spans
  p ∈ [−0.5, 0.5]), negative inside. Build it locally from any mask (scipy `distance_transform_edt` at 4×,
  block-mean to 512, divide by the work size) and pass it as a `data:` URL. Nothing leaves the box. The
  field loads after mount: re-seek once after ~1–4 s before the first captured frame.
- **Godrays brightness is its node `opacity`, not `intensity`** (intensity 0.035–0.3 changed little). But
  an opacity < 1 on a screen-blended Godrays INSIDE a Glass child renders nothing: use full opacity there.
- **Glass ignores its `center` for what it refracts.** At any centre but 0.5 the lens shows black. Move the
  lens with `transform.offsetX/Y` + `cutout: true`, and give every child the opposite offset so it refracts
  what is really behind it. Keep the offset non-zero (identity ↔ non-identity recompiles).
- **Engraving inks dark → paper, light → ink, both ways.** White-on-black plates need a light image; invert
  light-dominant images first (inkColor black, paperColor white).
- **Live pages in software WebGPU:** continuous rAF loops starve SwiftShader so automation never gets a
  turn. Check live pages with prefers-reduced-motion (one frame, then input only).
