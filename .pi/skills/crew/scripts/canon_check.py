#!/usr/bin/env python3
"""canon_check.py (skill crew) — the maker's own gate: is this frame (or take) the canon world?
Holistic critic scores were unreliable (2026-10-08: wrong on directions, blind to window changes). Atomic
yes/no questions with the master images beside the frame are reliable. The maker runs this BEFORE recording
and fixes every NO; the director should never have to.

usage: canon_check.py FRAME CHECKLIST.json OUT.json --family F [--refs a.jpg,b.jpg] [--shot ITEMDATA.json] [--brief "q1|q2"] [--ledger L] [--model M]
  --shot: the item's data JSON (shot + light_state); adds brief items so an edit that keeps the canon but loses the shot fails.
  CHECKLIST.json: {"common": [items], "<family>": {"refs": [...], "items": [...]}} ; an item = {"id", "q", "want": "yes"|"no"}
  FRAME may be an image or a video (video: 3 frames at 10/50/90 % are checked).
Prints {"pass": bool, "fails": [{id, q, answer, where}], "checked": n}. Exit 0 when the checker answered."""
import base64, json, os, subprocess, sys, tempfile, time, pathlib, urllib.request, urllib.error
os.environ["PATH"] = "/data/workspaces/<workspace>/tools/bin:" + os.environ.get("PATH", "")
a = sys.argv[1:]
def opt(k, d=None):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
fam = opt("--family"); refs_cli = [r for r in (opt("--refs") or "").split(",") if r]
shot = opt("--shot"); ledger = opt("--ledger", "/data/workspaces/<workspace>/projects/ledger-misc.jsonl"); model = opt("--model", "google/gemini-3.1-pro-preview")
if len(a) < 3 or not fam: print(__doc__); sys.exit(1)
frame, ck, out = a[0], json.loads(pathlib.Path(a[1]).read_text()), a[2]
F = ck.get(fam) or {}; items = ck.get("common", []) + F.get("items", []); refs = (F.get("refs") or []) + refs_cli
brief = opt("--brief")                         # the shot's own read: an edit that passes the canon but loses the shot must fail
if shot and pathlib.Path(shot).exists():
    sj = json.loads(pathlib.Path(shot).read_text()); sh = sj.get("shot", sj)
    if sh.get("on_screen"): items.append({"id": "brief_action", "q": f"Does the frame show what this shot is about: {sh['on_screen']}?", "want": "yes"})
    if sj.get("light_state"): items.append({"id": "brief_light", "q": f"Does the light match this state: {sj['light_state']} (SMOKE = dim amber-brown smoke; DARK SMOKE = windscreen almost black with dense smoke; FIRE = orange firelight from below; CLEAN SKY = bright pale sky, cool light)?", "want": "yes"})
if brief: items += [{"id": f"brief_{k}", "q": q.strip(), "want": "yes"} for k, q in enumerate(brief.split("|")) if q.strip()]
def jpg(path, w=1400):
    t = pathlib.Path(tempfile.mkdtemp()) / "i.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"scale='min({w},iw)':-2", "-frames:v", "1", "-q:v", "3", str(t)], check=True)
    return "data:image/jpeg;base64," + base64.b64encode(t.read_bytes()).decode()
judge = []
if frame.lower().endswith((".mp4", ".mov", ".webm")):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", frame], capture_output=True, text=True).stdout or 1)
    for k, f in enumerate((0.1, 0.5, 0.9)):
        t = pathlib.Path(tempfile.mkdtemp()) / f"f{k}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * f:.2f}", "-i", frame, "-frames:v", "1", "-q:v", "3", str(t)], check=True); judge.append(str(t))
else: judge = [frame]
urls = [jpg(j) for j in judge] + [jpg(r, 1000) for r in refs if pathlib.Path(r).exists()]   # the frame(s) to check FIRST
nref = len(urls) - len(judge)
qs = "\n".join(f'{i["id"]}: {i["q"]}' for i in items)
prompt = (f"IMAGE 1" + (f" to IMAGE {len(judge)}" if len(judge) > 1 else "") + " = the FRAME TO CHECK (answer every question about this only). "
          f"The next {nref} image(s) = APPROVED MASTERS of this film's world, for comparison only: never answer about a master. The frame to check"
          + ("") + ".\n"
          "Answer each question about the frame(s) to check with yes or no, by LOOKING, comparing to the masters where the question says so. "
          "First describe in a few words what you actually see for that item, then answer. A vehicle moves toward where its nose points; a camera facing backward "
          "at a person mirrors left and right. If an item is not visible in the frame, or too small to judge (a person far away), answer \"n/a\".\n"
          "Return ONE JSON object: {\"<id>\": {\"see\": \"...\", \"answer\": \"yes\"|\"no\"|\"n/a\", \"where\": \"region if no\"}, ...}\n\nQUESTIONS:\n" + qs)
body = {"model": model, "prompt": prompt, "image_urls": urls, "temperature": 0.1, "max_tokens": 20000, "reasoning": True}
H = {"Authorization": "Key " + os.environ["FAL_KEY"], "Content-Type": "application/json"}
def op(req, t):
    try: return json.load(urllib.request.urlopen(req, timeout=t))
    except urllib.error.HTTPError as e: print(f"HTTP {e.code}: {e.read()[:300]!r}", file=sys.stderr); sys.exit(2)
sub = op(urllib.request.Request("https://queue.fal.run/openrouter/router/vision", data=json.dumps(body).encode(), headers=H, method="POST"), 300)
t0 = time.time()
while op(urllib.request.Request(sub["status_url"], headers=H), 60).get("status") != "COMPLETED":
    if time.time() - t0 > 900: sys.exit(2)
    time.sleep(3)
r = op(urllib.request.Request(sub["response_url"], headers=H), 120); txt = (r.get("output") or "")
try: ans = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
except Exception: ans = {}
fails = []
for i in items:
    x = ans.get(i["id"]) or {}; v = str(x.get("answer", "")).lower()
    if v == "n/a": continue
    if v != i.get("want", "yes") and i.get("block", True): fails.append({"id": i["id"], "q": i["q"], "answer": v or "missing", "see": x.get("see"), "where": x.get("where")})
warn = [i["id"] for i in items if not i.get("block", True) and str((ans.get(i["id"]) or {}).get("answer", "")).lower() not in (i.get("want", "yes"), "n/a")]
res = {"pass": not fails and bool(ans), "warnings": warn, "fails": fails, "checked": len(items), "family": fam, "frame": frame, "cost": (r.get("usage") or {}).get("cost")}
pathlib.Path(out).write_text(json.dumps({**res, "answers": ans}, indent=1))
with open(ledger, "a") as f: f.write(json.dumps({"ts": int(time.time()), "endpoint": "openrouter/router/vision", "tag": f"canon-{fam}", "model": model, "est_usd": res["cost"]}) + "\n")
print(json.dumps(res)[:3000])
