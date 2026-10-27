"""modal_fetch.py — fetch public media (YouTube and 1,800+ sites yt-dlp knows) from a fresh Modal container IP.

Why: YouTube answers "Sign in to confirm you're not a bot" to data-center servers and data-center
proxies. A Modal container starts on a different address each time,
and yt-dlp from there usually passes. Pay per second; nothing runs when idle.

  source tools/env.sh   # or any python with `modal` installed and MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in env
  python -m modal run modal_fetch.py --url "<url>" --out <dir> [--mode video|audio] [--height 1080] [--tries 32] [--subs he,en]

Writes into <dir>: <id>.<ext> (video mp4 or audio m4a), <id>.info.json (title, uploader, duration,
chapters, description), subtitles when asked and present (<id>.<lang>.vtt), and fetch-result.json.
Prints one line "RESULT {json}": ok, files, meta, route, ip, blocked (addresses that hit the wall), wall_s.
How it passes YouTube's two walls (27.10.2026): (1) the bot wall is per IP — waves of 8 single-use
containers in 4 regions, first success wins (about 1 address in 10–20 passes); (2) the PO-token wall —
the bgutil helper mints the token inside the container. Node 22 is yt-dlp's JS runtime.
Private or members-only media still needs a login; this route fetches only public media.
"""
import json, os, pathlib, subprocess, time
import modal

BGUTIL = "/opt/bgutil/server/build/generate_once.js"
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg", "curl", "ca-certificates", "git", "unzip")
    .run_commands("curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs")
    .pip_install("yt-dlp[default]", "bgutil-ytdlp-pot-provider")
    # PO-token minter (yt-dlp's second YouTube wall): bgutil script mode, built once into the image
    .run_commands("git clone --depth 1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider /opt/bgutil",
                  "cd /opt/bgutil/server && npm ci --no-audit --no-fund && npx tsc",
                  "yt-dlp --version && ls /opt/bgutil/server/build/generate_once.js")
)
app = modal.App("shift-media-fetch", image=image)


def _fetch(url: str, mode: str = "video", height: int = 1080, subs: str = "", client: str = "") -> dict:
    d = pathlib.Path("/tmp/dl"); subprocess.run(["rm", "-rf", str(d)]); d.mkdir()
    if mode == "audio":
        fmt = ["-f", "ba/b", "-S", "ext:m4a"]
    else:
        # sort, do not filter: some player clients offer only combined formats; -S picks the best <= height
        fmt = ["-f", "bv*+ba/b", "-S", f"res:{height},ext:mp4:m4a", "--merge-output-format", "mp4"]
    cmd = ["yt-dlp", "--js-runtimes", "node", "--no-playlist", "--write-info-json", "--no-progress",
           "-o", str(d / "%(id)s.%(ext)s"), *fmt]
    cmd += ["--extractor-args", f"youtubepot-bgutilscript:script_path={BGUTIL}"]
    if client:
        cmd += ["--extractor-args", f"youtube:player_client={client}"]
    if subs:
        cmd += ["--write-subs", "--write-auto-subs", "--sub-langs", subs, "--sub-format", "vtt"]
    t0 = time.time()
    r = subprocess.run(cmd + [url], capture_output=True, text=True, timeout=1400)
    ip = subprocess.run(["curl", "-s", "--max-time", "5", "https://api.ipify.org"], capture_output=True, text=True).stdout.strip()
    if r.returncode:
        return {"error": (r.stdout + r.stderr)[-6000:], "ip": ip}
    files = {f.name: f.read_bytes() for f in sorted(d.iterdir()) if f.is_file()}
    info = {}
    for n, b in files.items():
        if n.endswith(".info.json"):
            j = json.loads(b)
            info = {k: j.get(k) for k in ("id", "title", "uploader", "channel", "duration", "upload_date",
                                          "webpage_url", "chapters", "description", "width", "height", "ext")}
    return {"files": files, "meta": info, "ip": ip, "dl_s": round(time.time() - t0, 1)}


# one function per region: each try starts a NEW container (max_inputs=1) in another region (another address range)
_kw = dict(timeout=1500, cpu=2.0, memory=4096, single_use_containers=True, scaledown_window=2)
@app.function(region="us-west", **_kw)
def fetch_aws(url, mode, height, subs, client): return _fetch(url, mode, height, subs, client)
@app.function(region="eu", **_kw)
def fetch_gcp(url, mode, height, subs, client): return _fetch(url, mode, height, subs, client)
@app.function(region="ap", **_kw)
def fetch_oci(url, mode, height, subs, client): return _fetch(url, mode, height, subs, client)
@app.function(**_kw)
def fetch_any(url, mode, height, subs, client): return _fetch(url, mode, height, subs, client)
# 16 routes: 4 regions x 4 YouTube client modes. In tests (27.10.2026) about 1 in 10 container
# addresses passes the bot wall; the PO-token helper then unlocks the formats.
_FN = [("any", fetch_any), ("ap", fetch_oci), ("eu", fetch_gcp), ("us-west", fetch_aws)]
ROUTES = [(r, f, c) for c in ("mweb", "tv_simply", "", "web_safari") for (r, f) in _FN]


@app.local_entrypoint()
def main(url: str, out: str, mode: str = "video", height: int = 1080, tries: int = 32, subs: str = ""):
    t0 = time.time(); errors = []
    plan = [ROUTES[i % len(ROUTES)] for i in range(tries)]
    WAVE = 8  # containers started at once; the first success wins
    for w in range(0, len(plan), WAVE):
        calls = []
        for cloud, fn, client in plan[w:w + WAVE]:
            calls.append((f"{cloud}/{client or 'default'}", fn.spawn(url, mode, height, subs, client)))
        results = []
        for route, fc in calls:
            try:
                r = fc.get(timeout=1500)
            except Exception as e:
                r = {"error": f"{type(e).__name__}: {e}", "ip": None}
            r["route"] = route; results.append(r)
        ok = [r for r in results if "error" not in r]
        for r in results:
            if "error" in r:
                e = r["error"]; wall = "Sign in to confirm" in e
                lines = [l for l in e.splitlines() if ("WARNING" in l or "ERROR" in l) and "Sign in to confirm" not in l]
                errors.append({"route": r["route"], "ip": r.get("ip"), "bot_wall": wall, "detail": " | ".join(lines)[-700:] if not wall else ""})
        if not ok: time.sleep(2); continue
        res = ok[0]; i = len(errors) + 1
        if True:
            os.makedirs(out, exist_ok=True); written = []
            for n, b in res["files"].items():
                p = pathlib.Path(out, n); p.write_bytes(b); written.append({"file": str(p), "bytes": len(b)})
            meta = {k: v for k, v in (res["meta"] or {}).items() if k != "description"}
            out_j = {"ok": True, "files": written, "meta": meta, "tries": i, "route": res["route"], "ip": res["ip"],
                     "dl_s": res["dl_s"], "wall_s": round(time.time() - t0, 1), "blocked": len(errors)}
            pathlib.Path(out, "fetch-result.json").write_text(json.dumps(out_j, ensure_ascii=False, indent=1))
            print("RESULT " + json.dumps(out_j, ensure_ascii=False))
            return
    out_j = {"ok": False, "errors": errors, "wall_s": round(time.time() - t0, 1)}
    os.makedirs(out, exist_ok=True); pathlib.Path(out, "fetch-result.json").write_text(json.dumps(out_j, ensure_ascii=False, indent=1))
    print("RESULT " + json.dumps(out_j, ensure_ascii=False))
    raise SystemExit(1)
