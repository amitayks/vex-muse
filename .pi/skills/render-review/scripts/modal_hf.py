"""modal_hf.py — render a built HyperFrames/GSAP composition on Modal CPU containers, in parallel.

Why: the local box captures ~2 fps (a 5.5-min comp = ~90 min). A GSAP comp whose timeline is a pure
function of time (no CSS @keyframes, no Math.random / Date.now / rAF loops) can be captured frame-exact by
seeking its registered timeline and screenshotting — the same thing HyperFrames does. Each container
renders one span of frames and encodes it with identical x264 settings; the local side concatenates the
chunks losslessly (-c copy) and muxes the master audio.

  source tools/env.sh
  $PY -m modal run .pi/skills/render-review/scripts/modal_hf.py --comp projects/<slug>/motion/<comp> \
      --timeline <id> --duration 334.94 --out projects/<slug>/renders/v1.mp4 --audio projects/<slug>/audio/mix.wav \
      [--fps 30 --chunks 25 --crf 16 --t0 0 --t1 <sec>]   (t0/t1 = partial test render)
The comp's audio folder is not shipped (a silent stub replaces it); the master audio is muxed locally.
"""
import json, os, pathlib, subprocess, sys, tempfile, time
import modal

COMP = os.environ.get("HF_COMP", "")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl", "ca-certificates", "gnupg", "unzip", "ffmpeg",
                 "libnss3", "libatk1.0-0", "libatk-bridge2.0-0", "libcups2", "libdrm2", "libxkbcommon0", "libxcomposite1",
                 "libxdamage1", "libxfixes3", "libxrandr2", "libgbm1", "libasound2", "libpango-1.0-0", "libcairo2",
                 "fonts-liberation")
    .run_commands(
        "curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs",
        "mkdir -p /opt/deps && cd /opt/deps && npm init -y >/dev/null && npm i puppeteer-core@^25.11.0 --ignore-scripts --no-audit --no-fund",
        "cd /opt && npx --yes @puppeteer/browsers install chrome-headless-shell@stable --path /opt/ch | tail -1 | awk '{print $2}' > /opt/chrome_path",
    )
)
if COMP:
    image = image.add_local_dir(COMP, "/comp", ignore=["assets/audio/**", "**/*.wav", "**/*.mp3"])
app = modal.App("muse-hf-render", image=image)

NODE = r"""
import { createRequire } from "module"; const require = createRequire("/opt/deps/"); const puppeteer = require("puppeteer-core");
import { spawn } from "child_process"; import fs from "fs";
const [,, chrome, tlid, f0s, f1s, fpss, crf, out] = process.argv; const f0 = +f0s, f1 = +f1s, fps = +fpss;
const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-preset", "slow", "-crf", crf, "-pix_fmt", "yuv420p", "-profile:v", "high",
  "-r", String(fps), out], { stdio: ["pipe", "inherit", "inherit"] });
const done = new Promise(r => ff.on("close", r));
const b = await puppeteer.launch({ executablePath: chrome, args: ["--no-sandbox", "--allow-file-access-from-files", "--hide-scrollbars", "--force-color-profile=srgb"] });
const p = await b.newPage(); await p.setViewport({ width: 1920, height: 1080 });
let errs = 0; p.on("pageerror", e => { errs++; console.log("PAGEERROR", e.message); });
await p.goto("file:///tmp/comp/index.html", { waitUntil: "load" });
await p.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
await new Promise(r => setTimeout(r, 2000));
const t0 = Date.now();
for (let i = f0; i < f1; i++) {
  await p.evaluate((t, id) => new Promise(res => { window.__timelines[id].seek(t, false); requestAnimationFrame(() => requestAnimationFrame(res)); }), i / fps, tlid);
  const buf = await p.screenshot({ type: "jpeg", quality: 95 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
}
ff.stdin.end(); await done; await b.close();
console.log(JSON.stringify({ f0, f1, errs, s_per_frame: ((Date.now() - t0) / 1000 / (f1 - f0)).toFixed(3) }));
"""

@app.function(cpu=2.0, memory=4096, timeout=3600, max_containers=30)
def chunk(tlid: str, f0: int, f1: int, fps: int, crf: int) -> dict:
    import shutil, wave
    shutil.rmtree("/tmp/comp", ignore_errors=True); shutil.copytree("/comp", "/tmp/comp")
    os.makedirs("/tmp/comp/assets/audio", exist_ok=True)
    with wave.open("/tmp/comp/assets/audio/mix.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b"\0\0" * 8000)
    open("/tmp/r.mjs", "w").write(NODE); out = f"/tmp/c_{f0:06d}.mp4"
    r = subprocess.run(["node", "/tmp/r.mjs", open("/opt/chrome_path").read().strip(), tlid, str(f0), str(f1), str(fps), str(crf), out],
                       capture_output=True, text=True)
    res = {"f0": f0, "f1": f1, "log": (r.stdout + r.stderr)[-1500:], "rc": r.returncode}
    if os.path.exists(out): res["mp4"] = open(out, "rb").read()
    return res

@app.local_entrypoint()
def main(comp: str, timeline: str, duration: float, out: str, audio: str = "", fps: int = 30, chunks: int = 25, crf: int = 16,
         t0: float = 0.0, t1: float = -1.0):
    import math
    total = math.ceil(duration * fps); a = round(t0 * fps); z = total if t1 < 0 else min(total, round(t1 * fps))
    step = -(-(z - a) // chunks); spans = [(a + i * step, min(z, a + (i + 1) * step)) for i in range(chunks) if a + i * step < z]
    tmp = tempfile.mkdtemp(prefix="hfchunks_", dir=os.path.dirname(os.path.abspath(out)))
    start = time.time(); parts = []; bad = []
    for res in chunk.starmap([(timeline, s, e, fps, crf) for s, e in spans]):
        if res.get("rc") != 0 or "mp4" not in res: bad.append(res); print("CHUNK FAIL", res["f0"], res["log"][-600:]); continue
        pth = f"{tmp}/c_{res['f0']:06d}.mp4"; open(pth, "wb").write(res.pop("mp4")); parts.append(pth)
        print("chunk", res["f0"], res["f1"], res["log"].strip().splitlines()[-1][:160])
    if bad: sys.exit(f"{len(bad)} chunk(s) failed; parts kept in {tmp}")
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in sorted(parts)))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst]
    if audio: cmd += ["-ss", str(t0), "-t", str((z - a) / fps), "-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "320k"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart"] + (["-shortest"] if audio else []) + [out]
    subprocess.run(cmd, check=True)
    for p in parts: os.remove(p)
    os.remove(lst); os.rmdir(tmp)
    print(json.dumps({"out": out, "frames": z - a, "chunks": len(spans), "wall_s": round(time.time() - start, 1), "mb": round(os.path.getsize(out) / 1e6, 1)}))
