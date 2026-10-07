# How the driver makes a WebGPU layer frame-exact

## The problem
- The public `createShader` API runs its own requestAnimationFrame clock: wall-clock deltas, gated at
  1–60 fps, clamped to 0.1 s. It exposes only pause/resume, and it starts telemetry beacons.
- A video frame must be a pure function of t, captured in any order by parallel workers.

## The driver (`assets/driver/hf-shaders.js` → `hf-shaders.iife.js`, global `HFShaders`)
- `mount(canvas, preset, {width, height, gpu?, colorSpace?, toneMapping?})` registers the same node
  tree as `createShader` on the engine renderer (`shaderRendererGPU`), with no telemetry and no
  observers. It returns `{ready, seek(t), set(id, props), elapsed(), swallowed(), destroy()}`.
- `seek(T)` reads the engine's elapsed time and renders one synthetic frame with `dt = T − elapsed`.
  Elapsed time and every per-node `_animTime` (= speed × Σdt) are linear in dt, so a signed dt lands
  exactly on T from any previous time. That is why `speed` must stay constant.
- Stray renders: every prop update or structural change calls the engine's `requestRender()`, which
  queues one rAF render with a wall-clock delta. A screenshot caught one (a frame 0.03 s late). During
  the synchronous mount, the driver hands the engine a rAF id that never fires; `requestRender()`
  then always sees a pending frame and returns early. `swallowed()` must be ≥ 1 after mount.
- `ready` compiles the pipelines (renders dt = 0 until the first composition draws), then seeks to 0.
- `bindToHyperFrames(layers, frame)` listens to the HyperFrames runtime's `hf-seek` window event
  `{time, waitUntil(promise)}`; the runtime awaits those promises before each capture. It also sets
  `window.__hfShadersSeek(t)`, which the capture scripts await after a direct timeline seek.

## Why our own capture
- On a GPU-less host, only SwiftShader on Vulkan presents a WebGPU canvas (`scripts/_chrome.mjs`).
- `hyperframes render` / `snapshot` launch software GL without WebGPU, or, with
  `data-requires-webgpu`, reject every fallback adapter (SwiftShader is one).
- So stills come from `scripts/webgpu_snap.mjs`, and renders from
  `render-review/scripts/modal_hf.py --webgpu`. Both seek the GSAP timeline, then await
  `__hfShadersSeek(t)`, then screenshot.

## Proof
`scripts/check_determinism.mjs` hashes N frames in order, shuffled, and again after 2.5 s idle. All
must match, and at least 2 distinct frames must exist (catches a blank canvas). Measured in the
first lab: before the rAF fix, 1 of 5 frames differed (it drew t + 0.03 s); after it, 0 of 11.
