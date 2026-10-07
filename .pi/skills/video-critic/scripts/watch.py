#!/usr/bin/env python3
"""watch.py (skill video-critic) — let Gemini watch a video WITH its sound and answer as a film professional.
Route: fal `openrouter/router/video` (FAL_KEY; no Google key needed), model google/gemini-3.1-pro-preview by default.
usage: watch.py VIDEO PROMPT_FILE OUT.md [--model M] [--max-height 540] [--public] [--ledger FILE]
- By default the video goes inline as a data URI (never a public CDN URL: our own cuts stay private).
  --public uploads via fal storage instead (only for third-party public clips that are too big to inline).
- The video is re-encoded to <= max-height and ~1.2 Mbps so the request stays small; audio kept (AAC 96k).
Writes the answer to OUT.md and a usage line to the project ledger."""
import base64, json, os, subprocess, sys, tempfile, time, pathlib, urllib.request, urllib.error
def _open(req, timeout):
    try: return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e: sys.exit(f'HTTP {e.code} at {req.full_url}: {e.read()[:1500]!r}')

args = sys.argv[1:]
if len(args) < 3: print(__doc__); sys.exit(1)
video, prompt_file, out = args[:3]
model = args[args.index("--model") + 1] if "--model" in args else "google/gemini-3.1-pro-preview"
mh = int(args[args.index("--max-height") + 1]) if "--max-height" in args else 540
public = "--public" in args
FAL = "/data/workspaces/<workspace>/.pi/skills/fal-media/scripts/fal.py"
LEDGER = args[args.index("--ledger") + 1] if "--ledger" in args else "/data/workspaces/<workspace>/projects/ledger-misc.jsonl"
KEY = os.environ["FAL_KEY"]

tmp = pathlib.Path(tempfile.mkdtemp(prefix="gw_")) / "v.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"scale=-2:'min({mh},ih)'", "-c:v", "libx264", "-b:v", "1200k",
                "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", "-ac", "2", "-movflags", "+faststart", str(tmp)], check=True)
if public:
    url = subprocess.run(["python3", FAL, "upload", str(tmp)], capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
else:
    url = "data:video/mp4;base64," + base64.b64encode(tmp.read_bytes()).decode()
body = {"model": model, "prompt": pathlib.Path(prompt_file).read_text(), "video_url": url, "temperature": 0.2, "max_tokens": 32000, "reasoning": True,
        "system_prompt": "You are a senior film editor, director of photography and re-recording mixer. You watch and LISTEN to the whole video. "
                         "You give timecodes (mm:ss.s) for every claim. You never invent what is not on screen or in the sound."}
H = {"Authorization": f"Key {KEY}", "Content-Type": "application/json"}
req = urllib.request.Request("https://queue.fal.run/openrouter/router/video", data=json.dumps(body).encode(), headers=H, method="POST")
sub = json.load(_open(req, 300)); rid = sub["request_id"]
st_url, res_url = sub["status_url"], sub["response_url"]; t0 = time.time(); wait = 3
while True:
    s = json.load(_open(urllib.request.Request(st_url, headers=H), 60))
    if s.get("status") == "COMPLETED": break
    if time.time() - t0 > 1500: sys.exit(f"timeout, request {rid}")
    time.sleep(wait); wait = min(wait * 1.3, 15)
r = json.load(_open(urllib.request.Request(res_url, headers=H), 120))
text = r.get("output") or json.dumps(r)[:4000]
pathlib.Path(out).write_text(text)
usage = r.get("usage") or {}
cost = usage.get("cost")
with open(LEDGER, "a") as f:
    f.write(json.dumps({"ts": int(time.time()), "endpoint": "openrouter/router/video", "request_id": rid, "tag": f"watch-{pathlib.Path(out).stem}",
                        "model": model, "est_usd": cost, "usage": usage, "wall_s": round(time.time() - t0, 1)}) + "\n")
print(json.dumps({"out": out, "model": model, "chars": len(text), "usage": usage, "wall_s": round(time.time() - t0, 1)}))
