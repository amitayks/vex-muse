// viewer.js - Muse splat viewer on Spark 2.3.1 + three.js r186, all vendored (no CDN).
// Modes:
//   free flight : ?file=<splat>[&cams=<cameras.json>][&up=x,y,z]
//   shot        : ?shot=<shot.json>[&t=<sec>][&still=1][&rate=1][&loop=1]
// Paths without a scheme or leading "/" or "." resolve against ?root= (default "/vol/"), the local mirror of
// Modal volume muse-splats. So a shot JSON written for modal_splat.py plays here unchanged when the PLYs exist.
import * as THREE from "three";
import { SparkRenderer, SplatMesh } from "@sparkjsdev/spark";
import { cameraAt, autoUp, cvToGlColumnMajor, lookC2w, normalize } from "./shotcam.js";

const Q = new URLSearchParams(location.search);
const ROOT = Q.get("root") ?? "/vol/";
const resolve = (p) => (/^([a-z]+:|\/|\.)/i.test(p) ? p : ROOT + p);
const num = (k, d) => (Q.has(k) ? parseFloat(Q.get(k)) : d);
const vec = (k) => (Q.has(k) ? Q.get(k).split(",").map(Number) : null);

const hud = document.getElementById("hud");
const msgEl = document.getElementById("msg");
const stage = document.getElementById("stage");
if (Q.get("hud") === "0" || Q.get("still") === "1") hud.classList.add("off");
const say = (s, ms = 2500) => { msgEl.textContent = s; msgEl.style.display = "block"; clearTimeout(say._t); say._t = setTimeout(() => (msgEl.style.display = "none"), ms); };

// ---------------------------------------------------------------- renderer
const still = Q.get("still") === "1";
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: still, powerPreference: "high-performance" });
renderer.setPixelRatio(num("dpr", still ? 1 : window.devicePixelRatio));
stage.appendChild(renderer.domElement);
renderer.domElement.tabIndex = 0;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, 16 / 9, 0.01, 10000);
const spark = new SparkRenderer({ renderer });
scene.add(spark);

