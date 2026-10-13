import { launch, sleep } from "../tools/cdp.mjs";
const B = "http://127.0.0.1:8765/";
const c = await launch({ headless: true, width: 1280, height: 720 });
try {
  await c.send("Page.navigate", { url: B + "?file=runs/garden-sfm/ply/garden_sfm_points.ply&cams=runs/garden-sfm/cameras.json" });
  await c.waitFor("window.__viewer && window.__viewer.ready", 60000);
  await sleep(2000);
  const info = await c.evaluate(`(()=>{const gl=__viewer.renderer.getContext();const e=gl.getExtension('WEBGL_debug_renderer_info');return {splats:__viewer.splats, gpu:e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):'?', fps:__viewer.fpsStats()}})()`);
  console.log(JSON.stringify(info));
  await c.screenshot("tests/smoke_free.png");
  console.log(c.logs.slice(-8).join("\n"));
} finally { await c.close(); }
