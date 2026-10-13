// record_flight.mjs - 10 s free flight in the Spark viewer, driven by real input events (CDP Input.*:
// held W/A/S/D/E/Q keys + mouse drags), screen-recorded with macOS screencapture, with fps stats.
// node tools/record_flight.mjs <url> <out.mov|-> <stats.json> [w h]
import { spawn, execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { launch, sleep } from "./cdp.mjs";

const [url, outMov, statsPath, W = "1280", H = "720"] = process.argv.slice(2);
const SIGN = +(process.env.YAW_SIGN ?? 1);
const w = +W, h = +H;
let front = "";
try { front = execFileSync("osascript", ["-e", 'tell application "System Events" to get name of first application process whose frontmost is true']).toString().trim(); } catch {}

const c = await launch({ headless: process.env.HEADLESS === "1", width: w, height: h + 28, x: 40, y: 60, port: 9335, app: url });
const stats = { url, front_before: front };
try {
  await c.waitFor("window.__viewer && window.__viewer.ready", 240000);
  await sleep(3000);
  const geo = await c.evaluate("({sx:window.screenX, sy:window.screenY, oh:window.outerHeight, ih:window.innerHeight, iw:window.innerWidth, dpr:devicePixelRatio})");
  const rect = [geo.sx, geo.sy + (geo.oh - geo.ih), geo.iw, geo.ih];
  stats.rect_points = rect; stats.dpr = geo.dpr;
  const cx = Math.round(geo.iw / 2), cy = Math.round(geo.ih / 2);
  let rec = null;
  if (outMov !== "-") {
    rec = spawn("screencapture", ["-x", "-v", "-V", "11", `-R${rect.join(",")}`, outMov], { stdio: "ignore" });
    await sleep(700); // recorder warm-up
  }
  await c.evaluate("__viewer.resetFps()");
  // flight plan: [t0, t1, keys[], drag px/s (dx, dy)]
  // orbit-like flight around the table: strafe while yawing toward it, rise, push in, pull out
  const plan = [
    [0.0, 2.0, ["KeyW"], [0, -10]],
    [2.0, 4.6, ["KeyD"], [-SIGN * 150, 0]],
    [4.6, 6.2, ["KeyD", "KeyE"], [-SIGN * 150, 30]],
    [6.2, 8.0, ["KeyW", "KeyD"], [-SIGN * 120, 0]],
    [8.0, 10.0, ["KeyS", "KeyA"], [SIGN * 60, -15]],
  ];
  const keyName = (code) => code.replace("Key", "").toLowerCase();
  const t0 = Date.now(); let held = new Set(); let mx = cx, my = cy;
  await c.mouse("mouseMoved", mx, my, 0);
  await c.mouse("mousePressed", mx, my, 1);
  while (true) {
    const t = (Date.now() - t0) / 1000;
    if (t >= 10) break;
    const seg = plan.find((p) => t >= p[0] && t < p[1]) ?? plan[plan.length - 1];
    const want = new Set(seg[2]);
    for (const k of held) if (!want.has(k)) await c.key("keyUp", k, keyName(k));
    for (const k of want) if (!held.has(k)) await c.key("keyDown", k, keyName(k));
    held = want;
    mx += seg[3][0] / 60; my += seg[3][1] / 60;
    await c.mouse("mouseMoved", Math.round(mx), Math.round(my), 1);
    if (process.env.SNAP && Math.floor(t * 2) !== (globalThis.__lastSnap ?? -1)) { globalThis.__lastSnap = Math.floor(t * 2); if (globalThis.__lastSnap % 4 === 0) await c.screenshot(`${process.env.SNAP}/snap_${globalThis.__lastSnap / 2}s.png`); }
    await sleep(16);
  }
  for (const k of held) await c.key("keyUp", k, keyName(k));
  await c.mouse("mouseReleased", Math.round(mx), Math.round(my), 0);
  stats.fps = await c.evaluate("__viewer.fpsStats()");
  stats.splats = await c.evaluate("__viewer.splats");
  stats.load_s = +(await c.evaluate("__viewer.loadMs") / 1000).toFixed(2);
  stats.gpu = await c.evaluate("(()=>{const gl=__viewer.renderer.getContext();const e=gl.getExtension('WEBGL_debug_renderer_info');return e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):'?'})()");
  stats.recording = outMov !== "-";
  if (rec) await new Promise((r) => rec.on("exit", r));
  stats.errors = c.logs.filter((l) => /error|exception/i.test(l)).slice(-5);
} finally {
  await c.close();
  if (front && !/switcher|loginwindow/i.test(front) && process.env.HEADLESS !== "1") { try { execFileSync("osascript", ["-e", `tell application "${front}" to activate`]); } catch {} }
}
writeFileSync(statsPath, JSON.stringify(stats, null, 1));
console.log(JSON.stringify(stats));
