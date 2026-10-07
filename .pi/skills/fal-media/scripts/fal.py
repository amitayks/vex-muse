#!/usr/bin/env python3
"""fal.py — stdlib-only fal.ai client for Muse. Queue submit/poll/fetch, file upload, cost ledger.

Usage:
  fal.py run <endpoint> <input.json|-> [--out DIR] [--ledger FILE] [--tag TAG] [--no-wait]
  fal.py status <endpoint> <request_id>
  fal.py result <endpoint> <request_id> [--out DIR]
  fal.py upload <file>                      -> prints a URL usable as *_url input
  fal.py schema <endpoint>                  -> prints input fields (from fal's OpenAPI)
  fal.py price <endpoint>                   -> prints the known rate used for the ledger estimate

Input JSON may reference local files as "@file:/abs/path" anywhere in a string value;
they are uploaded first and replaced by URLs.
Every completed call appends one line to the ledger: ts, endpoint, request_id, tag,
est_usd, seconds, outputs. Downloads every media URL in the result into --out.
Needs env FAL_KEY. Never prints the key.
"""
import json, os, sys, time, urllib.request, urllib.error, mimetypes, pathlib, re

QUEUE = "https://queue.fal.run"
KEY = os.environ.get("FAL_KEY", "")

# Approximate USD rates (checked 2026-09-26 on fal model pages). Update via LEARNINGS when they move.
# unit: 'sec' = per output second, 'img' = per image, 'call' = flat.
RATES = {
    "fal-ai/kling-video/v3/pro/image-to-video":  {"unit": "sec", "any": 0.112},   # audio off; checked 2026-10-07
    "fal-ai/kling-video/v3/4k/image-to-video":   {"unit": "sec", "any": 0.42},    # audio on or off; checked 2026-10-07
    # Veo 3.1 rates are AUDIO OFF (send generate_audio:false); audio on is +50-100 %. Checked 2026-10-07.
    "fal-ai/veo3.1/fast/image-to-video":         {"unit": "sec", "720p": 0.10, "1080p": 0.10, "4k": 0.30},
    "fal-ai/veo3.1/fast/first-last-frame-to-video": {"unit": "sec", "720p": 0.10, "1080p": 0.10, "4k": 0.30},
    "fal-ai/veo3.1/image-to-video":              {"unit": "sec", "720p": 0.20, "1080p": 0.20, "4k": 0.40},
    "fal-ai/veo3.1/first-last-frame-to-video":   {"unit": "sec", "720p": 0.20, "1080p": 0.20, "4k": 0.40},
    # Veo 3.1 Fast text-to-video, AUDIO ON (fal pricing API 0.15/s, 2026-10-07)
    "fal-ai/veo3.1/fast":                        {"unit": "sec", "720p": 0.15, "1080p": 0.15, "4k": 0.35},
    # Performance transfer (model pages, 2026-10-07). Recast: the pricing API's "0.05 units" is NOT per second; the page says $0.30/s 768P, $0.45/s 1080P
    "minimax/h3-max/recast":                     {"unit": "sec", "768P": 0.30, "1080P": 0.45},
    "fal-ai/kling-video/v3/pro/motion-control":  {"unit": "sec", "any": 0.168},
    "fal-ai/kling-video/v3/standard/motion-control": {"unit": "sec", "any": 0.126},
    "fal-ai/wan-motion":                         {"unit": "sec", "any": 0.06},
    "fal-ai/elevenlabs/voice-changer":           {"unit": "per", "per": 60, "any": 0.30},   # assumed per started minute (unverified)
    # MiniMax H3 Max: promo rates until 2026-10-15, then 480P 0.05 / 768P 0.08 / 1080P 0.16
    "minimax/h3-max/camera-controls":            {"unit": "sec", "480P": 0.03, "768P": 0.048, "1080P": 0.096},
    "minimax/h3-max/image-to-video":             {"unit": "sec", "480P": 0.03, "768P": 0.048, "1080P": 0.096},
    "alibaba/wan-3.0-prime/image-to-video":      {"unit": "sec", "480p": 0.068, "720p": 0.14, "1080p": 0.28},
    "fal-ai/marigold-v2":                        {"unit": "img", "any": 0.03},
    "bytedance/seedance-2.5/reference-to-video": {"unit": "sec", "480p": 0.2205, "720p": 0.2838, "1080p": 1.164},
    "bytedance/seedance-2.5/image-to-video":     {"unit": "sec", "480p": 0.2205, "720p": 0.4730, "1080p": 1.164},
    "bytedance/seedance-2.5/text-to-video":      {"unit": "sec", "480p": 0.2205, "720p": 0.4730, "1080p": 1.164},
    "bytedance/seedance-2.5/draft/complete":     {"unit": "sec", "1080p": 1.164},
    "minimax/h3-max/lip-sync/image-to-video":    {"unit": "sec", "768P": 0.04, "1080P": 0.08, "2K": 0.16},
    "fal-ai/sync-lipsync/v3":                    {"unit": "sec", "any": 0.1333},
    "fal-ai/nano-banana-pro":                    {"unit": "img", "any": 0.15},
    "fal-ai/nano-banana-pro/edit":               {"unit": "img", "any": 0.15},
    "fal-ai/nano-banana-2":                      {"unit": "img", "any": 0.08},
    "fal-ai/nano-banana-2/edit":                 {"unit": "img", "any": 0.08},
    "openai/gpt-image-2":                        {"unit": "img", "any": 0.20},
    "openai/gpt-image-2/edit":                   {"unit": "img", "any": 0.20},
    # FLUX 3 Image bills per output megapixel (fal pricing API, 2026-10-04); estimated from the returned width x height, rounded up
    "blackforestlabs/flux-3/text-to-image":      {"unit": "mp", "any": 0.024},
    "blackforestlabs/flux-3/edit-image":         {"unit": "mp", "any": 0.024},
    "fal-ai/bria/background/remove":             {"unit": "img", "any": 0.018},
    "fal-ai/sam-3/image":                        {"unit": "img", "any": 0.005},
    "bria/video/background-removal/v3":          {"unit": "sec", "any": 0.03},
    # Music / audio (fal pricing API, checked 2026-09-26). 'call' = flat per request, 'sec'/'min' = per output
    # second/minute (duration probed from the output file), 'per' = price per `per` seconds of output.
    "google/lyria-3.5":                          {"unit": "call", "any": 0.10},
    "fal-ai/lyria3/pro":                         {"unit": "call", "any": 0.08},
    "fal-ai/lyria3":                             {"unit": "call", "any": 0.04},
    "fal-ai/lyria2":                             {"unit": "per", "per": 30, "any": 0.10},
    "elevenlabs/music/v2.5":                     {"unit": "per", "per": 60, "any": 0.60},   # billed per STARTED minute
    "elevenlabs/music/v2":                       {"unit": "per", "per": 60, "any": 0.60},
    "fal-ai/elevenlabs/music":                   {"unit": "per", "per": 60, "any": 0.60},
    "minimax/music-3":                           {"unit": "sec", "any": 0.002},
    "fal-ai/minimax-music/v2.6":                 {"unit": "call", "any": 0.15},
    "fal-ai/minimax-music/v2.5":                 {"unit": "call", "any": 0.15},
    "fal-ai/stable-audio-3/medium/text-to-audio":      {"unit": "call", "any": 0.0376},
    "fal-ai/stable-audio-3/small/music/text-to-audio": {"unit": "call", "any": 0.0217},
    "fal-ai/stable-audio-3/medium/audio-inpainting":   {"unit": "call", "any": 0.0442},
    "fal-ai/stable-audio-3/medium/audio-outpainting":  {"unit": "call", "any": 0.0446},
    "fal-ai/stable-audio-3/medium/audio-to-audio":     {"unit": "call", "any": 0.0417},
    "fal-ai/stable-audio-25/text-to-audio":      {"unit": "call", "any": 0.20},
    "sonilo/v1.1/text-to-music":                 {"unit": "sec", "any": 0.0025, "min_s": 10},
    "sonilo/v1.1/video-to-music":                {"unit": "sec", "any": 0.009, "min_s": 10},
    "bytedance/seed-audio-1.0":                  {"unit": "min", "any": 0.1875},
    "fal-ai/ace-step":                           {"unit": "sec", "any": 0.0002},
    "fal-ai/ace-step/prompt-to-audio":           {"unit": "sec", "any": 0.0002},
    "fal-ai/ace-step/audio-to-audio":            {"unit": "sec", "any": 0.0002},
    "fal-ai/ace-step/audio-inpaint":             {"unit": "sec", "any": 0.0002},
    "fal-ai/ace-step/audio-outpaint":            {"unit": "sec", "any": 0.0002},
    "fal-ai/diffrhythm":                         {"unit": "per", "per": 10, "any": 0.01},
    "cassetteai/music-generator":                {"unit": "min", "any": 0.02},
    "fal-ai/demucs":                             {"unit": "in_sec", "any": 0.0007},
    "fal-ai/sam-audio/separate":                 {"unit": "per", "per": 30, "any": 0.05},
    "fal-ai/elevenlabs/sound-effects/v2":        {"unit": "sec", "any": 0.002},
    "fal-ai/elevenlabs/audio-isolation":         {"unit": "min", "any": 0.10},
    # TTS bills per 1000 input characters (voice-casting note, seen 2026-10-06)
    "fal-ai/elevenlabs/tts/eleven-v3":           {"unit": "kchar", "any": 0.10},
    "fal-ai/elevenlabs/text-to-dialogue/eleven-v3": {"unit": "kchar", "any": 0.10},
    "fal-ai/elevenlabs/tts/eleven-v4":           {"unit": "kchar", "any": 0.08},
    "fal-ai/elevenlabs/tts/eleven-v4-turbo":     {"unit": "kchar", "any": 0.04},
}
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac")

