// bench_headful.mjs - on-screen fps of a shot (real display, vsync), drawing buffer = w x h at the display's dpr.
// node tools/bench_headful.mjs <shot rel vol> <buffer w> <buffer h> <out.json>
import { writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { launch, sleep } from "./cdp.mjs";
const [shot, W, H, out] = process.argv.slice(2);
let front = ""; try { front = execFileSync("osascript", ["-e", 'tell application "System Events" to get name of first application process whose frontmost is true']).toString().trim(); } catch {}
const c = await launch({ headless: false, width: +W / 2, height: +H / 2 + 28, x: 40, y: 60, port: 9337, app: `http://127.0.0.1:8765/?shot=${shot}` });
try {
  await c.waitFor("window.__viewer && window.__viewer.ready", 240000);
  await sleep(3000);
  await c.evaluate("__viewer.resetFps()");
  await sleep(10000);
  const r = { shot, mode: "headful, display vsync", fps: await c.evaluate("__viewer.fpsStats()"), splats: await c.evaluate("__viewer.splats"),
    errors: c.logs.filter((l) => /error|exception/i.test(l)).slice(-5) };
  writeFileSync(out, JSON.stringify(r, null, 1)); console.log(JSON.stringify(r));
} finally { await c.close(); if (front && !/switcher|loginwindow/i.test(front)) { try { execFileSync("osascript", ["-e", `tell application "${front}" to activate`]); } catch {} } }
