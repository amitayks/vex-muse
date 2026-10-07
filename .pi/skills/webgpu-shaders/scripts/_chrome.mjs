// _chrome.mjs — headless Chrome with a WebGPU canvas that presents on a GPU-less Linux box.
// Only SwiftShader on Vulkan presents a WebGPU canvas; ANGLE-SwiftShader GL flags lose the device.
// puppeteer-core resolves from <workspace>/studio (override: PUPPETEER_ANCHOR=<any file in a dir that has it>).
// Chrome binary: CHROME_PATH (source tools/env.sh).
import { createRequire } from 'module';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const anchor = process.env.PUPPETEER_ANCHOR || path.resolve(here, '../../../../studio/x.js');
const puppeteer = createRequire(anchor)('puppeteer-core');

export const WEBGPU_ARGS = ['--enable-unsafe-webgpu', '--enable-features=Vulkan', '--use-vulkan=swiftshader',
  '--use-webgpu-adapter=swiftshader', '--use-angle=swiftshader'];

export async function launch() {
  if (!process.env.CHROME_PATH) throw new Error('CHROME_PATH is not set: run `source tools/env.sh` first');
  return puppeteer.launch({ executablePath: process.env.CHROME_PATH, headless: true, protocolTimeout: 900000,
    args: ['--no-sandbox', '--allow-file-access-from-files', '--hide-scrollbars', '--force-color-profile=srgb', ...WEBGPU_ARGS] });
}

// Open a page and forward page errors / console errors to stdout. A page must be file:// or localhost
// (WebGPU needs a secure context; about:blank has no navigator.gpu).
export async function open(browser, url, { width, height, scale = 1 }) {
  const p = await browser.newPage();
  await p.setViewport({ width, height, deviceScaleFactor: scale });
  p.on('pageerror', (e) => console.log('[pageerror]', e.message.slice(0, 300)));
  p.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warn') console.log('[console]', m.text().slice(0, 300)); });
  await p.goto(url, { waitUntil: 'load' });
  return p;
}

// Seek a HyperFrames comp exactly like render-review/scripts/modal_hf.py --webgpu does.
export async function seek(p, t, timeline = 'main') {
  await p.evaluate(async (t, id) => {
    window.__timelines[id].seek(t, false);
    if (window.__hfShadersSeek) await window.__hfShadersSeek(t);
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  }, t, timeline);
}

export async function compSize(p) {
  return p.evaluate(() => {
    const r = document.querySelector('[data-composition-id]');
    return { w: +r.dataset.width || 1920, h: +r.dataset.height || 1080, dur: +r.dataset.duration || 0 };
  });
}