def die(msg, code=1):
    print(json.dumps({"error": msg}), file=sys.stderr); sys.exit(code)

def http(method, url, body=None, headers=None, raw=False, timeout=600):
    h = {"Authorization": f"Key {KEY}"} if "fal.run" in url or "fal.ai" in url else {}
    h.update(headers or {})
    data = None
    if body is not None:
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                return b if raw else (json.loads(b) if b else {})
        except urllib.error.HTTPError as e:
            txt = e.read().decode(errors="replace")[:2000]
            if e.code in (429, 502, 503, 504) and attempt < 4:
                time.sleep(3 * (attempt + 1)); continue
            die(f"HTTP {e.code} {method} {url.split('?')[0]}: {txt}")
        except urllib.error.URLError as e:
            if attempt < 4: time.sleep(3 * (attempt + 1)); continue
            die(f"network {url}: {e}")

def upload(path):
    p = pathlib.Path(path)
    if not p.is_file(): die(f"no such file {path}")
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    init = http("POST", "https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3",
                {"content_type": ctype, "file_name": p.name})
    http("PUT", init["upload_url"], p.read_bytes(), {"Content-Type": ctype}, raw=True)
    return init["file_url"]

def resolve_files(x):
    if isinstance(x, str) and x.startswith("@file:"):
        return upload(x[6:])
    if isinstance(x, list): return [resolve_files(i) for i in x]
    if isinstance(x, dict): return {k: resolve_files(v) for k, v in x.items()}
    return x

