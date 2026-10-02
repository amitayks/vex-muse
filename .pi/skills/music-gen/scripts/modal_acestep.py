"""modal_acestep.py — ACE-Step 1.5 (MIT, open weights) on a Modal GPU: our own music model, no per-song fee.

  $PY -m modal run .pi/skills/music-gen/scripts/modal_acestep.py::gen --job job.json --out DIR

job.json (all optional except caption or lyrics):
  {"caption": "...", "lyrics": "[Instrumental]" | "[verse]\\n...", "bpm": 128, "keyscale": "A minor", "timesignature": "4",
   "duration": 30, "seed": 7, "batch": 2, "thinking": true, "steps": 8,
   "task": "text2music|cover|repaint", "src_audio": "/local/path.mp3", "reference_audio": "/local/ref.mp3",
   "repaint": [t0, t1], "cover_strength": 0.6, "dit": "acestep-v15-turbo", "lm": "acestep-5Hz-lm-1.7B"}
Writes DIR/<i>.wav per take + DIR/acestep.json (params, lm metadata, timings, gpu, wall_s).
Cost = wall_s × GPU rate (L4 ≈ $0.80/h); first call pays a cold start (weights are baked into the image).
"""
import json, os, time, pathlib, subprocess
import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "libsndfile1", "build-essential")
    .pip_install("uv", "huggingface_hub[hf_transfer]")
    .run_commands("git clone --depth 1 https://github.com/ace-step/ACE-Step-1.5.git /opt/ace",
                  "cd /opt/ace && UV_PYTHON=python3.11 uv sync --no-dev 2>&1 | tail -5")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_commands("python -c \"from huggingface_hub import snapshot_download; snapshot_download('ACE-Step/Ace-Step1.5', local_dir='/opt/ace/checkpoints')\"")
)
app = modal.App("muse-acestep", image=image)

RUNNER = r'''
import json, sys, time, os, traceback
os.chdir("/opt/ace"); sys.path.insert(0, "/opt/ace")
job = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True); T = {}
t = time.time()
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music
dit = AceStepHandler(); llm = LLMHandler()
print("dit init:", dit.initialize_service(project_root="/opt/ace", config_path=job.get("dit", "acestep-v15-turbo"), device="cuda"))
if job.get("thinking", True):
    print("lm init:", llm.initialize(checkpoint_dir="/opt/ace/checkpoints", lm_model_path=job.get("lm", "acestep-5Hz-lm-1.7B"), backend=job.get("backend", "pt"), device="cuda"))
T["init_s"] = round(time.time() - t, 1)
kw = dict(task_type=job.get("task", "text2music"), caption=job.get("caption", ""), lyrics=job.get("lyrics", "[Instrumental]"),
          instrumental=job.get("lyrics", "[Instrumental]").strip().lower() in ("[instrumental]", "[inst]"),
          bpm=job.get("bpm"), keyscale=job.get("keyscale", ""), timesignature=str(job.get("timesignature", "")),
          duration=float(job.get("duration", -1)), inference_steps=int(job.get("steps", 8)), thinking=bool(job.get("thinking", True)))
if job.get("src_audio"): kw["src_audio"] = job["src_audio"]
if job.get("reference_audio"): kw["reference_audio"] = job["reference_audio"]
if job.get("repaint"): kw.update(repainting_start=float(job["repaint"][0]), repainting_end=float(job["repaint"][1]), chunk_mask_mode="explicit")
if job.get("cover_strength") is not None: kw["audio_cover_strength"] = float(job["cover_strength"])
params = GenerationParams(**kw)
seeds = [int(job["seed"]) + i for i in range(int(job.get("batch", 1)))] if job.get("seed") is not None else None
config = GenerationConfig(batch_size=int(job.get("batch", 1)), audio_format="wav", seeds=seeds, use_random_seed=seeds is None)
t = time.time(); res = generate_music(dit, llm, params, config, save_dir=out); T["gen_s"] = round(time.time() - t, 1)
meta = {"success": res.success, "error": res.error, "status": res.status_message, "timing": T, "takes": []}
for a in (res.audios or []):
    p = {k: v for k, v in (a.get("params") or {}).items() if isinstance(v, (str, int, float, bool, type(None)))}
    meta["takes"].append({"path": a.get("path"), "key": a.get("key"), "params": p})
try:
    lm = (res.extra_outputs or {}).get("lm_metadata")
    meta["lm_metadata"] = json.loads(json.dumps(lm, default=str)) if lm else None
    meta["time_costs"] = json.loads(json.dumps((res.extra_outputs or {}).get("time_costs"), default=str))
except Exception: pass
json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1, default=str)
print(json.dumps({"success": res.success, "error": res.error, "timing": T}))
'''

@app.function(gpu="L4", timeout=1800)
def generate(job: dict, files: dict) -> dict:
    d = pathlib.Path("/tmp/job"); subprocess.run(["rm", "-rf", str(d)]); (d / "in").mkdir(parents=True)
    for k in ("src_audio", "reference_audio"):
        if job.get(k):
            p = d / "in" / os.path.basename(job[k]); p.write_bytes(files[job[k]]); job[k] = str(p)
    (d / "job.json").write_text(json.dumps(job)); (d / "run.py").write_text(RUNNER)
    t0 = time.time()
    r = subprocess.run(["/opt/ace/.venv/bin/python", str(d / "run.py"), str(d / "job.json"), str(d / "out")], capture_output=True, text=True, cwd="/opt/ace")
    res = {"wall_s": round(time.time() - t0, 1), "log": (r.stdout + r.stderr)[-4000:], "files": {}}
    for p in sorted((d / "out").rglob("*")):
        if p.is_file() and p.suffix in (".wav", ".flac", ".mp3", ".json"): res["files"][p.name] = p.read_bytes()
    return res

@app.local_entrypoint()
def gen(job: str, out: str):
    j = json.loads(pathlib.Path(job).read_text()); files = {}
    for k in ("src_audio", "reference_audio"):
        if j.get(k): files[j[k]] = pathlib.Path(j[k]).read_bytes()
    t0 = time.time(); res = generate.remote(j, files)
    os.makedirs(out, exist_ok=True); n = 0
    for name, b in res["files"].items():
        pathlib.Path(out, name).write_bytes(b); n += name.endswith((".wav", ".flac", ".mp3"))
    summary = {"out": out, "takes": n, "gpu": "L4", "container_wall_s": res["wall_s"], "call_wall_s": round(time.time() - t0, 1),
               "est_usd": round(res["wall_s"] / 3600 * 0.80, 4)}
    pathlib.Path(out, "acestep.json").write_text(json.dumps(summary | {"job": j, "log_tail": res["log"][-1500:]}, indent=1))
    print(res["log"][-1200:]); print(json.dumps(summary))
