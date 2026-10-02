#!/usr/bin/env python3
"""eleven.py — ElevenLabs sound design for Muse (stdlib only). Needs ELEVENLABS_API_KEY.

  eleven.py sfx "<prompt>" <out.mp3> [--dur 1.5] [--influence 0.4] [--loop] [--ledger L --tag T]
  eleven.py music "<prompt>" <out.mp3> --ms 30000 [--ledger L --tag T]
  eleven.py isolate <in_audio> <out.mp3>                      # voice isolation (clean vocal stem)
  eleven.py usage                                              # character/credit balance

Sound effects: POST /v1/sound-generation {text, duration_seconds (0.5-30), prompt_influence (0-1), loop}.
Music: POST /v1/music {prompt, music_length_ms}. Isolation: POST /v1/audio-isolation (multipart).
Each call appends a ledger line (credits are the unit ElevenLabs bills; est_usd left null).
"""
import json, os, sys, time, urllib.request, urllib.error, uuid

API = "https://api.elevenlabs.io"
KEY = os.environ.get("ELEVENLABS_API_KEY", "")

def die(m): print(json.dumps({"error": m}), file=sys.stderr); sys.exit(1)

def post(path, body=None, files=None, accept="audio/mpeg"):
    if not KEY: die("ELEVENLABS_API_KEY not set — ask the principal for a secure handoff")
    h = {"xi-api-key": KEY, "Accept": accept}
    if files:
        b = "----" + uuid.uuid4().hex; data = bytearray()
        for name, (fn, content, ctype) in files.items():
            data += f"--{b}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{fn}\"\r\nContent-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n"
        data += f"--{b}--\r\n".encode(); h["Content-Type"] = f"multipart/form-data; boundary={b}"
    else:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=bytes(data), headers=h, method="POST")
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as r: return r.read()
        except urllib.error.HTTPError as e:
            t = e.read().decode(errors="replace")[:1500]
            if e.code in (429, 500, 502, 503) and i < 3: time.sleep(4 * (i + 1)); continue
            die(f"HTTP {e.code} {path}: {t}")

def ledger(path, rec):
    if not path: return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a") as f: f.write(json.dumps(rec) + "\n")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    cmd = a[0]; t0 = time.time()
    if cmd == "sfx":
        body = {"text": a[1], "prompt_influence": float(opt("--influence", 0.4)), "loop": "--loop" in a}
        if opt("--dur"): body["duration_seconds"] = float(opt("--dur"))
        out = post("/v1/sound-generation", body); open(a[2], "wb").write(out)
        ledger(opt("--ledger"), {"ts": int(t0), "endpoint": "elevenlabs/sound-generation", "tag": opt("--tag"), "prompt": a[1], "file": a[2], "est_usd": None})
        print(a[2])
    elif cmd == "music":
        out = post("/v1/music", {"prompt": a[1], "music_length_ms": int(opt("--ms", 30000))}); open(a[2], "wb").write(out)
        ledger(opt("--ledger"), {"ts": int(t0), "endpoint": "elevenlabs/music", "tag": opt("--tag"), "prompt": a[1], "file": a[2], "est_usd": None})
        print(a[2])
    elif cmd == "isolate":
        out = post("/v1/audio-isolation", files={"audio": (os.path.basename(a[1]), open(a[1], "rb").read(), "audio/mpeg")})
        open(a[2], "wb").write(out); print(a[2])
    elif cmd == "usage":
        req = urllib.request.Request(API + "/v1/user/subscription", headers={"xi-api-key": KEY})
        d = json.load(urllib.request.urlopen(req)); print(json.dumps({k: d.get(k) for k in ("tier", "character_count", "character_limit", "next_character_count_reset_unix")}))
    else: print(__doc__)
