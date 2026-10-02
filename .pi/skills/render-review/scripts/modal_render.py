"""modal_render.py — Muse's GPU render farm on Modal (pay per second, nothing idle).

Run with the Muse venv:  source tools/env.sh; export MODAL_TOKEN_ID/SECRET (from secrets);
  $PY -m modal run .pi/skills/render-review/scripts/modal_render.py::probe
  $PY -m modal run .pi/skills/render-review/scripts/modal_render.py::render \
       --page projects/<slug>.html --t0 0 --t1 30 --chunks 8 --fps 24 --out projects/<slug>/renders/frames [--gpu L4] [--angle vulkan]
The studio/ folder (minus node_modules/out) is shipped with each call, so what renders is exactly the
local working tree — no git sync needed. Frames come back as JPEGs named f%05d.jpg (global frame index),
ready for farm.py encode.
"""
import io, os, sys, tarfile, time, json, pathlib
import modal

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4] if len(HERE.parents) > 4 else HERE.parent   # workspace root (local side only)
STUDIO = ROOT / "studio"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl", "ca-certificates", "gnupg", "unzip", "ffmpeg", "libvulkan1", "mesa-vulkan-drivers",
                 "libnss3", "libatk1.0-0", "libatk-bridge2.0-0", "libcups2", "libdrm2", "libxkbcommon0", "libxcomposite1",
                 "libxdamage1", "libxfixes3", "libxrandr2", "libgbm1", "libasound2", "libpango-1.0-0", "libcairo2",
                 "libegl1", "libgl1", "fonts-liberation", "fonts-noto-color-emoji")
    .run_commands(
        "curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs",
        "mkdir -p /opt/studio-deps && cd /opt/studio-deps && npm init -y >/dev/null && npm i p5@^2.3.3 p5.brush@^2.2.3 puppeteer-core@^25.11.0 --ignore-scripts --no-audit --no-fund",
        "cd /opt && npx --yes @puppeteer/browsers install chrome-headless-shell@stable --path /opt/ch | tail -1 | awk '{print $2}' > /opt/chrome_path",
        # NVIDIA Vulkan ICD so ANGLE/Vulkan finds the driver Modal mounts into GPU containers
        "mkdir -p /usr/share/vulkan/icd.d && printf '{\"file_format_version\":\"1.0.0\",\"ICD\":{\"library_path\":\"libGLX_nvidia.so.0\",\"api_version\":\"1.3\"}}' > /usr/share/vulkan/icd.d/nvidia_icd.json",
    )
    .env({"NVIDIA_DRIVER_CAPABILITIES": "all", "NVIDIA_VISIBLE_DEVICES": "all"})
)
app = modal.App("muse-render", image=image)

def pack_studio() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for p in STUDIO.rglob("*"):
            rel = p.relative_to(STUDIO)
            if rel.parts and rel.parts[0] in ("node_modules", "out"): continue
            if p.is_file(): t.add(p, arcname=str(rel))
    return buf.getvalue()

def _prep(studio_tgz: bytes) -> str:
    import shutil
    d = "/tmp/studio"
    shutil.rmtree(d, ignore_errors=True)   # warm containers are reused: never render a previous call's tree or frames
    os.makedirs(d); tarfile.open(fileobj=io.BytesIO(studio_tgz), mode="r:gz").extractall(d)
    os.symlink("/opt/studio-deps/node_modules", f"{d}/node_modules")
    return d

def _angle_args(angle):
    return {"vulkan": "--gpu-angle=vulkan", "gl-egl": "--gpu-angle=gl-egl", "soft": "--soft-gl"}[angle]

@app.function(gpu="L4", timeout=900)
def probe_gpu(studio_tgz: bytes, angle: str = "vulkan") -> dict:
    import subprocess
    d = _prep(studio_tgz); chrome = open("/opt/chrome_path").read().strip()
    smi = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    out = {"gpu": smi, "angle": angle}
    r = subprocess.run(["node", "gpu_probe.mjs", chrome], cwd=d, capture_output=True, text=True, timeout=300)
    out["probe"] = (r.stdout + r.stderr)[-1500:]
    t0 = time.time()
    r = subprocess.run(["node", "render.mjs", f"--chrome={chrome}", _angle_args(angle), "--sheet=1,1.04,5,8", "--cols=4", "--w=480", "--out=out/s.jpg"],
                       cwd=d, capture_output=True, text=True, timeout=800)
    out["sheet"] = (r.stdout + r.stderr)[-800:]; out["wall_s"] = round(time.time() - t0, 1)
    if os.path.exists(f"{d}/out/s.jpg"): out["sheet_jpg"] = open(f"{d}/out/s.jpg", "rb").read()
    return out

@app.function(gpu="L4", timeout=3600, max_containers=20)
def render_chunk(studio_tgz: bytes, page: str, a: float, b: float, fps: float, angle: str) -> bytes:
    import subprocess
    d = _prep(studio_tgz); chrome = open("/opt/chrome_path").read().strip()
    r = subprocess.run(["node", "render.mjs", f"--page={page}", f"--chrome={chrome}", _angle_args(angle), "--frames",
                        f"--range={a:.6f}:{b:.6f}", f"--fps={fps}", "--workers=2"], cwd=d, capture_output=True, text=True)
    log = (r.stdout + r.stderr)[-3000:]
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        fr = pathlib.Path(d, "out/frames")
        for f in sorted(fr.glob("f*.jpg")): t.add(f, arcname=f.name)
        data = log.encode(); ti = tarfile.TarInfo(f"render-{a:.2f}.log"); ti.size = len(data); t.addfile(ti, io.BytesIO(data))
    return buf.getvalue()

@app.local_entrypoint()
def probe(angle: str = "vulkan"):
    res = probe_gpu.remote(pack_studio(), angle)
    jpg = res.pop("sheet_jpg", None)
    if jpg: pathlib.Path("/tmp/modal_probe_sheet.jpg").write_bytes(jpg); res["sheet_file"] = "/tmp/modal_probe_sheet.jpg"
    print(json.dumps(res, indent=1))

@app.local_entrypoint()
def render(page: str, t0: float, t1: float, out: str, chunks: int = 8, fps: float = 24, angle: str = "vulkan"):
    tgz = pack_studio(); f0, f1 = round(t0 * fps), round(t1 * fps); step = -(-(f1 - f0) // chunks)
    spans = [((f0 + i * step) / fps, min(f1, f0 + (i + 1) * step) / fps) for i in range(chunks) if f0 + i * step < f1]
    os.makedirs(out, exist_ok=True); start = time.time(); n = 0
    for tb in render_chunk.starmap([(tgz, page, a, b, fps, angle) for a, b in spans]):
        with tarfile.open(fileobj=io.BytesIO(tb)) as t: t.extractall(out); n += sum(1 for m in t.getmembers() if m.name.endswith(".jpg"))
    print(json.dumps({"frames": n, "expected": f1 - f0, "chunks": len(spans), "wall_s": round(time.time() - start, 1), "out": out}))