let fixed = null; // {w,h} when the output size is fixed (shot mode or ?w&h)
function layout() {
  const ww = window.innerWidth, wh = window.innerHeight;
  if (fixed) {
    const s = still ? 1 : Math.min(ww / fixed.w, wh / fixed.h);
    renderer.setSize(Math.round(fixed.w * s), Math.round(fixed.h * s));
    camera.aspect = fixed.w / fixed.h;
  } else {
    renderer.setSize(ww, wh);
    camera.aspect = ww / wh;
  }
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", layout);

// ---------------------------------------------------------------- fps meter (rAF frame times)
const fpsm = { times: [], last: 0, window: [], since: performance.now() };
function fpsTick(now) {
  if (fpsm.last) {
    const dt = now - fpsm.last;
    fpsm.times.push(dt);
    fpsm.window.push([now, dt]);
    while (fpsm.window.length && now - fpsm.window[0][0] > 1000) fpsm.window.shift();
  }
  fpsm.last = now;
}
function fpsStats() {
  const t = fpsm.times.slice().sort((a, b) => a - b);
  if (!t.length) return null;
  const sum = t.reduce((a, b) => a + b, 0);
  const q = (p) => t[Math.min(t.length - 1, Math.floor(p * t.length))];
  return {
    frames: t.length, seconds: +(sum / 1000).toFixed(2), mean_fps: +((1000 * t.length) / sum).toFixed(1),
    median_fps: +(1000 / q(0.5)).toFixed(1), p1_low_fps: +(1000 / q(0.99)).toFixed(1),
    worst_ms: +t[t.length - 1].toFixed(1),
    buffer: [renderer.domElement.width, renderer.domElement.height], dpr: renderer.getPixelRatio(),
  };
}
const fpsNow = () => {
  const w = fpsm.window; if (w.length < 2) return 0;
  return (1000 * w.length) / w.reduce((a, b) => a + b[1], 0);
};

// ---------------------------------------------------------------- loading
const meshes = [];
let totalSplats = 0, loadMs = 0;
async function loadSplat({ url, bytes, name, xform }) {
  const t0 = performance.now();
  const opts = bytes ? { fileBytes: bytes, fileName: name } : { url };
  const mesh = new SplatMesh(opts);
  if (xform) new THREE.Matrix4().set(...xform).decompose(mesh.position, mesh.quaternion, mesh.scale);
  scene.add(mesh);
  await mesh.initialized;
  loadMs += performance.now() - t0;
  totalSplats += mesh.numSplats ?? 0;
  meshes.push(mesh);
  return mesh;
}
async function getJson(p) {
  const r = await fetch(resolve(p), { cache: "no-store" });
  if (!r.ok) throw new Error(`${p}: HTTP ${r.status}`);
  return r.json();
}

// ---------------------------------------------------------------- free flight
let UP = [0, -1, 0];         // world up of the PLY frame (OpenCV-style PLYs are y-down)
let cams = null;              // cameras.json (training cameras in the PLY frame)
let camIdx = 0;
const fly = { pos: new THREE.Vector3(), fwd: new THREE.Vector3(0, 0, 1), speed: 1, keys: new Set(), drag: null, fov: 50, roll: 0 };
const upV = () => new THREE.Vector3(...UP);

function setPose(pos, look, fov = fly.fov) {
  fly.pos.set(...pos);
  fly.fwd.set(look[0] - pos[0], look[1] - pos[1], look[2] - pos[2]).normalize();
  fly.fov = fov;
}
function poseFromC2w(c2w, fov) {
  const p = [c2w[0][3], c2w[1][3], c2w[2][3]], f = [c2w[0][2], c2w[1][2], c2w[2][2]];
  setPose(p, [p[0] + f[0], p[1] + f[1], p[2] + f[2]], fov);
}
function camFovY(c) { return (2 * Math.atan(c.h / 2 / c.K[1][1]) * 180) / Math.PI; }
function gotoCam(i) {
  if (!cams?.cams?.length) return;
  camIdx = (i + cams.cams.length) % cams.cams.length;
  const c = cams.cams[camIdx];
  poseFromC2w(c.c2w, camFovY(c));
  say(`training camera ${camIdx + 1}/${cams.cams.length}  ${c.name}`);
}
function applyFly(dt) {
  const U = upV();
  const right = new THREE.Vector3().crossVectors(fly.fwd, U).normalize();
  let s = fly.speed * dt * (fly.keys.has("ShiftLeft") || fly.keys.has("ShiftRight") ? 4 : 1) * (fly.keys.has("AltLeft") ? 0.25 : 1);
  const m = new THREE.Vector3();
  if (fly.keys.has("KeyW")) m.add(fly.fwd);
  if (fly.keys.has("KeyS")) m.sub(fly.fwd);
  if (fly.keys.has("KeyD")) m.add(right);
  if (fly.keys.has("KeyA")) m.sub(right);
  if (fly.keys.has("KeyE") || fly.keys.has("Space")) m.add(U);
  if (fly.keys.has("KeyQ") || fly.keys.has("KeyC")) m.sub(U);
  if (m.lengthSq() > 0) fly.pos.addScaledVector(m.normalize(), s);
  const look = 1.6 * dt;
  if (fly.keys.has("ArrowLeft")) turn(look, 0);
  if (fly.keys.has("ArrowRight")) turn(-look, 0);
  if (fly.keys.has("ArrowUp")) turn(0, look);
  if (fly.keys.has("ArrowDown")) turn(0, -look);
  const c2w = lookC2w(fly.pos.toArray(), fly.pos.clone().add(fly.fwd).toArray(), UP, fly.roll);
  setCameraCv(c2w, fly.fov);
}
function turn(yaw, pitch) {
  const U = upV();
  fly.fwd.applyAxisAngle(U, yaw);
  const right = new THREE.Vector3().crossVectors(fly.fwd, U).normalize();
  const f2 = fly.fwd.clone().applyAxisAngle(right, pitch);
  if (Math.abs(f2.dot(U)) < 0.985) fly.fwd.copy(f2);
  fly.fwd.normalize();
}
function setCameraCv(c2w, fovDeg) {
  const m = new THREE.Matrix4().fromArray(cvToGlColumnMajor(c2w));
  m.decompose(camera.position, camera.quaternion, camera.scale);
  if (camera.fov !== fovDeg) { camera.fov = fovDeg; camera.updateProjectionMatrix(); }
  camera.updateMatrixWorld(true);
}

// key capture -> shot JSON (same schema as modal_splat.py)
const shotKeys = [];
function addKey() {
  const t = shotKeys.length ? shotKeys[shotKeys.length - 1].t + 2 : 0;
  const r = (v) => +v.toFixed(4);
  shotKeys.push({ t, pos: fly.pos.toArray().map(r), look: fly.pos.clone().add(fly.fwd).toArray().map(r), fov: r(fly.fov), roll: fly.roll });
  say(`key ${shotKeys.length} at t=${t}s`);
}
function downloadShot() {
  if (!shotKeys.length) return say("no keys yet (press K)");
  const layer = file ? [{ ply: file, xform: null, effects: [] }] : [];
  const shot = {
    width: 1920, height: 1080, fps: 30, duration: shotKeys[shotKeys.length - 1].t || 1, bg: [0, 0, 0],
    lens: { samples: 8, shutter: 0.5, aperture: 0.0, focus: "look" },
    camera: { type: "keys", up: UP.map((v) => +v.toFixed(6)), keys: shotKeys }, layers: layer,
  };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(shot, null, 1)], { type: "application/json" }));
  a.download = "shot.json"; a.click();
  console.log("SHOT", JSON.stringify(shot));
}

