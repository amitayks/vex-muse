#!/usr/bin/env python3
"""critic.py (skill crew) — the independent critic station. A different model (Gemini via fal's OpenRouter routes)
judges a maker's artifact against a rubric and returns JSON: {"pass": bool, "score": 0-10, "scores": {...},
"defects": [{"where": "...", "what": "...", "fix": "..."}], "verdict": "..."}.

usage: critic.py KIND RUBRIC.md OUT.json FILE [FILE ...] [--ledger LEDGER] [--model M] [--context CONTEXT.md] [--refs A.jpg,B.jpg]
  --refs (image kind): approved reference images sent FIRST and labelled REFERENCE; the judged files follow.
  KIND = text  (scripts, treatments, shot lists: .md/.txt/.json)
       | image (cast sheets, sets, start frames: .jpg/.png, sent inline)
       | video (takes, cuts: .mp4, sent inline through video-critic/scripts/watch.py logic)
In a factory bash step: FILE paths may be read from $VEX_STEP_OUTPUTS by the caller; this script only takes paths.
Exit 0 always when the critic answered (pass/fail is in the JSON); exit 2 on transport errors."""
import base64, json, os, subprocess, sys, tempfile, time, pathlib, urllib.request, urllib.error
# factory bash stations do not source tools/env.sh: put the studio's static ffmpeg on PATH (image/video kinds need it)
os.environ["PATH"] = "/data/workspaces/<workspace>/tools/bin:" + os.environ.get("PATH", "/usr/bin:/bin")

a = sys.argv[1:]
def opt(k, d=None):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
ledger = opt("--ledger", "/data/workspaces/<workspace>/projects/ledger-misc.jsonl")
model = opt("--model", "google/gemini-3.1-pro-preview")
ctx = opt("--context")
refs = [r for r in (opt("--refs") or "").split(",") if r]   # approved reference images (set, cast) to compare against
if len(a) < 4: print(__doc__); sys.exit(1)
kind, rubric, out, files = a[0], a[1], a[2], a[3:]
H = {"Authorization": "Key " + os.environ["FAL_KEY"], "Content-Type": "application/json"}

def call(route, body):
    def op(req, t):
        try: return json.load(urllib.request.urlopen(req, timeout=t))
        except urllib.error.HTTPError as e: print(f"HTTP {e.code}: {e.read()[:800]!r}", file=sys.stderr); sys.exit(2)
    sub = op(urllib.request.Request(f"https://queue.fal.run/{route}", data=json.dumps(body).encode(), headers=H, method="POST"), 300)
    t0, w = time.time(), 2
    while True:
        s = op(urllib.request.Request(sub["status_url"], headers=H), 60)
        if s.get("status") == "COMPLETED": break
        if time.time() - t0 > 1500: print("timeout", file=sys.stderr); sys.exit(2)
        time.sleep(w); w = min(w * 1.3, 12)
    return sub["request_id"], op(urllib.request.Request(sub["response_url"], headers=H), 120), round(time.time() - t0, 1)

SYS = ("You are the independent critic on a film crew. You did not make this work and you owe the maker nothing. "
       "Judge only against the rubric and the project context. Scores are calibrated: 10 = nothing could be improved by a top "
       "professional (rare), 8 = strong with clear weak spots, 7 = the pass line, 5 = needs rework. List at most 12 defects, most severe first, each field under 40 words. Always list at least the 3 "
       "weakest moments as defects, even when the work passes (severity minor), plus every real fault (severity major). "
       "Be specific: every defect names where it is "
       "(timecode mm:ss.s, line number, or region of the image), what is wrong, and the smallest fix. "
       "Answer with ONE JSON object and nothing else: "
       '{"pass": true|false, "score": 0-10, "scores": {"<rubric item>": 0-10, ...}, '
       '"defects": [{"where": "...", "severity": "major|minor", "what": "...", "fix": "..."}], "verdict": "one sentence"}')
prompt = "RUBRIC:\n" + pathlib.Path(rubric).read_text()
if ctx: prompt += "\n\nPROJECT CONTEXT:\n" + pathlib.Path(ctx).read_text()[:20000]
body = {"model": model, "system_prompt": SYS, "temperature": 0.2, "max_tokens": 30000, "reasoning": True}

