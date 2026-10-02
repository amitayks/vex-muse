"""modal_audio.py — Muse's GPU audio lab on Modal (pay per second, nothing idle).

Heavy open models that don't fit this 2-CPU box: Demucs stems, beat_this beats/downbeats, and a
yt-dlp fetch from a different IP. Run with the Muse venv (MODAL_TOKEN_ID/SECRET in env):

  $PY -m modal run .pi/skills/song-map/scripts/modal_audio.py::stems --audio song.mp3 --out audio/stems [--model htdemucs_ft] [--cpu]
  $PY -m modal run .pi/skills/song-map/scripts/modal_audio.py::beats --audio song.mp3 --out audio/beats.json
  $PY -m modal run .pi/skills/song-map/scripts/modal_audio.py::fetch --url "<url or ytsearch1:...>" --out sources/

Outputs: stems as 320k MP3 (<name>.mp3 per stem) + timing JSON; beats.json {beats[], downbeats[], model, wall_s}.
GPU: L4 (~$0.80/h). Cost ≈ wall_s × rate; each call prints wall_s and gpu so the caller logs it to the ledger.
"""
import io, os, json, time, pathlib, subprocess
import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git", "libsndfile1")
    .pip_install("torch==2.5.1", "torchaudio==2.5.1", "numpy<2", "soundfile", "soxr", "einops", "rotary-embedding-torch",
                 "tqdm", "demucs==4.0.1", "yt-dlp[default]")
    .pip_install("https://github.com/CPJKU/beat_this/archive/main.zip")
    .run_commands("python -c \"from demucs.pretrained import get_model; get_model('htdemucs_ft'); get_model('htdemucs')\"")
    .run_commands("python -c \"from beat_this.inference import File2Beats; File2Beats(checkpoint_path='final0', device='cpu', dbn=False)\"")
)
app = modal.App("muse-audio", image=image)

def _stems(audio: bytes, name: str, model: str, device: str) -> dict:
    d = pathlib.Path("/tmp/job"); subprocess.run(["rm", "-rf", str(d)]); d.mkdir(parents=True)
    src = d / name; src.write_bytes(audio); t0 = time.time()
    r = subprocess.run(["python", "-m", "demucs", "-n", model, "-d", device, "-o", str(d / "out"), str(src)], capture_output=True, text=True)
    sep = time.time() - t0
    if r.returncode: return {"error": (r.stdout + r.stderr)[-2000:]}
    files = {}
    for w in sorted((d / "out" / model).rglob("*.wav")):
        mp3 = w.with_suffix(".mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-b:a", "320k", str(mp3)], check=True)
        files[mp3.name] = mp3.read_bytes()
    return {"files": files, "separate_s": round(sep, 1), "model": model, "device": device}

@app.function(gpu="L4", timeout=1800)
def stems_gpu(audio: bytes, name: str, model: str = "htdemucs_ft") -> dict:
    return _stems(audio, name, model, "cuda")

@app.function(cpu=2.0, memory=8192, timeout=3600)
def stems_cpu(audio: bytes, name: str, model: str = "htdemucs_ft") -> dict:
    """2 vCPU — a stand-in for Muse's own box, used to measure CPU separation time."""
    return _stems(audio, name, model, "cpu")

@app.function(gpu="L4", timeout=900)
def beats_gpu(audio: bytes, name: str) -> dict:
    from beat_this.inference import File2Beats
    p = pathlib.Path("/tmp") / name; p.write_bytes(audio); t0 = time.time()
    f2b = File2Beats(checkpoint_path="final0", device="cuda", dbn=False)
    beats, downs = f2b(str(p))
    return {"beats": [round(float(b), 4) for b in beats], "downbeats": [round(float(b), 4) for b in downs],
            "model": "beat_this final0 (no DBN)", "wall_s": round(time.time() - t0, 2)}

@app.function(timeout=900)
def fetch_remote(url: str) -> dict:
    """yt-dlp from Modal's IP (Muse's box IP is bot-walled by YouTube)."""
    d = pathlib.Path("/tmp/dl"); subprocess.run(["rm", "-rf", str(d)]); d.mkdir()
    r = subprocess.run(["yt-dlp", "-f", "bestaudio", "--no-playlist", "-o", str(d / "%(id)s.%(ext)s"), "--print-json", url],
                       capture_output=True, text=True, timeout=800)
    if r.returncode: return {"error": (r.stdout + r.stderr)[-1500:]}
    info = json.loads(r.stdout.strip().splitlines()[-1])
    f = next(iter(sorted(d.iterdir())), None)
    return {"file": f.name if f else None, "data": f.read_bytes() if f else None,
            "meta": {k: info.get(k) for k in ("id", "title", "uploader", "duration", "webpage_url", "abr", "acodec", "ext")}}

@app.local_entrypoint()
def stems(audio: str, out: str, model: str = "htdemucs_ft", cpu: bool = False):
    data = pathlib.Path(audio).read_bytes(); t0 = time.time()
    fn = stems_cpu if cpu else stems_gpu
    res = fn.remote(data, pathlib.Path(audio).name, model)
    if "error" in res: print(json.dumps(res)); raise SystemExit(1)
    os.makedirs(out, exist_ok=True)
    for n, b in res.pop("files").items(): pathlib.Path(out, n).write_bytes(b)
    res.update({"wall_s": round(time.time() - t0, 1), "gpu": None if cpu else "L4", "out": out, "stems": sorted(os.listdir(out))})
    print(json.dumps(res))

@app.local_entrypoint()
def beats(audio: str, out: str):
    t0 = time.time(); res = beats_gpu.remote(pathlib.Path(audio).read_bytes(), pathlib.Path(audio).name)
    res["call_wall_s"] = round(time.time() - t0, 1); res["gpu"] = "L4"
    pathlib.Path(out).write_text(json.dumps(res)); print(json.dumps({k: v for k, v in res.items() if k not in ("beats", "downbeats")} | {"n_beats": len(res["beats"]), "n_down": len(res["downbeats"]), "out": out}))

@app.local_entrypoint()
def fetch(url: str, out: str):
    res = fetch_remote.remote(url)
    if res.get("error"): print(json.dumps({"error": res["error"]})); raise SystemExit(1)
    os.makedirs(out, exist_ok=True); p = pathlib.Path(out, res["file"]); p.write_bytes(res["data"])
    print(json.dumps({"file": str(p), "meta": res["meta"]}))
