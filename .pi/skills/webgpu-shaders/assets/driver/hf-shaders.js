// hf-shaders — shaders (MIT, Shader Effects Inc.) as a frame-exact, seekable WebGPU layer.
// pin: shaders@4.0.0  (rebuild: scripts/build_driver.sh [version])
//
// Why this file exists: the public `createShader` API runs its own requestAnimationFrame clock
// (wall-clock deltas, 1-60 fps gating) and exposes only pause/resume. A video frame must be a pure
// function of t. The engine's renderer has `renderSyntheticFrame(dt)` and a readable elapsed time,
// so this driver mounts the same component tree (logic copied from shaders' dist/js/createShader.js) and
// seeks to an ABSOLUTE time: dt = T - renderer elapsed. Stray wall-clock renders (initialize, rAF
// requestRender) only shift the elapsed time, and the next seek corrects it.
//
// Rules for frame-exact output (skill webgpu-shaders, SKILL.md):
//  - keep every `speed` prop constant (per-node _animTime = speed x elapsed only if speed never changes);
//  - animate any other prop per frame with `set()` (pure function of t);
//  - never use simulation components (ReactionDiffusion, TimeTrail, DataMosh, Smoke, InkFlow, FlowField,
//    Boids, ParticleFlow, ... = state carried frame to frame) in a parallel or random-seek render;
//  - never change compile-time props mid-timeline (`visible`, shape type, select props) -> use opacity;
//  - no Text component (it loads Google Fonts over the network); type stays in the DOM.
import {
  createGpuUniformsMap, debugError, getRegisteredShader, resolveBoundingBox,
  rootPassthrough, shaderRendererGPU, getWebGPUSupport, getNaturalSize, onNaturalSizeChange,
} from '../node_modules/shaders/dist/core/index.js';

// Image media load asynchronously (fetch -> createImageBitmap) after the first frames, so `ready` must
// wait for them or the first captured frames show an empty texture. The engine registers each loaded
// image's natural size under its url; we wait for every ImageTexture url in the preset. Use data: URLs
// (fetch cannot read file:// pages' files, and remote URLs make a render depend on the network).
const MEDIA_TYPES = new Set(['ImageTexture']);
function mediaUrls(components, out = []) {
  for (const c of components || []) {
    if (MEDIA_TYPES.has(c.type) && c.props?.url) out.push(c.props.url);
    mediaUrls(c.children, out);
  }
  return out;
}
function waitMedia(urls, timeoutMs) {
  const pending = () => urls.filter((u) => !getNaturalSize(u));
  if (!pending().length) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const off = onNaturalSizeChange(() => { if (!pending().length) { off(); clearTimeout(timer); resolve(); } });
    const timer = setTimeout(() => { off(); reject(new Error(`[hf-shaders] media not loaded after ${timeoutMs} ms: ${pending().map((u) => u.slice(0, 60)).join(', ')}`)); }, timeoutMs);
  });
}
import { getAllShaders } from '../node_modules/shaders/dist/core/registry.js';

const METADATA_PROPS = new Set(['opacity', 'blendMode', 'visible', 'transform', 'boundingBox',
  'maskSource', 'maskType', 'flow', 'absolute']);

function isPropDriver(v) {
  if (typeof v !== 'object' || v === null || !('type' in v)) return false;
  return v.type === 'map' || v.type === 'mouse' || v.type === 'mouse-position' || v.type === 'auto-animate';
}

let REGISTRY = null;
function registry(custom = []) {
  if (!REGISTRY) {
    REGISTRY = new Map();
    for (const s of getAllShaders()) {
      REGISTRY.set(s.definition.name, s.definition);
      for (const old of s.definition.deprecatedNames ?? []) REGISTRY.set(old, s.definition);
    }
  }
  for (const c of custom) REGISTRY.set(c.name, c);
  return REGISTRY;
}