AUD = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus")
if kind == "text":
    texts = [f for f in files if not f.lower().endswith(AUD)]; auds = [f for f in files if f.lower().endswith(AUD)]
    prompt += "".join(f"\n\nARTIFACT {i + 1} ({pathlib.Path(f).name}):\n" + pathlib.Path(f).read_text(errors="replace")[:60000] for i, f in enumerate(texts))
    route = "openrouter/router"
    if auds:   # audio artifacts (voice auditions): one listening reel, clips in order with 1 s gaps, sent on the video route
        tmpd = pathlib.Path(tempfile.mkdtemp()); t, rows, parts = 0.0, [], []
        for i, f in enumerate(auds):
            w = tmpd / f"a{i}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-ac", "2", "-ar", "44100", "-af", "apad=pad_dur=1", str(w)], check=True)
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(w)],
                                     capture_output=True, text=True).stdout.strip())
            rows.append(f"clip {i + 1} = {pathlib.Path(f).name}: {t:.1f}-{t + d - 1:.1f} s"); t += d; parts.append(w)
        (tmpd / "l.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        reel = tmpd / "reel.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x180:r=10", "-f", "concat", "-safe", "0",
                        "-i", str(tmpd / "l.txt"), "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "128k", str(reel)], check=True)
        body["video_url"] = "data:video/mp4;base64," + base64.b64encode(reel.read_bytes()).decode(); route = "openrouter/router/video"
        prompt += ("\n\nAUDIO ARTIFACTS: the attached video has a black picture. LISTEN to its sound track; it plays these audio files "
                   "in order, 1 s of silence after each:\n" + "\n".join(rows))
elif kind == "image":
    urls = []
    for f in refs + files:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "i.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", str(tmp)], check=True)
        urls.append("data:image/jpeg;base64," + base64.b64encode(tmp.read_bytes()).decode())
    body["image_urls"] = urls; route = "openrouter/router/vision"
    if refs:
        prompt += (f"\n\nThe first {len(refs)} image(s) are APPROVED REFERENCES (the canon for every set, vehicle and person in them): "
                   + ", ".join(pathlib.Path(f).name for f in refs) + ". Judge the remaining image(s) against them: the same architecture "
                   "(window shapes and count, frame posts, overhead glazing, panels), the same livery and the same faces. Any difference is a defect.")
    prompt += f"\n\nThe {len(files)} image(s) to judge, in order: " + ", ".join(pathlib.Path(f).name for f in files)
elif kind == "video":
    if len(files) != 1: sys.exit("video: one file per call (compare takes by calling once per take)")
    tmp = pathlib.Path(tempfile.mkdtemp()) / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", files[0], "-vf", "scale=-2:'min(540,ih)'", "-c:v", "libx264", "-b:v", "1200k",
                    "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", "-ac", "2", str(tmp)], check=True)
    body["video_url"] = "data:video/mp4;base64," + base64.b64encode(tmp.read_bytes()).decode(); route = "openrouter/router/video"
else:
    sys.exit("KIND must be text|image|video")
body["prompt"] = prompt
rid, r, wall = call(route, body)
text = (r.get("output") or "").strip()
s, e = text.find("{"), text.rfind("}")
try: verdict = json.loads(text[s:e + 1])
except Exception: verdict = {"pass": False, "score": 0, "defects": [{"where": "critic", "what": "unparseable critic output", "fix": "re-run"}], "raw": text[:3000]}
verdict["_critic"] = {"model": model, "kind": kind, "files": files, "request_id": rid, "cost": (r.get("usage") or {}).get("cost"), "wall_s": wall}
pathlib.Path(out).write_text(json.dumps(verdict, indent=1))
with open(ledger, "a") as f:
    f.write(json.dumps({"ts": int(time.time()), "endpoint": route, "request_id": rid, "tag": f"critic-{kind}-{pathlib.Path(out).stem}",
                        "model": model, "est_usd": verdict["_critic"]["cost"], "wall_s": wall}) + "\n")
print(json.dumps({"out": out, "pass": verdict.get("pass"), "score": verdict.get("score"), "defects": len(verdict.get("defects", [])), "cost": verdict["_critic"]["cost"]}))
