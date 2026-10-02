#!/usr/bin/env python3
"""farm.py — Muse's render farm client (GitHub Actions `render.yml` in OWNER/REPO).

The farm renders what is COMMITTED: the workspace git-syncs every 15 min; before submitting, force a
sync (the operator's `git.sync`) or wait for it, and pass --expect-sha to refuse stale code.

  farm.py submit --page projects/<slug>.html --range A:B --chunks N --tag <slug>-v3 [--fps 24] [--runs-on LABEL] [--gl soft|gpu]
  farm.py status <run_id>
  farm.py collect <run_id> <frames_dir>           # download + untar every chunk, verify contiguous frame numbers
  farm.py encode <frames_dir> <audio> <out.mp4> [--fps 24] [--start A]   # A = song time of the first frame
  farm.py sha                                      # current main sha on the remote

Env: MUSE_GITHUB_TOKEN (classic PAT with repo+workflow). Farm defaults: .github/render-farm.json
{"repo":"OWNER/REPO","runs_on":"ubuntu-latest","gl":"soft","max_chunks":20}
"""
import json, os, sys, time, urllib.request, urllib.error, io, zipfile, tarfile, subprocess, re, glob

W = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(W, "../../../.."))
CFG = {"repo": "OWNER/REPO", "runs_on": "ubuntu-latest", "gl": "soft", "max_chunks": 20}
try: CFG.update(json.load(open(os.path.join(ROOT, ".github/render-farm.json"))))
except FileNotFoundError: pass
TOK = os.environ.get("MUSE_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
API = f"https://api.github.com/repos/{CFG['repo']}"

def gh(method, path, body=None, raw=False):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"token {TOK}", "Accept": "application/vnd.github+json", "User-Agent": "muse-farm"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            b = r.read(); return b if raw else (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"HTTP {e.code} {method} {path}", "body": e.read().decode()[:800]})); sys.exit(1)

def submit(a, opt):
    t0, t1 = opt("--range").split(":"); chunks = min(int(opt("--chunks", 4)), CFG["max_chunks"])
    sha = gh("GET", "/commits/main")["sha"]
    if opt("--expect-sha") and not sha.startswith(opt("--expect-sha")): print(json.dumps({"error": "remote is stale", "remote": sha})); sys.exit(1)
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 5))
    gh("POST", "/actions/workflows/render.yml/dispatches", {"ref": "main", "inputs": {
        "page": opt("--page"), "t0": t0, "t1": t1, "chunks": str(chunks), "fps": opt("--fps", "24"),
        "runs_on": opt("--runs-on", CFG["runs_on"]), "gl": opt("--gl", CFG["gl"]), "tag": opt("--tag")}})
    for _ in range(20):
        time.sleep(4)
        runs = gh("GET", f"/actions/workflows/render.yml/runs?per_page=5&created=>={since}")["workflow_runs"]
        if runs: r = runs[0]; print(json.dumps({"run_id": r["id"], "sha": sha[:10], "url": r["html_url"], "chunks": chunks})); return
    print(json.dumps({"error": "dispatched but run not visible yet", "sha": sha[:10]}))

def status(rid):
    r = gh("GET", f"/actions/runs/{rid}"); jobs = gh("GET", f"/actions/runs/{rid}/jobs?per_page=100")["jobs"]
    print(json.dumps({"status": r["status"], "conclusion": r["conclusion"],
                      "jobs": [{"name": j["name"], "status": j["status"], "conclusion": j["conclusion"]} for j in jobs]}, indent=1))

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None

def download_artifact(url):
    """GitHub answers with a 302 to blob storage; the Authorization header must NOT follow it (403)."""
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOK}", "Accept": "application/vnd.github+json", "User-Agent": "muse-farm"})
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=120); raise RuntimeError("expected redirect")
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302, 303, 307): raise
        loc = e.headers["Location"]
    with urllib.request.urlopen(loc, timeout=1200) as r: return r.read()

def collect(rid, out):
    os.makedirs(out, exist_ok=True); arts = gh("GET", f"/actions/runs/{rid}/artifacts?per_page=100")["artifacts"]
    for art in arts:
        z = zipfile.ZipFile(io.BytesIO(download_artifact(art["archive_download_url"])))
        for n in z.namelist():
            with tarfile.open(fileobj=io.BytesIO(z.read(n))) as t:
                for m in t.getmembers():
                    if m.isfile() and m.name.endswith(".jpg"):
                        m.name = os.path.basename(m.name); t.extract(m, out)
                    elif m.name.endswith("render.log"):
                        m.name = f"render-{art['name']}.log"; t.extract(m, out)
    if not glob.glob(os.path.join(out, "f*.jpg")): print(json.dumps({"artifacts": len(arts), "frames": 0})); return
    nums = sorted(int(re.findall(r"\d+", os.path.basename(f))[0]) for f in glob.glob(os.path.join(out, "f*.jpg")))
    gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)] if nums else []
    print(json.dumps({"artifacts": len(arts), "frames": len(nums), "first": nums[0] if nums else None, "last": nums[-1] if nums else None, "missing": gaps[:50]}))

def encode(fr, audio, out, fps=24.0, start=None):
    files = sorted(glob.glob(os.path.join(fr, "f*.jpg"))); first = int(re.findall(r"\d+", os.path.basename(files[0]))[0])
    start = float(start) if start is not None else first / fps
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-start_number", str(first), "-i", os.path.join(fr, "f%05d.jpg"),
                    "-ss", f"{start:.4f}", "-i", audio, "-map", "0:v", "-map", "1:a", "-shortest",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out], check=True)
    print(json.dumps({"out": out, "frames": len(files), "start": start}))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if not TOK: print(json.dumps({"error": "MUSE_GITHUB_TOKEN not set"})); sys.exit(1)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    c = a[0]
    if c == "submit": submit(a, opt)
    elif c == "status": status(a[1])
    elif c == "collect": collect(a[1], a[2])
    elif c == "encode": encode(a[1], a[2], a[3], float(opt("--fps", 24)), opt("--start"))
    elif c == "sha": print(gh("GET", "/commits/main")["sha"])
    else: print(__doc__)