def media_urls(obj, acc=None):
    acc = [] if acc is None else acc
    if isinstance(obj, dict):
        if isinstance(obj.get("url"), str) and obj["url"].startswith("http"): acc.append(obj["url"])
        for v in obj.values(): media_urls(v, acc)
    elif isinstance(obj, list):
        for v in obj: media_urls(v, acc)
    return acc

def probe_secs(u):
    try:
        import subprocess
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", u], capture_output=True, text=True, timeout=120).stdout.strip()
        return float(out) if out else None
    except Exception: return None

def estimate(endpoint, inp, res, files=None, in_secs=None):
    r = RATES.get(endpoint)
    if not r: return None
    if r["unit"] == "kchar":
        txt = inp.get("text") or "".join(str(x.get("text", "")) for x in (inp.get("inputs") or []) if isinstance(x, dict))
        return round(r["any"] * len(txt) / 1000, 5) if txt else None
    if r["unit"] == "mp":
        import math
        ims = (res.get("images") or []) if isinstance(res, dict) else []
        mp = sum((i.get("width") or 0) * (i.get("height") or 0) for i in ims if isinstance(i, dict)) / 1e6
        return round(r["any"] * math.ceil(mp), 4) if mp else None
    if r["unit"] == "img":
        n = len(set(media_urls(res))) or int(inp.get("num_images", 1))   # unique: SAM repeats its mask URL
        return round(r["any"] * n, 4)
    if r["unit"] == "call":
        return round(r["any"] * max(1, int(inp.get("num_samples", 1) or 1)), 4)
    if r["unit"] in ("min", "per", "in_sec") or (r["unit"] == "sec" and any(u.split("?")[0].endswith(AUDIO_EXT) for u in media_urls(res) + list(files or []))):
        # audio: bill on output length (input length for separation), probed from the file itself
        if r["unit"] == "in_sec":
            secs = in_secs
            if not secs: return None
        else:
            # probe the DOWNLOADED files: the static ffprobe segfaults on https URLs
            auds = [f for f in (files or []) if f.endswith(AUDIO_EXT)] or [u for u in media_urls(res) if u.split("?")[0].endswith(AUDIO_EXT)] or media_urls(res)
            if r["unit"] == "sec" and endpoint.startswith("sonilo"): auds = auds[:max(1, int(inp.get("num_samples", 1) or 1))]
            ds = [probe_secs(u) or 0 for u in auds[:4]]
            if not any(ds): return None
            ds = [max(d, r.get("min_s", 0)) for d in ds]; secs = sum(ds)
        if r["unit"] == "min": return round(r["any"] * secs / 60, 4)
        if r["unit"] == "per": return round(r["any"] * -(-secs // r["per"]), 4)
        return round(r["any"] * secs, 4)
    secs = res.get("duration") if isinstance(res, dict) else None
    if not secs:
        d = inp.get("duration")
        secs = float(d) if d and str(d).replace(".", "").isdigit() else None
    if not secs:  # e.g. seedance draft/complete returns no duration: probe the output video itself (local copy first)
        for u in [f for f in (files or []) if f.endswith((".mp4", ".mov", ".webm"))] + media_urls(res):
            if u.split("?")[0].endswith((".mp4", ".mov", ".webm")):
                try:
                    import subprocess
                    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", u], capture_output=True, text=True, timeout=60).stdout.strip()
                    secs = float(out) if out else None
                except Exception: secs = None
                break
    if not secs: return None
    res_key = "480p" if inp.get("draft") else (inp.get("resolution") or next(k for k in r if k != "unit"))
    rate = r.get(res_key) or r.get("any") or max(v for k, v in r.items() if k != "unit")
    return round(rate * float(secs), 4)

def download(urls, out):
    os.makedirs(out, exist_ok=True); files = []
    for u in urls:
        name = re.sub(r"[^A-Za-z0-9._-]", "_", u.split("?")[0].rsplit("/", 1)[-1])[-80:] or "out.bin"
        dest = os.path.join(out, name)
        with urllib.request.urlopen(u, timeout=600) as r, open(dest, "wb") as f: f.write(r.read())
        files.append(dest)
    return files

def run(endpoint, inp, out=None, ledger=None, tag=None, wait=True):
    if not KEY: die("FAL_KEY not set — ask the principal for a secure handoff (vex.secrets.request)")
    in_secs = None
    for v in (inp.values() if isinstance(inp, dict) else []):
        if isinstance(v, str) and v.startswith("@file:") and v.endswith(AUDIO_EXT + (".webm",)):
            in_secs = probe_secs(v[6:]); break
    inp = resolve_files(inp)
    t0 = time.time()
    sub = http("POST", f"{QUEUE}/{endpoint}", inp)
    rid = sub.get("request_id")
    status_url = sub.get("status_url") or f"{QUEUE}/{endpoint}/requests/{rid}/status"
    resp_url = sub.get("response_url") or f"{QUEUE}/{endpoint}/requests/{rid}"
    if not wait:
        print(json.dumps({"request_id": rid, "status_url": status_url, "response_url": resp_url})); return
    delay = 3
    while True:
        st = http("GET", status_url)
        s = st.get("status")
        if s == "COMPLETED": break
        if s in ("FAILED", "ERROR", "CANCELLED"): die(f"{endpoint} {rid} {s}: {st}")
        time.sleep(delay); delay = min(delay * 1.4, 20)
        if time.time() - t0 > 3600: die(f"timeout waiting {rid}")
    res = http("GET", resp_url)
    urls = media_urls(res)
    files = download(urls, out) if out else []
    rec = {"ts": int(time.time()), "endpoint": endpoint, "request_id": rid, "tag": tag,
           "est_usd": estimate(endpoint, inp, res, files, in_secs), "wall_s": round(time.time() - t0, 1),
           "seed": res.get("seed") if isinstance(res, dict) else None,
           "draft_id": res.get("draft_id") if isinstance(res, dict) else None,
           "urls": urls, "files": files}
    if ledger:
        os.makedirs(os.path.dirname(os.path.abspath(ledger)), exist_ok=True)
        with open(ledger, "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps({"result": res, "ledger": rec}, indent=1))

def schema(endpoint):
    d = json.loads(http("GET", f"https://fal.ai/api/openapi/queue/openapi.json?endpoint_id={endpoint}", raw=True))
    for n, s in d.get("components", {}).get("schemas", {}).items():
        if n.endswith("Input"):
            print(n, "required:", s.get("required"))
            for k, v in s.get("properties", {}).items():
                print(f"  {k}: enum={v.get('enum')} default={v.get('default')} | {(v.get('description') or '')[:200]}")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    cmd = a[0]
    if cmd == "run":
        src = a[2]; inp = json.load(sys.stdin if src == "-" else open(src))
        run(a[1], inp, opt("--out"), opt("--ledger"), opt("--tag"), "--no-wait" not in a)
    elif cmd == "status": print(json.dumps(http("GET", f"{QUEUE}/{a[1]}/requests/{a[2]}/status")))
    elif cmd == "result":
        res = http("GET", f"{QUEUE}/{a[1]}/requests/{a[2]}")
        files = download(media_urls(res), opt("--out")) if opt("--out") else []
        print(json.dumps({"result": res, "files": files}, indent=1))
    elif cmd == "upload": print(upload(a[1]))
    elif cmd == "schema": schema(a[1])
    elif cmd == "price": print(json.dumps(RATES.get(a[1], "unknown — read the model page and add it to RATES")))
    else: print(__doc__); sys.exit(2)