// ---------------------------------------------------------------- input
const el = renderer.domElement;
el.addEventListener("pointerdown", (e) => { el.focus(); fly.drag = [e.clientX, e.clientY]; el.setPointerCapture(e.pointerId); if (shot && !freeInShot) { freeInShot = true; grabShotPose(); } });
el.addEventListener("pointermove", (e) => {
  if (!fly.drag) return;
  const k = (fly.fov * Math.PI) / 180 / el.clientHeight; // one screen height = one fov
  turn(-(e.clientX - fly.drag[0]) * k, -(e.clientY - fly.drag[1]) * k);
  fly.drag = [e.clientX, e.clientY];
});
el.addEventListener("pointerup", () => (fly.drag = null));
el.addEventListener("wheel", (e) => { e.preventDefault(); fly.speed *= Math.exp(-e.deltaY * 0.0015); say(`speed ${fly.speed.toPrecision(3)} /s`, 900); }, { passive: false });
window.addEventListener("keydown", (e) => {
  fly.keys.add(e.code);
  if (e.repeat) return;
  if (e.code === "KeyH") hud.classList.toggle("off");
  if (e.code === "KeyR") reset();
  if (e.code === "BracketRight") gotoCam(camIdx + 1);
  if (e.code === "BracketLeft") gotoCam(camIdx - 1);
  if (e.code === "KeyK") addKey();
  if (e.code === "KeyX") { shotKeys.length = 0; say("keys cleared"); }
  if (e.code === "KeyP") downloadShot();
  if (e.code === "KeyZ") { fly.roll += e.shiftKey ? 5 : -5; }
  if (e.code === "Minus") { fly.fov = Math.min(120, fly.fov + 2); }
  if (e.code === "Equal") { fly.fov = Math.max(5, fly.fov - 2); }
  if (e.code === "KeyF" && shot) { freeInShot = !freeInShot; if (freeInShot) grabShotPose(); }
  if (shot && e.code === "Space" && !freeInShot) { playing = !playing; e.preventDefault(); }
  if (shot && !freeInShot && (e.code === "Comma" || e.code === "Period")) { playing = false; shotT += (e.code === "Period" ? 1 : -1) / (shot.fps || 30); }
  if (shot && e.code === "Home") { shotT = 0; }
});
window.addEventListener("keyup", (e) => fly.keys.delete(e.code));
window.addEventListener("blur", () => fly.keys.clear());

