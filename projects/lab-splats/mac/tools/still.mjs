// node tools/still.mjs <shot rel vol> <t sec> <out.png> [w h]
import { launch, sleep } from "./cdp.mjs";
import { writeFileSync } from "node:fs";
const [shot, t, out] = process.argv.slice(2);
const c = await launch({ headless: true, width: 1600, height: 1000, port: 9334 });
try {
  await c.send("Page.navigate", { url: `http://127.0.0.1:8765/?shot=${shot}&t=${t}&still=1` });
  await c.waitFor("window.__viewer && window.__viewer.ready", 180000);
  await c.waitFor("window.__still_ready === true", 60000);
  await sleep(500);
  const url = await c.evaluate("__viewer.renderer.domElement.toDataURL('image/png')");
  writeFileSync(out, Buffer.from(url.split(",")[1], "base64"));
  console.log(JSON.stringify({ out, splats: await c.evaluate("__viewer.splats"), size: await c.evaluate("[__viewer.renderer.domElement.width, __viewer.renderer.domElement.height]"), logs: c.logs.filter(l => /error|exception/i.test(l)).slice(-5) }));
} finally { await c.close(); }
