#!/usr/bin/env python3
"""bench.py — Eleven v3 vs v4 vs v4 Turbo on Muse's real voice jobs (Antioch cast, fal route).
usage: bench.py gen   -> generates takes into ../takes/<model>/<item>_t<n>.mp3 (+ .json), ledgered
       bench.py qc    -> transcribe (gpt-4o-transcribe) + WER + voice stats -> ../review/qc.json
Timing uses fal's synchronous endpoint (https://fal.run/<endpoint>) so wall_s is not quantised by queue polling.
Never prints keys."""
import json, os, sys, time, re, uuid, subprocess, urllib.request, concurrent.futures as cf
P = "/data/workspaces/<workspace>/projects/lab-voice"; A = "/data/workspaces/<workspace>/projects/antioch-1098"
FAL = os.environ.get("FAL_KEY", ""); OAI = os.environ.get("OPENAI_API_KEY", "")
MODELS = {  # endpoint, USD per 1000 chars (fal pricing API, 2026-09-28)
    "v3":       ("fal-ai/elevenlabs/tts/eleven-v3", 0.10),
    "v4":       ("elevenlabs/tts/eleven-v4", 0.08),
    "v4turbo":  ("elevenlabs/tts/eleven-v4-turbo", 0.04),
}
NAR, BOH, FIR = "VC6vCXhVaI8BZefRtXZV", "m3ERpbBFjTAqD5PJozID", "csXxiUN2BUFflsCaDxPM"
L = {l["id"]: l["text"] for l in json.load(open(f"{A}/audio/voice/lines.json"))}
ITEMS = [
    dict(id="nar_long", voice=NAR, text=" ".join([L["A01"], L["A02"], L["A03"]])),
    dict(id="nar_names", voice=NAR, text="Firuz. He commanded the Tower of the Two Sisters. Why he would sell it — money, perhaps; a grudge against the governor, perhaps — nobody quite knows. Bohemond didn't ask."),
    dict(id="nar_nums", voice=NAR, text="On 3 June 1098, at about 4 a.m., some 60 men climbed a single ladder, and by sunrise Yaghi-Siyan, the governor, had fled."),
    dict(id="boh_line", voice=BOH, text=L["B04"]),
    dict(id="fir_plain", voice=FIR, text="I guard three towers. Name the hour, and they're yours."),
    dict(id="fir_whisper", voice=FIR, text="[whispers] Psst. Are ye there? How many of ye?"),
    dict(id="nar_he", voice=NAR, lang="he", text="אנטיוכיה, אביב אלף תשעים ושמונה. אחת הערים הגדולות של המזרח, ואחת הקשות ביותר לכיבוש."),
]
TAKES = 2

def post(url, body, hdr, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**hdr, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())

def gen_one(model, item, take):
    ep, rate = MODELS[model]; d = f"{P}/takes/{model}"; os.makedirs(d, exist_ok=True)
    stem = f"{d}/{item['id']}_t{take}"
    if os.path.exists(stem + ".mp3"): return model, item["id"], take, "cached"
    inp = {"text": item["text"], "voice": item["voice"], "timestamps": True, "stability": 0.5}
    if item.get("lang"): inp["language_code"] = item["lang"]
    t0 = time.time()
    try: res = post(f"https://fal.run/{ep}", inp, {"Authorization": f"Key {FAL}"})
    except urllib.error.HTTPError as e: return model, item["id"], take, f"HTTP {e.code} {e.read().decode()[:300]}"
    except Exception as e: return model, item["id"], take, f"ERR {e}"
    wall = time.time() - t0
    url = res["audio"]["url"]; urllib.request.urlretrieve(url, stem + ".mp3")
    usd = round(len(item["text"]) / 1000 * rate, 5)
    json.dump({"item": item, "model": model, "endpoint": ep, "wall_s": round(wall, 3), "chars": len(item["text"]),
               "est_usd": usd, "fal": {"result": res}}, open(stem + ".json", "w"), ensure_ascii=False)
    with open(f"{P}/ledger.jsonl", "a") as f:
        f.write(json.dumps({"ts": int(time.time()), "endpoint": ep, "request_id": None, "tag": f"bench-{model}-{item['id']}-t{take}",
                            "est_usd": usd, "wall_s": round(wall, 2), "seed": None, "draft_id": None, "urls": [url],
                            "files": [stem + ".mp3"]}) + "\n")
    return model, item["id"], take, f"ok {wall:.2f}s"

