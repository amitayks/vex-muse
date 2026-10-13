// cdp.mjs - minimal Chrome DevTools Protocol driver (Node 22+, no deps).
// Launches Google Chrome with a throwaway profile; never touches the user's own Chrome profile.
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function launch({ headless = true, width = 1280, height = 720, x = 0, y = 0, port = 9333, app = null, extra = [] } = {}) {
  const prof = mkdtempSync(join(tmpdir(), "muse-cdp-"));
  const args = [`--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, "--no-first-run", "--no-default-browser-check",
    "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
    "--enable-gpu-rasterization", "--ignore-gpu-blocklist", `--window-size=${width},${height}`, `--window-position=${x},${y}`, ...extra];
  if (headless) args.push("--headless=new");
  args.push(app ? `--app=${app}` : "about:blank");
  const proc = spawn(CHROME, args, { stdio: "ignore" });
  let ws;
  for (let i = 0; i < 100; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) { ws = page.webSocketDebuggerUrl; break; }
    } catch {}
    await sleep(150);
  }
  if (!ws) throw new Error("chrome did not expose a page target");
  const sock = new WebSocket(ws);
  await new Promise((r, j) => { sock.onopen = r; sock.onerror = j; });
  let id = 0; const pending = new Map(); const listeners = [];
  sock.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { const { res, rej } = pending.get(d.id); pending.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); }
    else if (d.method) for (const l of listeners) l(d);
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); sock.send(JSON.stringify({ id: i, method, params })); });
  const logs = [];
  listeners.push((d) => {
    if (d.method === "Runtime.consoleAPICalled") logs.push(`[${d.params.type}] ` + d.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
    if (d.method === "Runtime.exceptionThrown") logs.push("[exception] " + (d.params.exceptionDetails.exception?.description ?? d.params.exceptionDetails.text));
  });
  await send("Runtime.enable"); await send("Page.enable");
  const evaluate = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
    return r.result.value;
  };
  const waitFor = async (expr, ms = 120000, step = 250) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) { if (await evaluate(expr).catch(() => false)) return true; await sleep(step); }
    throw new Error("timeout waiting for " + expr);
  };
  const screenshot = async (path) => {
    const r = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    writeFileSync(path, Buffer.from(r.data, "base64"));
  };
  const key = (type, code, keyName) => send("Input.dispatchKeyEvent", { type, code, key: keyName, windowsVirtualKeyCode: keyName.length === 1 ? keyName.toUpperCase().charCodeAt(0) : 0 });
  const mouse = (type, x, y, buttons = 1) => send("Input.dispatchMouseEvent", { type, x, y, button: "left", buttons, clickCount: type === "mousePressed" || type === "mouseReleased" ? 1 : 0 });
  const close = async () => { try { await send("Browser.close"); } catch {} proc.kill(); await sleep(300); rmSync(prof, { recursive: true, force: true }); };
  return { send, evaluate, waitFor, screenshot, key, mouse, close, logs, proc };
}
