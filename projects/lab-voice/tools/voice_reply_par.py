#!/usr/bin/env python3
"""voice_reply_par.py - split the answer into sentence chunks, TTS them in
parallel, join the MP3s losslessly (ffmpeg concat, stream copy).

Usage: voice_reply_par.py "<text>" <out.mp3> [--model M] [--voice ID] [--workers N]
Uses previous_text/next_text so the prosody joins across chunks.
"""
import json, os, re, subprocess, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://api.elevenlabs.io/v1"
# Natural delivery without tags (tested 2026-10-06): freer than the 0.5 default, a little faster.
VOICE_SETTINGS = {"stability": 0.35, "similarity_boost": 0.75, "speed": 1.1}
DEFAULT_VOICE = "bIHbv24MWmeRgasZH58o"  # premade "Will": default until the principal picks the voice. He picked v4 Turbo (2026-10-06).


def chunks(text, target=160):
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    out, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) + 1 > target:
            out.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        out.append(cur)
    return out


def tts(i, parts, model, voice, key, tmp):
    body = {"text": parts[i], "model_id": model, "voice_settings": VOICE_SETTINGS}
    if i > 0:
        body["previous_text"] = " ".join(parts[:i])[-500:]
    if i < len(parts) - 1:
        body["next_text"] = " ".join(parts[i + 1:])[:500]
    req = urllib.request.Request(
        f"{API}/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    t0 = time.perf_counter()
    for attempt in range(4):
        try:
            data = urllib.request.urlopen(req, timeout=120).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(0.3 * (attempt + 1)); continue
            raise
    p = os.path.join(tmp, f"{i:03d}.mp3")
    open(p, "wb").write(data)
    return p, round(time.perf_counter() - t0, 2)


def main():
    args = sys.argv[1:]
    opts = {"--model": "eleven_v4_turbo", "--voice": DEFAULT_VOICE, "--workers": "4"}
    for k in list(opts):
        if k in args:
            i = args.index(k); opts[k] = args[i + 1]; del args[i:i + 2]
    text, out = args[0], args[1]
    key = os.environ["ELEVENLABS_API_KEY"]
    parts = chunks(text)
    tmp = tempfile.mkdtemp(prefix="vr_")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(int(opts["--workers"])) as ex:
        res = list(ex.map(lambda i: tts(i, parts, opts["--model"], opts["--voice"], key, tmp), range(len(parts))))
    t_tts = time.perf_counter() - t0
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p, _ in res))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", out], check=True)
    total = time.perf_counter() - t0
    print(json.dumps({"out": out, "model": opts["--model"], "chunks": len(parts),
                      "chunk_s": [s for _, s in res], "first_chunk_s": res[0][1],
                      "tts_s": round(t_tts, 2), "total_s": round(total, 2)}))


if __name__ == "__main__":
    main()