# ---------- QC ----------
def transcribe(path, lang):
    b = "----" + uuid.uuid4().hex; data = open(path, "rb").read()
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="model"\r\n\r\ngpt-4o-transcribe\r\n'.encode(),
             f'--{b}\r\nContent-Disposition: form-data; name="language"\r\n\r\n{lang}\r\n'.encode(),
             f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + data + b"\r\n",
             f"--{b}--\r\n".encode()]
    req = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
                                 headers={"Authorization": f"Bearer {OAI}", "Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=120))["text"]
NUMS = {"3": "three", "1098": "ten ninety eight", "4": "four", "60": "sixty", "am": "a m"}
def norm(s):
    s = re.sub(r"\[.*?\]", " ", s).lower().replace("’", "'").replace("a.m.", "am")
    s = re.sub(r"[^\w' ]+", " ", s); w = s.split()
    out = []
    for x in w: out += NUMS.get(x, x).split()
    return out
def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1])); prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r))

sys.path.insert(0, f"{A}/tools")
def vstats(path):
    import voicestats
    s = voicestats.stats(path)
    return dict(dur=s["dur"], f0=s["main"]["f0"], sd_st=s["main"]["sd_st"], db=s["main"]["db"], cen=s["main"]["cen"],
                voiced=s["main"]["voiced"], pauses=len(s["pauses"]))
def speech_span(path):
    """seconds between first and last sample above -40 dBFS-ish (10 ms frames) — speech length without edge silence"""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    y = np.frombuffer(raw, dtype=np.float32); w = 160; n = len(y) // w
    e = np.array([np.sqrt(np.mean(y[i*w:(i+1)*w]**2) + 1e-12) for i in range(n)]); db = 20*np.log10(e/(e.max()+1e-12))
    idx = np.where(db > -40)[0]
    return (float(idx[-1] - idx[0] + 1) * w / 16000, float(idx[0]*w/16000)) if len(idx) else (0.0, 0.0)
def ts_summary(res):
    ts = res.get("timestamps")
    if not ts: return "none"
    if isinstance(ts, list) and ts and isinstance(ts[0], dict):
        return "chars:" + ",".join(sorted(ts[0].keys()))[:80] + f" blocks={len(ts)}"
    if isinstance(ts, dict): return "dict:" + ",".join(sorted(ts.keys()))[:80]
    return type(ts).__name__

def qc_one(path):
    meta = json.load(open(path[:-4] + ".json")); it = meta["item"]; lang = it.get("lang", "en")
    try: hyp = transcribe(path, lang)
    except Exception as e: hyp = f"ERR {e}"
    span, lead = speech_span(path)
    words = len(norm(it["text"])) if lang == "en" else len(it["text"].split())
    r = dict(model=meta["model"], item=it["id"], take=path[-6:-4], chars=meta["chars"], wall_s=meta["wall_s"],
             gen_cps=round(meta["chars"] / meta["wall_s"], 1), est_usd=meta["est_usd"], speech_s=round(span, 2),
             lead_s=round(lead, 2), wpm=round(words / span * 60) if span else None,
             wer=round(wer(it["text"], hyp), 3) if lang == "en" else None, hyp=hyp,
             ts=ts_summary(meta["fal"]["result"]))
    if lang == "he":  # character error rate on letters only
        ref = re.sub(r"[^\u05d0-\u05ea]", "", it["text"]); h = re.sub(r"[^\u05d0-\u05ea]", "", hyp)
        d = list(range(len(h) + 1))
        for i in range(1, len(ref) + 1):
            prev, d[0] = d[0], i
            for j in range(1, len(h) + 1):
                cur = min(d[j] + 1, d[j - 1] + 1, prev + (ref[i - 1] != h[j - 1])); prev, d[j] = d[j], cur
        r["cer_he"] = round(d[len(h)] / max(1, len(ref)), 3)
    try: r.update(vstats(path))
    except Exception as e: r["vstats_err"] = str(e)[:120]
    return r

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        jobs = [(m, it, t) for t in range(1, TAKES + 1) for it in ITEMS for m in MODELS]  # interleave models
        with cf.ThreadPoolExecutor(3) as ex:
            for r in ex.map(lambda j: gen_one(*j), jobs): print(*r, flush=True)
    elif cmd == "qc":
        import glob
        fs = sorted(glob.glob(f"{P}/takes/*/*.mp3"))
        with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(qc_one, fs))
        os.makedirs(f"{P}/review", exist_ok=True)
        json.dump(res, open(f"{P}/review/qc.json", "w"), indent=1, ensure_ascii=False)
        for r in res: print(r["model"], r["item"], r["take"], r.get("wer"), r.get("cer_he"), r["wpm"], r["gen_cps"], r.get("sd_st"), "|", r["hyp"][:60])