// drag & drop a local file
window.addEventListener("dragover", (e) => { e.preventDefault(); document.getElementById("drop").style.display = "flex"; });
window.addEventListener("dragleave", () => (document.getElementById("drop").style.display = "none"));
window.addEventListener("drop", async (e) => {
  e.preventDefault(); document.getElementById("drop").style.display = "none";
  const f = e.dataTransfer.files[0]; if (!f) return;
  for (const m of meshes.splice(0)) { scene.remove(m); m.dispose(); }
  totalSplats = 0; loadMs = 0; file = null;
  say(`loading ${f.name}…`, 60000);
  await loadSplat({ bytes: new Uint8Array(await f.arrayBuffer()), name: f.name });
  frameScene(); say(`${f.name}: ${totalSplats.toLocaleString()} splats`);
});

// ---------------------------------------------------------------- scene framing
let start = null;
function frameScene() {
  if (cams?.cams?.length) { gotoCam(0); start = { pos: fly.pos.clone(), fwd: fly.fwd.clone(), fov: fly.fov }; return; }
  const box = new THREE.Box3();
  for (const m of meshes) box.union(m.getBoundingBox(true).applyMatrix4(m.matrixWorld));
  const c = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3()).length();
  const U = upV(), side = Math.abs(U.x) > 0.9 ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(1, 0, 0);
  const back = new THREE.Vector3().crossVectors(U, side).normalize();
  const p = c.clone().addScaledVector(back, size * 0.6).addScaledVector(U, size * 0.15);
  setPose(p.toArray(), c.toArray(), 50);
  fly.speed = size * 0.08;
  start = { pos: fly.pos.clone(), fwd: fly.fwd.clone(), fov: fly.fov };
}
function reset() { if (start) { fly.pos.copy(start.pos); fly.fwd.copy(start.fwd); fly.fov = start.fov; fly.roll = 0; } }

// ---------------------------------------------------------------- shot playback
let shot = null, shotUp = [0, 0, 1], shotT = 0, playing = true, freeInShot = false;
const fadeFx = [];
function grabShotPose() {
  const { c2w, fov } = cameraAt(shot.camera, shotT, shotUp);
  UP = shotUp; poseFromC2w(c2w, fov); fly.roll = 0;
}
async function loadShot(path) {
  shot = await getJson(path);
  const cam = shot.camera;
  if (cam.type === "keys") {
    const up = cam.up ?? [0, 0, 1];
    if (typeof up === "string" && up.startsWith("auto:")) {
      cams = await getJson(`runs/${up.slice(5)}/cameras.json`);
      shotUp = autoUp(cams);
    } else shotUp = normalize(up);
  }
  UP = shotUp;
  fixed = { w: shot.width ?? 1920, h: shot.height ?? 1080 };
  const bg = shot.bg ?? [0, 0, 0];
  renderer.setClearColor(new THREE.Color(bg[0], bg[1], bg[2]), 1);
  layout();
  const warn = [];
  for (const L of shot.layers ?? []) {
    const mesh = await loadSplat({ url: resolve(L.ply), xform: L.xform });
    for (const fx of L.effects ?? []) {
      if (fx.type === "fade") fadeFx.push([mesh, fx]); else warn.push(`${fx.type} (render-only)`);
    }
    if (L.crop) warn.push("crop (render-only)");
  }
  if (warn.length) say("viewer preview skips: " + [...new Set(warn)].join(", "), 6000);
  if (Q.has("t")) { shotT = num("t", 0); playing = false; }
}
function applyShot() {
  const dur = shot.duration ?? 8;
  const { c2w, fov } = cameraAt(shot.camera, shotT, shotUp);
  setCameraCv(c2w, fov);
  for (const [mesh, fx] of fadeFx) {
    const x = Math.min(Math.max((shotT - fx.t0) / Math.max(fx.t1 - fx.t0, 1e-9), 0), 1);
    const from = fx.from ?? 0, to = fx.to ?? 1;
    mesh.opacity = from + (to - from) * x;
  }
  return dur;
}

