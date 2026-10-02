#!/usr/bin/env python3
"""platecheck.py — automatic half of plate QA. The eye does the other half (it reads the sheets).

  $PY platecheck.py <plate.mp4> --slice <slice.wav> --song song.json --window A B [--offset O]
                    [--face x,y,w,h] [--out plates/qa/<id>]

Writes <out>.json and two images for me to read:
  <out>_mouth.jpg   — face crop at every word onset + mid-word, labeled with the word
  <out>_contact.jpg — 1 fps full-frame contact sheet
  <out>_sync.png    — slice vs plate soundtrack spectra + the match curve over time
Checks: duration vs slice (±1 frame); sync over time (syncdiverge.py: spectral lag, copy
strength, divergence point, suggested cut on the last eighth before it); frame rate, resolution.
sync verdict → check: in_sync → True; diverges → False (cut + cover, see sync.cut_song_s);
glitch → None (look at the mouth in the sync.check_by_eye spans);
no_copy / ambiguous → None (audio can't vouch: the mouth sheet decides).
Legacy onset-envelope lag kept as onset_lag_ms (it aliases on the beat period; don't gate on it).
A, B = the song-time window the slice covers; O = seconds of context pad before the shot.
"""
import sys, json, subprocess, os
import numpy as np, cv2
from scipy.signal import stft, correlate
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import syncdiverge

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)

def pcm(p, sr=16000):
    """Decode audio on the container timeline: a stream that starts late (start_time > video start) is
    padded with leading silence, so lag is measured the way a player would present it."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).copy()
    st = probe(p)["streams"]
    a = next((float(s.get("start_time", 0) or 0) for s in st if s["codec_type"] == "audio"), 0.0)
    v = next((float(s.get("start_time", 0) or 0) for s in st if s["codec_type"] == "video"), 0.0)
    d = a - v
    if d > 0: y = np.concatenate([np.zeros(int(d * sr), np.float32), y])
    elif d < 0: y = y[int(-d * sr):]
    return y, sr

def env(y, sr, hop=160):
    if len(y) < 1024: return np.zeros(1)
    _, _, Z = stft(y, fs=sr, nperseg=1024, noverlap=1024 - hop, boundary=None)
    S = np.log1p(50 * np.abs(Z)); e = np.maximum(0, np.diff(S, axis=1)).sum(0)
    return (e - e.mean()) / (e.std() + 1e-9)

def lag_ms(plate, sl):
    a, sr = pcm(plate); b, _ = pcm(sl)
    if len(a) < 1600: return None, 0.0
    ea, eb = env(a, sr), env(b, sr); n = min(len(ea), len(eb)); ea, eb = ea[:n], eb[:n]
    c = correlate(ea, eb, "full") / n; lags = np.arange(-n + 1, n); m = np.abs(lags) <= 50  # ±0.5 s
    i = np.argmax(c[m]); return float(lags[m][i] * 10), float(c[m][i])  # hop 10 ms

def frame_at(cap, t, fps):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps))); ok, f = cap.read(); return f if ok else None

def tile(imgs, labels, cols, w):
    cells = []
    for im, lb in zip(imgs, labels):
        if im is None: im = np.zeros((10, 10, 3), np.uint8)
        h = int(im.shape[0] * w / im.shape[1]); im = cv2.resize(im, (w, h))
        im = cv2.copyMakeBorder(im, 0, 28, 0, 0, cv2.BORDER_CONSTANT, value=(20, 20, 20))
        cv2.putText(im, lb[:24], (4, h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA); cells.append(im)
    if not cells: return None
    H = max(c.shape[0] for c in cells); cells = [cv2.copyMakeBorder(c, 0, H - c.shape[0], 0, 0, cv2.BORDER_CONSTANT) for c in cells]
    rows = [np.hstack(cells[i:i + cols] + [np.zeros_like(cells[0])] * (cols - len(cells[i:i + cols]))) for i in range(0, len(cells), cols)]
    return np.vstack(rows)

def main():
    a = sys.argv[1:]; opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    plate = a[0]; sl = opt("--slice"); song = opt("--song"); out = opt("--out", os.path.splitext(plate)[0] + "_qa")
    A, B = (float(x) for x in a[a.index("--window") + 1:a.index("--window") + 3]); off = float(opt("--offset", 0))
    pr = probe(plate); v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    num, den = v["r_frame_rate"].split("/"); fps = float(num) / float(den); dur = float(pr["format"]["duration"])
    rep = {"plate": plate, "fps": round(fps, 3), "size": [v["width"], v["height"]], "duration": round(dur, 3), "checks": {}}
    if sl:
        sdur = float(probe(sl)["format"]["duration"]); rep["slice_duration"] = round(sdur, 3)
        rep["checks"]["duration_ok"] = abs(dur - sdur) <= 1.0 / fps + 0.05
        has_audio = any(s["codec_type"] == "audio" for s in pr["streams"])
        if has_audio:
            l, peak = lag_ms(plate, sl); rep["onset_lag_ms"] = l; rep["onset_corr_peak"] = round(peak, 3)
            sy, data = syncdiverge.analyse(plate, sl, song, A)
            syncdiverge.plot(out + "_sync.png", data, sy["verdict"]); sy["plot"] = out + "_sync.png"
            rep["sync"] = sy; v = sy["verdict"]
            rep["audio_lag_ms"] = sy["lag_ms"] if v in ("in_sync", "diverges", "glitch") else None
            rep["checks"]["audio_lag_ok"] = abs(sy["lag_ms"]) <= 40 if v in ("in_sync", "diverges", "glitch") else None
            rep["checks"]["sync_ok"] = {"in_sync": True, "diverges": False}.get(v)
        else: rep["checks"]["audio_lag_ok"] = None; rep["checks"]["sync_ok"] = None
    cap = cv2.VideoCapture(plate)
    # mouth sheet
    if song:
        s = json.load(open(song)); fx = opt("--face"); crop = [int(x) for x in fx.split(",")] if fx else None
        imgs, labels = [], []
        for w in s["words"]:
            if A <= w["t0"] < B:
                for tt, tag in ((w["t0"], ""), ((w["t0"] + w["t1"]) / 2, "~")):
                    f = frame_at(cap, tt - A + off, fps)
                    if f is not None and crop: x, y, cw, ch = crop; f = f[y:y + ch, x:x + cw]
                    imgs.append(f); labels.append(f"{tag}{w['w']} {tt:.2f}")
        m = tile(imgs, labels, 8, 180)
        if m is not None: cv2.imwrite(out + "_mouth.jpg", m, [cv2.IMWRITE_JPEG_QUALITY, 85]); rep["mouth_sheet"] = out + "_mouth.jpg"
    # contact sheet 1 fps
    imgs = [frame_at(cap, t, fps) for t in np.arange(0, dur, 1.0)]
    c = tile(imgs, [f"{t:.0f}s" for t in np.arange(0, dur, 1.0)], 6, 320)
    if c is not None: cv2.imwrite(out + "_contact.jpg", c, [cv2.IMWRITE_JPEG_QUALITY, 85]); rep["contact_sheet"] = out + "_contact.jpg"
    rep["auto_pass"] = all(v is not False for v in rep["checks"].values())
    rep["eye_pending"] = ["mouth_sheet", "content"] + (["sync_by_eye"] if rep["checks"].get("sync_ok") is None else [])
    json.dump(rep, open(out + ".json", "w"), indent=1); print(json.dumps(rep))

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(0)
    main()
