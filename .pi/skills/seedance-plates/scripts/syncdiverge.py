#!/usr/bin/env python3
"""syncdiverge.py - time-resolved audio sync check for audio-conditioned video plates.

Why: Seedance copies @Audio1 into its own soundtrack, and the mouth follows that soundtrack.
Where the copy holds, the plate is in sync. Where it diverges (it re-sings, slips, or
generated SFX take over), the mouth drifts with it. One global lag hides this and aliases on
the beat period. Instead, this follows the match second by second, finds the divergence
point and proposes a cut there (method: knowledge/references/escape-velocity-case.md §1).

  $PY syncdiverge.py <plate.mp4> <slice.wav> [--out <prefix>] [--song song.json --song-t0 T]

It prints JSON and writes <prefix>_sync.png (slice spectrum / plate spectrum / match curve).

Features: log-mel (64 bands, 60-7600 Hz, 10 ms hop) with per-band mean removed on each
signal, so codec and EQ colour cancel out. Plates re-generate the audio rather than
copying it bit-exact (waveform NCC is only 0.05-0.36 on real plates), so the check
compares spectra, not waveforms.

  global:  lag in ±500 ms maximising mean frame cosine. copy = best - p90(null lags at 0.6-1.5 s).
           ambiguous when the runner-up peak (>=100 ms away) is within 80 % of the best,
           e.g. beat aliasing.
  curve:   400 ms windows, 10 ms hop, cosine at the global lag, plus a local best lag in
           ±120 ms. The threshold is p90 of the same curve at null lags + 0.12, with a
           floor of 0.25.
  diverge: the first run >= 250 ms below the threshold, or a run >= 250 ms where the
           local lag sits >= 60 ms off the global lag while still matching (a slip).
  verdict: in_sync      copy strong, no divergence
           diverges     copy strong until t_div, never back: cut before it, cover from that frame
           glitch       short drops that recover (held vowels, model SFX): look at the mouth
                        in check_by_eye spans; mouth hidden or on a hold -> keep
           no_copy      the plate's soundtrack does not follow the slice: audio can't
                        vouch for the mouth, so decide by eye
           ambiguous    two lags fit about equally: decide by eye

Sign: lag > 0 means the plate audio is late, so advance the picture by lag.
"""
import sys, json, os, subprocess
import numpy as np
from scipy.signal import stft

