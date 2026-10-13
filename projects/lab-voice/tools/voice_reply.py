#!/usr/bin/env python3
"""voice_reply.py - turn a final text answer into a playable audio file, fast.

Usage: voice_reply.py "<text>" <out.mp3> [--model eleven_v4_turbo] [--voice <voice_id>]
Prints one JSON line with stage timings (seconds) and the output path.

Direct ElevenLabs streaming TTS -> MP3 (WhatsApp plays audio/mpeg inline as an
audio bubble; ogg/opus becomes a file card on this Vex adapter).
Key: ELEVENLABS_API_KEY (by name only).
"""
import json, os, sys, time, urllib.request

API = "https://api.elevenlabs.io/v1"
# Natural delivery without tags (tested 2026-10-06): freer than the 0.5 default, a little faster.
VOICE_SETTINGS = {"stability": 0.35, "similarity_boost": 0.75, "speed": 1.1}
DEFAULT_VOICE = "bIHbv24MWmeRgasZH58o"  # premade "Will": default until the principal picks the voice. He picked v4 Turbo (2026-10-06).


def main():
    args = sys.argv[1:]
    model, voice = "eleven_v4_turbo", DEFAULT_VOICE
    if "--model" in args:
        i = args.index("--model"); model = args[i + 1]; del args[i:i + 2]
    if "--voice" in args:
        i = args.index("--voice"); voice = args[i + 1]; del args[i:i + 2]
    text, out = args[0], args[1]
    key = os.environ["ELEVENLABS_API_KEY"]
    body = json.dumps({"text": text, "model_id": model, "voice_settings": VOICE_SETTINGS}).encode()
    req = urllib.request.Request(
        f"{API}/text-to-speech/{voice}/stream?output_format=mp3_44100_128",
        data=body, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    t0 = time.perf_counter()
    ttfb = None
    n = 0
    with urllib.request.urlopen(req, timeout=120) as r, open(out, "wb") as f:
        while True:
            chunk = r.read(8192)
            if not chunk:
                break
            if ttfb is None:
                ttfb = time.perf_counter() - t0
            f.write(chunk); n += len(chunk)
    total = time.perf_counter() - t0
    dur = n * 8 / 128000  # CBR 128k estimate
    print(json.dumps({"out": out, "model": model, "chars": len(text), "bytes": n,
                      "audio_s": round(dur, 1), "ttfb_s": round(ttfb or 0, 2),
                      "total_s": round(total, 2), "x_realtime": round(dur / total, 1)}))


if __name__ == "__main__":
    main()