// ---------------------------------------------------------------- HUD
function drawHud(mode) {
  if (hud.classList.contains("off")) return;
  const p = camera.position, f = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  const lines = [
    `Spark 2.3.1 · three r186 · ${mode}`,
    `fps ${fpsNow().toFixed(1)}   buffer ${renderer.domElement.width}x${renderer.domElement.height}`,
    `splats ${totalSplats.toLocaleString()}   load ${(loadMs / 1000).toFixed(1)} s`,
    `pos  ${p.toArray().map((v) => v.toFixed(3)).join(", ")}`,
    `fwd  ${f.toArray().map((v) => v.toFixed(3)).join(", ")}   fov ${camera.fov.toFixed(1)}`,
    `up   ${UP.map((v) => v.toFixed(3)).join(", ")}`,
  ];
  if (shot && !freeInShot) lines.push(`t ${shotT.toFixed(3)} / ${shot.duration ?? 8} s  ${playing ? "▶" : "❚❚"}  (space · , . · Home · F free)`);
  else lines.push(`WASD move · E/Q up/down · drag look · wheel speed (${fly.speed.toPrecision(3)}/s)`,
    `shift fast · R reset · [ ] train cams · K key (${shotKeys.length}) · P save shot · H hud`);
  hud.textContent = lines.join("\n");
}

// ---------------------------------------------------------------- main loop
let file = Q.get("file");
let lastNow = performance.now();
let stillFrames = 0;
window.__viewer = {
  THREE, camera, renderer, spark, scene, meshes, fly,
  fpsStats, resetFps: () => { fpsm.times = []; fpsm.last = 0; },
  setTime: (t) => { shotT = t; playing = false; stillFrames = 0; window.__still_ready = false; },
  get splats() { return totalSplats; }, get loadMs() { return loadMs; },
  ready: false,
};

async function main() {
  layout();
  try {
    if (Q.has("shot")) await loadShot(Q.get("shot"));
    else {
      if (Q.has("cams")) cams = await getJson(Q.get("cams"));
      UP = vec("up") ?? (cams ? autoUp(cams) : UP);
      if (Q.has("w") && Q.has("h")) { fixed = { w: num("w", 1920), h: num("h", 1080) }; layout(); }
      if (file) { say(`loading ${file}…`, 120000); await loadSplat({ url: resolve(file) }); say(`${totalSplats.toLocaleString()} splats in ${(loadMs / 1000).toFixed(1)} s`); }
      else say("no ?file= given: drop a splat file here", 10000);
      frameScene();
      if (cams && meshes.length) {
        // speed from the size of the capture: 15 % of the mean camera distance to the camera centroid, per second
        const P = cams.cams.map((c) => new THREE.Vector3(c.c2w[0][3], c.c2w[1][3], c.c2w[2][3]));
        const ctr = P.reduce((a, b) => a.add(b), new THREE.Vector3()).multiplyScalar(1 / P.length);
        fly.speed = (P.reduce((a, b) => a + b.distanceTo(ctr), 0) / P.length) * 0.15;
      }
      if (Q.has("speed")) fly.speed = num("speed", fly.speed);
    }
  } catch (err) {
    hud.classList.remove("off"); hud.textContent = "ERROR\n" + (err?.stack ?? err); console.error(err); return;
  }
  window.__viewer.ready = true;
  renderer.setAnimationLoop((now) => {
    const dt = Math.min((now - lastNow) / 1000, 0.1); lastNow = now;
    fpsTick(now);
    let mode = "free flight";
    if (shot && !freeInShot) {
      if (playing) {
        shotT += dt * num("rate", 1);
        const dur = shot.duration ?? 8;
        if (shotT > dur) shotT = Q.get("loop") === "0" ? dur : shotT % dur;
      }
      applyShot();
      mode = `shot ${Q.get("shot")}`;
    } else applyFly(dt);
    renderer.render(scene, camera);
    if (still && ++stillFrames === 90) window.__still_ready = true; // sort settled
    drawHud(mode);
  });
}
main();