HOP_S = 0.01
WIN = 40          # 400 ms
LOCAL = 12        # ±120 ms local lag search
MIN_RUN = 25      # 250 ms
RECOVER = 50      # a drop followed by >= 500 ms back above threshold is a glitch, not a divergence
COPY_MIN = 0.15   # best - null p90 needed to call it a copy
AMBIG = 0.80


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def pcm(p, sr=16000):
    """Mono PCM on the container timeline (late-starting audio is padded, as a player shows it)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).copy()
    st = probe(p)["streams"]
    a = next((float(s.get("start_time", 0) or 0) for s in st if s["codec_type"] == "audio"), 0.0)
    v = next((float(s.get("start_time", 0) or 0) for s in st if s["codec_type"] == "video"), a)
    d = a - v
    if d > 0: y = np.concatenate([np.zeros(int(d * sr), np.float32), y])
    elif d < 0: y = y[int(-d * sr):]
    return y, sr


def _melfb(sr, n_fft, n_mels=64, fmin=60, fmax=7600):
    hz2m = lambda f: 2595 * np.log10(1 + f / 700); m2hz = lambda m: 700 * (10 ** (m / 2595) - 1)
    pts = m2hz(np.linspace(hz2m(fmin), hz2m(fmax), n_mels + 2)); b = np.floor((n_fft + 1) * pts / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        for k in range(b[i], b[i + 1]): fb[i, k] = (k - b[i]) / max(1, b[i + 1] - b[i])
        for k in range(b[i + 1], b[i + 2]): fb[i, k] = (b[i + 2] - k) / max(1, b[i + 2] - b[i + 1])
    return fb


def feat(y, sr, n=512):
    hop = int(sr * HOP_S)
    _, _, Z = stft(y, fs=sr, nperseg=n, noverlap=n - hop, boundary=None)
    L = np.log(_melfb(sr, n) @ (np.abs(Z) ** 2) + 1e-6)
    return L - L.mean(1, keepdims=True), L


def _cos(X, Y):
    n = min(X.shape[1], Y.shape[1]); X, Y = X[:, :n], Y[:, :n]
    return (X * Y).sum(0) / (np.linalg.norm(X, axis=0) * np.linalg.norm(Y, axis=0) + 1e-9)


def _pair(Fa, Fb, l):
    """l > 0: plate late -> plate frame t+l matches slice frame t. Returns aligned pair + slice-frame offset."""
    return (Fa[:, l:], Fb, 0) if l >= 0 else (Fa, Fb[:, -l:], -l)


def _curve(Fa, Fb, l, nfr):
    """Windowed cosine at lag l, indexed by slice frame (window centre); NaN where no overlap."""
    x, y, o = _pair(Fa, Fb, l); c = _cos(x, y)
    out = np.full(nfr, np.nan)
    if len(c) >= WIN:
        w = np.convolve(c, np.ones(WIN) / WIN, "valid")
        s = o + WIN // 2; out[s:s + len(w)] = w[:max(0, nfr - s)]
    return out


def _runs(mask):
    runs, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            runs.append((i, j)); i = j
        else: i += 1
    return runs


def analyse(plate, sl, song=None, song_t0=None):
    a, sr = pcm(plate); b, _ = pcm(sl)
    Fa, Ra = feat(a, sr); Fb, Rb = feat(b, sr); nfr = Fb.shape[1]
    lags = range(-50, 51)
    g = np.array([_cos(*_pair(Fa, Fb, l)[:2]).mean() for l in lags])
    ib = int(np.argmax(g)); lag = ib - 50; best = float(g[ib])
    far = [i for i in range(len(g)) if abs(i - ib) >= 10]
    j2 = max(far, key=lambda i: g[i]); second = (j2 - 50, float(g[j2]))
    nl = [l for l in range(-150, 151, 5) if 60 <= abs(l)]
    null_g = np.array([_cos(*_pair(Fa, Fb, l)[:2]).mean() for l in nl])
    copy = best - float(np.percentile(null_g, 90))
    ambiguous = second[1] >= AMBIG * best and best > 0
    switch = None
    if ambiguous:
        # Two lags fit. Beat aliasing: both fit the SAME stretches. A slip: one lag owns the
        # clip up to a point and the other owns it after. Then the in-sync reference is the
        # lag that owns the start, and the switch point is the divergence.
        c1, c2 = _curve(Fa, Fb, lag, nfr), _curve(Fa, Fb, second[0], nfr)
        d = c1 - c2; ok = ~np.isnan(d)
        r1 = [r for r in _runs(ok & (d > 0.10)) if r[1] - r[0] >= MIN_RUN]
        r2 = [r for r in _runs(ok & (d < -0.10)) if r[1] - r[0] >= MIN_RUN]
        if r1 and r2 and (r1[-1][0] < r2[0][0] or r2[-1][0] < r1[0][0]):
            first_is_1 = r1[0][0] < r2[0][0]
            if not first_is_1: lag, best, second = second[0], second[1], (lag, best)
            later = r2 if first_is_1 else r1
            switch = later[0][0]; ambiguous = False

    curve = _curve(Fa, Fb, lag, nfr)
    local = np.stack([_curve(Fa, Fb, lag + d, nfr) for d in range(-LOCAL, LOCAL + 1)])
    loc_best = np.nanmax(np.nan_to_num(local, nan=-9), 0); loc_lag = (np.argmax(np.nan_to_num(local, nan=-9), 0) - LOCAL) * 10
    null_w = np.concatenate([_curve(Fa, Fb, l, nfr) for l in (-120, -90, -70, 70, 90, 120)])
    thr = max(0.25, float(np.nanpercentile(null_w, 90)) + 0.12)

    valid = ~np.isnan(curve)
    low = valid & (curve < thr)
    slip = valid & (loc_best >= thr) & (np.abs(loc_lag) >= 60) & (curve < loc_best - 0.05)
    events = [(s, e, "drop") for s, e in _runs(low) if e - s >= MIN_RUN] + \
             [(s, e, "slip") for s, e in _runs(slip) if e - s >= MIN_RUN]
    if switch is not None:
        events.append((switch, nfr, "slip"))
        loc_lag[switch:] = (second[0] - lag) * 10  # report the slip size, beyond the ±120 ms local search
    events.sort()
    frac = float((curve[valid] >= thr).mean()) if valid.any() else 0.0
    good = valid & (curve >= thr)
    recovers = lambda e: any(r1 - r0 >= RECOVER for r0, r1 in _runs(good[e:]))
    hard = [ev for ev in events if not (ev[2] == "drop" and recovers(ev[1]))]
    glitches = [ev for ev in events if ev not in hard]

    if copy < COPY_MIN: verdict = "no_copy"
    elif ambiguous: verdict = "ambiguous"
    elif hard: verdict = "diverges"
    elif glitches: verdict = "glitch"
    else: verdict = "in_sync"

    rep = {"lag_ms": lag * 10, "match": round(best, 3), "copy_margin": round(copy, 3),
           "runner_up": {"lag_ms": second[0] * 10, "match": round(second[1], 3)},
           "threshold": round(thr, 3), "in_sync_fraction": round(frac, 3), "verdict": verdict,
           "events": [{"kind": k, "t0": round(s * HOP_S, 2), "t1": round(e * HOP_S, 2),
                       "median_local_lag_ms": int(np.median(loc_lag[s:e])),
                       "recovers": (s, e, k) in glitches} for s, e, k in events]}
    if glitches:
        rep["check_by_eye"] = [[round(s * HOP_S, 2), round(e * HOP_S, 2)] for s, e, _ in glitches]
    if verdict == "diverges":
        t_div = hard[0][0] * HOP_S; rep["t_div"] = round(t_div, 2)
        if song and song_t0 is not None:
            s = json.load(open(song)); beats = sorted(s.get("beats", []))
            eighths = sorted(beats + [(x + y) / 2 for x, y in zip(beats, beats[1:])])
            cut = max([e for e in eighths if e <= song_t0 + t_div - 0.02] or [song_t0])
            rep["cut_song_s"] = round(cut, 3); rep["cover_from_plate_s"] = round(cut - song_t0 + lag * HOP_S, 3)
            words = [w for w in s.get("words", []) if song_t0 <= w["t0"] < song_t0 + nfr * HOP_S]
            rep["words_before_cut"] = [w["w"] for w in words if w["t1"] <= cut]
            rep["words_to_cover"] = [w["w"] for w in words if w["t1"] > cut]
    return rep, (Ra, Rb, curve, loc_lag, thr, lag, events)


def plot(out, data, title):
    import cv2
    Ra, Rb, curve, loc_lag, thr, lag, events = data
    W, H = 1200, 170
    def spec(R, shift=0):
        R = R[:, max(0, shift):] if shift >= 0 else np.pad(R, ((0, 0), (-shift, 0)), constant_values=R.min())
        n = len(curve); R = R[:, :n] if R.shape[1] >= n else np.pad(R, ((0, 0), (0, n - R.shape[1])), constant_values=R.min())
        v = np.clip((R - np.percentile(R, 5)) / (np.percentile(R, 99) - np.percentile(R, 5) + 1e-9), 0, 1)
        im = cv2.applyColorMap((v[::-1] * 255).astype(np.uint8), cv2.COLORMAP_MAGMA)
        return cv2.resize(im, (W, H), interpolation=cv2.INTER_NEAREST)
    top, mid = spec(Rb), spec(Ra, lag)
    bot = np.full((220, W, 3), 22, np.uint8); n = len(curve); X = lambda i: int(i * W / max(1, n))
    Y = lambda v: int(200 - np.clip(v, -0.2, 1.0) * 170 - 34)
    for s, e, k in events:
        cv2.rectangle(bot, (X(s), 0), (X(e), 219), (40, 40, 110) if k == "drop" else (40, 90, 110), -1)
    cv2.line(bot, (0, Y(thr)), (W, Y(thr)), (255, 160, 80), 1)  # BGR: blue
    pts = [(X(i), Y(v)) for i, v in enumerate(curve) if not np.isnan(v)]
    for p, q in zip(pts, pts[1:]): cv2.line(bot, p, q, (120, 230, 120), 2)
    lp = [(X(i), int(200 - (np.clip(l, -120, 120) + 120) / 240 * 60)) for i, l in enumerate(loc_lag) if not np.isnan(curve[i])]
    for p, q in zip(lp, lp[1:]): cv2.line(bot, p, q, (200, 200, 200), 1)
    for t in range(0, int(n * HOP_S) + 1):
        cv2.putText(bot, f"{t}s", (X(t / HOP_S) + 2, 214), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1)
    lab = lambda im, s: cv2.putText(im, s, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    lab(top, "slice sent (@Audio1)"); lab(mid, f"plate soundtrack, aligned at {lag * 10:+d} ms")
    lab(bot, f"match (green) vs threshold {thr:.2f} (blue); local lag +-120 ms (grey); red = divergence   {title}")
    cv2.imwrite(out, np.vstack([top, mid, bot]))


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    plate, sl = a[0], a[1]; out = opt("--out", os.path.splitext(plate)[0])
    st0 = opt("--song-t0"); rep, data = analyse(plate, sl, opt("--song"), float(st0) if st0 else None)
    plot(out + "_sync.png", data, rep["verdict"]); rep["plot"] = out + "_sync.png"
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
