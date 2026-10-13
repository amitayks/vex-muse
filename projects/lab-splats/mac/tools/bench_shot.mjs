// bench_shot.mjs - play a shot for 10 s (headless, vsync on: 60 fps cap) and report rAF fps stats.
// Do not use --disable-frame-rate-limit: headless rAF timestamps then stop tracking GPU work (tested: invalid).
// node tools/bench_shot.mjs <shot rel vol> <w> <h> <out.json>
import { writeFileSync } from "node:fs";
import { launch, sleep } from "./cdp.mjs";
const [shot, W, H, out] = process.argv.slice(2);
const c = await launch({ headless: true, width: +W, height: +H, port: 9336 });
try {
  await c.send("Emulation.setDeviceMetricsOverride", { width: +W, height: +H, deviceScaleFactor: 1, mobile: false });
  await c.send("Page.navigate", { url: `http://127.0.0.1:8765/?shot=${shot}&dpr=1&hud=0` });
  await c.waitFor("window.__viewer && window.__viewer.ready", 240000);
  await sleep(3000);
  await c.evaluate("__viewer.resetFps()");
  await sleep(10000);
  const r = { shot, vsync: "on (60 Hz headless)", fps: await c.evaluate("__viewer.fpsStats()"), splats: await c.evaluate("__viewer.splats"),
    load_s: +((await c.evaluate("__viewer.loadMs")) / 1000).toFixed(2), errors: c.logs.filter((l) => /error|exception/i.test(l)).slice(-5) };
  writeFileSync(out, JSON.stringify(r, null, 1)); console.log(JSON.stringify(r));
} finally { await c.close(); }