function registerComponent(reg, renderer, entries, component, parentId, renderOrder) {
  const def = reg.get(component.type) ?? getRegisteredShader(component.type);
  if (!def) throw new Error(`[hf-shaders] unknown component type: ${component.type}`);
  if (!component.id) throw new Error(`[hf-shaders] every component needs an id (got ${component.type})`);
  const nodeId = component.id;
  const maps = {};
  for (const [k, v] of Object.entries(component.props || {})) {
    if (!METADATA_PROPS.has(k) && Object.prototype.hasOwnProperty.call(def.props, k) && isPropDriver(v)) maps[k] = v;
  }
  const uniforms = createGpuUniformsMap(def, Object.fromEntries(Object.entries(def.props).map(([k, cfg]) => {
    const v = component.props?.[k] !== undefined ? component.props[k] : cfg.default;
    return [k, isPropDriver(v) ? cfg.default : v];
  })), nodeId);
  const p = component.props || {};
  const metadata = {
    blendMode: p.blendMode || 'normal',
    opacity: p.opacity,
    visible: p.visible,
    renderOrder,
    id: component.id,
    maps: Object.keys(maps).length ? { ...maps } : undefined,
    mask: p.maskSource ? { source: p.maskSource, type: p.maskType || 'alpha' } : undefined,
    transform: p.transform ? { offsetX: 0, offsetY: 0, rotation: 0, scale: 1, anchorX: 0.5, anchorY: 0.5,
      edges: 'transparent', ...p.transform } : undefined,
    boundingBox: resolveBoundingBox(p.boundingBox),
    flow: p.flow,
    absolute: p.absolute,
  };
  renderer.registerNode(nodeId, def.fragment, parentId, metadata, uniforms, def);
  entries.set(nodeId, { def, component, live: { ...p } });
  component.children?.forEach((child, i) => registerComponent(reg, renderer, entries, child, nodeId, i));
}

/**
 * Mount a Shaders preset ({components:[...]}, every component with an `id`) on a canvas.
 * Returns { ready, seek(t), set(id, props), time(), renderer, destroy() }.
 */
export async function mount(canvas, preset, opts = {}) {
  const width = opts.width ?? canvas.clientWidth ?? canvas.width;
  const height = opts.height ?? canvas.clientHeight ?? canvas.height;
  const dpr = window.devicePixelRatio || 1;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  // A canvas hidden at mount (display:none) measures 0; the engine then falls back to the canvas
  // attributes (300x150), and size-normalised effects (Dither cells, Halftone dots) come out ~3x coarse.
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const reg = registry(opts.components);
  const renderer = shaderRendererGPU();
  let failure = null;
  let markReady;
  const firstFrame = new Promise((r) => { markReady = r; });
  renderer.setOnReady(() => markReady());
  renderer.setOnUnavailable((reason) => { failure = reason; markReady(); });
  await renderer.initialize({
    canvas, resizeTarget: canvas, observeElement: false,
    colorSpace: opts.colorSpace, toneMapping: opts.toneMapping, gpu: opts.gpu,
  });
  renderer.stopAnimation();
  // Block stray renders for good. Every prop update or structural change calls the engine's
  // requestRender(), which schedules ONE requestAnimationFrame render with a wall-clock delta
  // (measured: a 16 s SwiftShader frame got +0.03 s and the screenshot caught it). requestRender
  // returns early while its pending id is non-null, so we hand it an id that never fires: swap rAF
  // for a stub during this synchronous block only (no other code can run inside it).
  const realRaf = window.requestAnimationFrame;
  let swallowed = 0;
  window.requestAnimationFrame = () => { swallowed += 1; return 0x7ffffff0 + swallowed; };
  const entries = new Map();
  try {
    renderer.registerNode('shader-root', rootPassthrough.fragment, null, null, {}, rootPassthrough);
    preset.components.forEach((c, i) => registerComponent(reg, renderer, entries, structuredClone(c), 'shader-root', i));
    // renderer.resize() applies on the next requestAnimationFrame (stubbed here, and absent in some
    // capture modes): set the size synchronously through the recording-resolution hook instead.
    renderer.beginRecordingResolution(width, height, dpr);
    renderer.stopAnimation();
  } finally {
    window.requestAnimationFrame = realRaf;
  }
  if (swallowed === 0) debugError('[hf-shaders] no requestRender was swallowed: stray wall-clock renders stay possible');

  const elapsed = () => renderer.__testing?.getFrameDiagnostics?.().globalElapsedTime ?? NaN;
  let target = 0;

  async function seek(t) {
    if (failure) throw new Error(`[hf-shaders] GPU unavailable: ${failure}`);
    target = t;
    const now = elapsed();
    const dt = Number.isFinite(now) ? t - now : 0;
    await renderer.renderSyntheticFrame(dt);
  }

  function set(id, props) {
    const e = entries.get(id);
    if (!e) throw new Error(`[hf-shaders] unknown id ${id}`);
    for (const [k, v] of Object.entries(props)) {
      if (METADATA_PROPS.has(k)) {
        if (k === 'transform') renderer.updateNodeMetadata(id, { transform: { offsetX: 0, offsetY: 0, rotation: 0,
          scale: 1, anchorX: 0.5, anchorY: 0.5, edges: 'transparent', ...e.live.transform, ...v } });
        else if (k === 'boundingBox') renderer.updateNodeMetadata(id, { boundingBox: resolveBoundingBox(v) });
        else if (k === 'maskSource') renderer.updateNodeMetadata(id, { mask: v ? { source: v, type: props.maskType || e.live.maskType || 'alpha' } : undefined });
        else if (k !== 'maskType') renderer.updateNodeMetadata(id, { [k]: v });
        e.live[k] = k === 'transform' ? { ...e.live.transform, ...v } : v;
      } else if (Object.prototype.hasOwnProperty.call(e.def.props, k)) {
        if (/^speed$|Speed$/.test(k) && e.live[k] !== undefined && e.live[k] !== v) {
          debugError(`[hf-shaders] ${id}.${k} changed mid-timeline: animated time stops being a pure function of t`);
        }
        renderer.updateUniformValue(id, k, v);
        e.live[k] = v;
      }
    }
  }

  // Warm-up: compile pipelines and draw once, wait for image media, then pin the clock at 0.
  const urls = mediaUrls(preset.components);
  const warm = (async () => {
    for (let i = 0; i < 200 && !failure; i++) {
      await renderer.renderSyntheticFrame(0);
      const ok = await Promise.race([firstFrame.then(() => true), new Promise((r) => setTimeout(() => r(false), 25))]);
      if (ok) break;
    }
    if (failure) throw new Error(`[hf-shaders] GPU unavailable: ${failure}`);
    if (urls.length) {
      await waitMedia(urls, opts.mediaTimeoutMs ?? 60000);
      await renderer.renderSyntheticFrame(0); // uploads happen on the frame after the decode
    }
    await seek(0);
  })();

  return {
    ready: warm,
    seek,
    set,
    time: () => target,
    elapsed,
    renderer,
    failure: () => failure,
    swallowed: () => swallowed,
    destroy: () => renderer.cleanup(),
  };
}

