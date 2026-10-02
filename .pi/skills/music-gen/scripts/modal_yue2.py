"""modal_yue2.py — YuE2 (m-a-p, Sep 2026; code Apache-2.0, creators may monetize outputs) on a Modal L40S.

  $PY -m modal run .pi/skills/music-gen/scripts/modal_yue2.py::gen --style "<style words, BPM>" --lyrics-file lyrics.txt --out DIR [--seed 7] [--cot full]

Lyrics use [Verse]/[Chorus] headers. Writes DIR/yue2.flac (48 kHz stereo) + DIR/yue2.json (score/plan files kept
by the pipeline, timings, est_usd). Weights (~m-a-p/YuE2-3B) download on first call into a Modal volume.
"""
import json, os, time, pathlib, subprocess
import modal

image = (modal.Image.debian_slim(python_version="3.12").apt_install("git", "ffmpeg", "libsndfile1")
         .run_commands("git clone --depth 1 https://github.com/multimodal-art-projection/YuE.git /opt/yue", "cd /opt/yue && pip install ."))
vol = modal.Volume.from_name("muse-hf-cache", create_if_missing=True)
app = modal.App("muse-yue2", image=image)
RATE = 1.95  # L40S $/h

@app.function(gpu="L40S", timeout=3600, volumes={"/cache": vol}, env={"HF_HOME": "/cache/hf"})
def generate(style: str, lyrics: str, seed: int = 7, cot: str = "full") -> dict:
    from yue2 import YuE2Pipeline
    t0 = time.time(); out = pathlib.Path("/tmp/yue2out"); subprocess.run(["rm", "-rf", str(out)])
    with YuE2Pipeline.from_pretrained("m-a-p/YuE2-3B", device="cuda") as pipe:
        t1 = time.time(); song = pipe(style=style, lyrics=lyrics, cot=cot, seed=seed); song.save_artifacts(str(out)); t2 = time.time()
    vol.commit()
    files = {p.name: p.read_bytes() for p in out.rglob("*") if p.is_file() and p.suffix in (".flac", ".wav", ".abc", ".json", ".txt") and p.stat().st_size < 50_000_000}
    return {"files": files, "load_s": round(t1 - t0, 1), "gen_s": round(t2 - t1, 1), "wall_s": round(time.time() - t0, 1), "truncated": getattr(song, "truncated", None)}

@app.local_entrypoint()
def gen(style: str, lyrics_file: str, out: str, seed: int = 7, cot: str = "full"):
    t0 = time.time(); res = generate.remote(style, pathlib.Path(lyrics_file).read_text(), seed, cot)
    os.makedirs(out, exist_ok=True)
    for n, b in res.pop("files").items(): pathlib.Path(out, ("yue2" + pathlib.Path(n).suffix) if n.startswith("audio") else n).write_bytes(b)
    res.update({"call_wall_s": round(time.time() - t0, 1), "gpu": "L40S", "est_usd": round(res["wall_s"] / 3600 * RATE, 4)})
    pathlib.Path(out, "yue2.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res))