/**
 * Drive one or more mounted layers from HyperFrames' seek protocol.
 * HyperFrames dispatches `hf-seek` {time, waitUntil} on window for every captured frame and awaits
 * the promises (window.__hfWaitForSeekCompletion) before the screenshot.
 * `layers` = one layer or an array; each may still be the Promise from mount(), so this can be called
 * synchronously at load (before the first seek arrives).
 * `frame(t, layers)` is the comp's own per-frame prop function (pure function of t, calls layer.set);
 * it runs before every seek. If it returns an array of layers, only those render (hidden canvases cost
 * nothing; each seek is absolute, so a layer that skipped frames is still exact when it shows again). Also exposes window.__hfShadersSeek(t) for capture scripts that seek the
 * GSAP timeline directly (render-review modal_hf.py --webgpu, webgpu_snap.mjs, check_determinism.mjs).
 */
export function bindToHyperFrames(layers, frame) {
  const all = (Array.isArray(layers) ? layers : [layers]).map((l) => Promise.resolve(l));
  let chain = Promise.resolve();
  const run = (t) => {
    chain = chain.then(async () => {
      const ls = await Promise.all(all);
      await Promise.all(ls.map((l) => l.ready));
      // frame may return the layers visible at t (array of layers): only those render this frame.
      const which = frame?.(t, ls);
      for (const l of Array.isArray(which) ? which : ls) await l.seek(t);
    });
    return chain;
  };
  window.addEventListener('hf-seek', (e) => {
    const t = Number(e.detail?.time) || 0;
    e.detail?.waitUntil?.(run(t));
  });
  window.__hfShadersSeek = run;
  window.__hfShadersReady = Promise.all(all).then((ls) => Promise.all(ls.map((l) => l.ready)));
  return run;
}

export { getWebGPUSupport };
