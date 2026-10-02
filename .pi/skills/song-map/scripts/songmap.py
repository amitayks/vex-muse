#!/usr/bin/env python3
"""songmap.py — turn an audio file (+ optional lyrics) into song.json, the timing spine of a video.

  $PY songmap.py analyze <audio> --out song.json [--lyrics lyrics.txt] [--bpm 120] [--no-words]
                         [--vocals vocals.mp3] [--drums drums.mp3]   # stems from fal-ai/demucs: much better words/beats
                         [--beats beats.json]                        # beat_this grid (modal_audio.py::beats) replaces the DP tracker
                         [--lrc lyrics_lines.json]                   # LRCLIB line times (musiclib.py lyrics): fills missed lines + reports drift
  $PY songmap.py eval song.json [--ref beats.json] [--lrc lyrics_lines.json] [--bpm-true 116] [--key-true "F# minor"]
  $PY songmap.py slice <audio> <t0> <t1> <out.wav|mp3> [--pad 0.0]     # exact segment (Seedance audio ref)
  $PY songmap.py grid song.json [--from 0 --to 30]                      # print beats/bars/words for a window
  $PY songmap.py click song.json <audio> <out.wav>                      # song + clicks on beats + blips on word onsets (sync QA by ear)

Beat/tempo: spectral-flux onset envelope -> tempo by autocorrelation (60-200 BPM, --bpm overrides)
-> dynamic-programming beat tracker (Ellis 2007). Downbeats: phase of the 4-beat grouping with the
strongest low-band accent. Sections: novelty over a self-similarity matrix of beat-synchronous
log-spectra, snapped to bars, grouped by similarity (A/B/C) with a label guess. Key: harmonic chroma vs
Krumhansl-Kessler + Temperley profiles. Loudness: ffmpeg ebur128 (LUFS-I, true peak). Hits: strongest
broadband transients; drops/breaks: +/-5 dB energy jumps at downbeats. Energy: RMS at 10 Hz. Words: OpenAI transcription with word
timestamps (OPENAI_API_KEY), then aligned onto the given lyrics so spelling is the song's, not
whisper's. Needs ffmpeg on PATH and numpy/scipy (tools/py).
"""
import sys, os, json, subprocess, difflib, re, urllib.request, uuid
import numpy as np
from scipy.signal import stft, find_peaks
from scipy.ndimage import uniform_filter1d, median_filter

SR = 22050; HOP = 256
LAT = 1024 / SR   # onset-env frames are stamped at their START; the 2048-pt window centre is 46 ms later (measured: DP grid was 52 ms early vs kicks)

def load(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def onset_env(y):
    f, t, Z = stft(y, fs=SR, nperseg=2048, noverlap=2048 - HOP, boundary=None)
    S = np.log1p(100 * np.abs(Z))
    flux = np.maximum(0, np.diff(S, axis=1)).sum(axis=0)
    flux = np.concatenate([[0], flux])
    flux = flux - uniform_filter1d(flux, 16)
    flux = np.maximum(flux, 0)
    low = np.maximum(0, np.diff(S[f < 200], axis=1)).sum(axis=0); low = np.concatenate([[0], low])
    return flux / (flux.max() + 1e-9), low, S, f

def tempo(env, fps, lo=60, hi=200, prior=110):
    """Autocorrelation tempo with harmonic summation: a true beat period P also shows peaks at 2P and 4P,
    while a 3/2 or 2x false tempo does not line up with the bar. Returns (bpm, candidates)."""
    e = env - env.mean()
    ac = np.correlate(e, e, "full")[len(e) - 1:]; ac = ac / (ac[0] + 1e-9)
    def at(l):
        i = int(round(l)); return ac[i] if 0 < i < len(ac) else 0.0
    cands = []
    for bpm in np.arange(lo, hi, 0.25):
        P = 60 * fps / bpm
        s = at(P) + 0.5 * at(2 * P) + 0.5 * at(4 * P) + 0.25 * at(8 * P)
        s *= np.exp(-0.5 * (np.log2(bpm / prior) / 1.2) ** 2)
        cands.append((s, bpm))
    cands.sort(reverse=True)
    return float(cands[0][1]), [round(b, 2) for _, b in cands[:12:3]]

def beat_track(env, fps, bpm, tight=100):
    period = 60 * fps / bpm; n = len(env)
    score = env.copy(); back = np.full(n, -1)
    lo, hi = int(round(period / 2)), int(round(period * 2))
    for i in range(n):
        a, b = max(0, i - hi), i - lo
        if b <= a: continue
        prev = np.arange(a, b)
        pen = -tight * (np.log((i - prev) / period)) ** 2
        j = np.argmax(score[prev] + pen)
        score[i] += score[prev][j] + pen[j]; back[i] = prev[j]
    # start from best in last period
    i = int(np.argmax(score[-int(period):]) + n - int(period)); beats = []
    while i >= 0: beats.append(i); i = back[i]
    return np.array(beats[::-1]) / fps + LAT

def chord_change(y, beats):
    """Per-beat harmonic change (chroma distance to the previous beat): chords move on bar lines."""
    f, t, Z = stft(y, fs=SR, nperseg=4096, noverlap=4096 - 1024, boundary=None); t = t + 2048 / SR
    sel = (f >= 80) & (f <= 2000); M = np.abs(Z[sel]); pc = np.round(69 + 12 * np.log2(f[sel] / 440)).astype(int) % 12
    ch = np.array([M[pc == p].sum(0) for p in range(12)]); ch /= ch.sum(0, keepdims=True) + 1e-9; B = []
    for a, b in zip(beats, np.r_[beats[1:], beats[-1] + 0.5]):
        m = (t >= a) & (t < b); B.append(ch[:, m].mean(1) if m.any() else np.zeros(12))
    return np.r_[0, np.linalg.norm(np.diff(np.array(B), axis=0), axis=1)]

def fit_tempo(beats, bpm_hint=None):
    """Tempo from a least-squares line through the beat grid (frame-quantised IBIs bias the median, e.g. 128 reads 129.2).
    Returns (bpm, residual_ms): the residual measures tempo drift/wobble of the performance."""
    b = np.asarray(beats, float)
    if len(b) < 6: return (round(float(bpm_hint), 2) if bpm_hint else None), None
    lo, hi = int(len(b) * 0.1), int(len(b) * 0.9) or len(b); i = np.arange(len(b))[lo:hi]; t = b[lo:hi]
    k, c = np.polyfit(i, t, 1); res = t - (k * i + c)
    return round(float(60 / k), 2), round(float(1000 * np.std(res)), 1)

def downbeats(beats, low, fps, per_bar=4, y=None):
    """Bar phase = z(bass accent) + z(chord change). Measured: needs the DRUM STEM as `low` source (mix-only picks
    the wrong phase on four-on-the-floor songs); without stems prefer beat_this (modal_audio.py::beats)."""
    idx = np.clip(((beats - LAT) * fps).round().astype(int), 0, len(low) - 1); acc = low[idx]
    z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
    sc = z(np.array([acc[p::per_bar].mean() if len(acc[p::per_bar]) else 0 for p in range(per_bar)]))
    if y is not None:
        c = chord_change(y, beats); sc = sc + z(np.array([c[p::per_bar].mean() for p in range(per_bar)]))
    return beats[int(np.argmax(sc))::per_bar]

PC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
PROFILES = {  # Krumhansl-Kessler and Temperley (Kostka-Payne) key profiles
    "kk": ([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]),
    "temperley": ([.748, .060, .488, .082, .670, .460, .096, .715, .104, .366, .057, .400], [.712, .084, .474, .618, .049, .460, .105, .747, .404, .067, .133, .330])}

def key_detect(y):
    """Global key from harmonic chroma (median-filtered spectrogram, 110-4200 Hz) correlated with two profile sets."""
    f, t, Z = stft(y, fs=SR, nperseg=8192, noverlap=8192 - 2048, boundary=None)
    sel = (f >= 110) & (f <= 4200); M = np.abs(Z[sel]); H = median_filter(M, size=(1, 9))
    pc = np.round(69 + 12 * np.log2(f[sel] / 440)).astype(int) % 12
    ch = np.array([H[pc == p].sum(0) for p in range(12)]); ch = ch / (ch.sum(0, keepdims=True) + 1e-9)
    w = H.sum(0); c = (ch * w).sum(1) / (w.sum() + 1e-9)
    scores = []
    for tonic in range(12):
        for mode, idx in (("major", 0), ("minor", 1)):
            r = np.mean([np.corrcoef(np.roll(PROFILES[p][idx], tonic), c)[0, 1] for p in PROFILES])
            scores.append((float(r), f"{PC[tonic]} {mode}"))
    scores.sort(reverse=True)
    # relative major/minor share a pitch set: the tonic is the more frequent BASS note (55-220 Hz chroma)
    f2, _, Z2 = stft(y, fs=SR, nperseg=16384, noverlap=16384 - 4096, boundary=None)
    bs = (f2 >= 55) & (f2 <= 220); B = median_filter(np.abs(Z2[bs]), size=(1, 5))
    bpc = np.round(69 + 12 * np.log2(f2[bs] / 440)).astype(int) % 12; bass = np.array([B[bpc == p].sum() for p in range(12)]); bass /= bass.sum() + 1e-9
    (s1, k1), (s2, k2) = scores[0], scores[1]
    t1, m1 = PC.index(k1.split()[0]), k1.split()[1]; t2, m2 = PC.index(k2.split()[0]), k2.split()[1]
    rel = m1 != m2 and ((m1 == "major" and (t1 + 9) % 12 == t2) or (m1 == "minor" and (t1 + 3) % 12 == t2))
    if rel and s1 - s2 < 0.1 and bass[t2] > bass[t1] * 1.15: scores[0], scores[1] = scores[1], scores[0]
    return scores[0][1], round(abs(scores[0][0] - scores[1][0]), 3), [s for _, s in scores[:3]], [round(float(x), 4) for x in c]

def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    I = re.search(r"I:\s+(-?[\d.]+) LUFS", tail); P = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail); L = re.search(r"LRA:\s+([\d.]+) LU", tail)
    return {"lufs": float(I.group(1)) if I else None, "true_peak_db": float(P.group(1)) if P and P.group(1) != "-inf" else None, "lra": float(L.group(1)) if L else None}

def hits_and_drops(env, low, energy, beats, dbs, fps, bpm, n=16):
    """hits: strongest broadband+low transients (beat-snapped within 60 ms); drops/breaks: >= +/-5 dB 2-bar energy jumps at downbeats."""
    lowb = low / (low.max() + 1e-9); comb = env + 0.5 * lowb
    pk, pr = find_peaks(comb, distance=int(0.25 * fps), prominence=0.15)
    top = pk[np.argsort(-pr["prominences"])][:n]; hits = []
    for i in sorted(top):
        t = i / fps + LAT; j = int(np.argmin(np.abs(beats - t))) if len(beats) else None
        if j is not None and abs(beats[j] - t) < 0.06: t = float(beats[j])
        hits.append({"t": round(float(t), 3), "strength": round(float(comb[i]), 3)})
    e = np.asarray(energy); bar = 4 * 60 / bpm; changes = []
    for d in dbs:
        a, b, c = int((d - 2 * bar) * 10), int(d * 10), int((d + 2 * bar) * 10)
        if a < 0 or c > len(e): continue
        pre, post = e[a:b].mean() + 1e-4, e[b:c].mean() + 1e-4; db = 20 * np.log10(post / pre)
        if abs(db) >= 5: changes.append({"t": round(float(d), 3), "kind": "drop" if db > 0 else "break", "db": round(float(db), 1)})
    return hits, changes

def label_sections(sec_objs, F, beats):
    """Group sections by timbre/harmony similarity (A, B, ...) and guess labels: most-repeated loud group = chorus."""
    vecs = []
    for s in sec_objs:
        m = (beats[:-1] >= s["t0"]) & (beats[:-1] < s["t1"]); v = F[m[:len(F)]].mean(0) if m[:len(F)].any() else np.zeros(F.shape[1])
        vecs.append(v / (np.linalg.norm(v) + 1e-9))
    groups = []
    for i, v in enumerate(vecs):
        g = next((groups[j] for j in sorted(range(i), key=lambda j: -float(v @ vecs[j])) if float(v @ vecs[j]) > 0.7), None)
        groups.append(g if g is not None else chr(65 + len(set(groups))))
    for s, g in zip(sec_objs, groups): s["group"] = g
    med = float(np.median([s["energy"] for s in sec_objs])) if sec_objs else 0
    rep = {g: [s for s in sec_objs if s["group"] == g] for g in set(groups)}
    loud = sorted([g for g in rep if len(rep[g]) >= 2], key=lambda g: -np.mean([s["energy"] for s in rep[g]]))
    chorus = loud[0] if loud and np.mean([s["energy"] for s in rep[loud[0]]]) >= med else None
    for i, s in enumerate(sec_objs):
        if s["group"] == chorus: s["label"] = "chorus"
        elif i == 0 and s["energy"] < med: s["label"] = "intro"
        elif i == len(sec_objs) - 1 and s["energy"] < med: s["label"] = "outro"
        elif len(rep[s["group"]]) >= 2: s["label"] = "verse"
        else: s["label"] = "bridge" if s["energy"] < med else "drop"
        s["label_guess"] = True
    return sec_objs

def sections(y, beats, bars, fps):
    f, t, Z = stft(y, fs=SR, nperseg=4096, noverlap=4096 - HOP * 2, boundary=None)
    S = np.log1p(np.abs(Z[(f > 40) & (f < 8000)]))
    bins = np.linspace(0, S.shape[0], 48).astype(int)
    S = np.array([S[bins[i]:bins[i + 1]].mean(0) for i in range(47)])
    tt = t
    feats = []
    for a, b in zip(beats[:-1], beats[1:]):
        m = (tt >= a) & (tt < b)
        feats.append(S[:, m].mean(1) if m.any() else np.zeros(47))
    F = np.array(feats); F = (F - F.mean(0)) / (F.std(0) + 1e-9)
    F /= np.linalg.norm(F, axis=1, keepdims=True) + 1e-9
    SSM = F @ F.T; k = 32 if len(F) >= 192 else 16   # half-kernel of 8 bars (4 on short cues): pop sections are 8/16 bars
    kern = np.outer(np.r_[np.ones(k), -np.ones(k)], np.r_[np.ones(k), -np.ones(k)]) * np.outer(np.hanning(2 * k), np.hanning(2 * k))
    nov = np.zeros(len(F))
    for i in range(k, len(F) - k): nov[i] = (SSM[i - k:i + k, i - k:i + k] * kern).sum()
    nov = np.maximum(nov, 0)
    pk, _ = find_peaks(nov, distance=2 * k if k == 16 else k, height=np.percentile(nov, 60) if nov.any() else 0)
    bounds = sorted(set([0.0] + [float(beats[p]) for p in pk] + [float(beats[-1])]))
    snapped = sorted(set(float(bars[np.argmin(np.abs(bars - b))]) for b in bounds)) if len(bars) else bounds
    return snapped, F

def lead_silence(path, db=-45.0):
    """Seconds before the first 100 ms frame above `db` dBFS (vocal stems of songs with long intros)."""
    y = load(path, 16000); n = 1600; r = [np.sqrt(np.mean(y[i:i + n] ** 2) + 1e-12) for i in range(0, len(y) - n, n)]
    on = next((i for i, v in enumerate(r) if 20 * np.log10(v) > db), 0); return max(0.0, on * 0.1 - 0.5)

def chunk_points(path, max_len=28.0):
    """Cut points (s) at the quietest 100 ms inside each <=max_len window: whisper's timestamps are only trustworthy
    inside its native 30 s window (measured: a 4-min vocal stem drifted 2-17 s when sent whole)."""
    y = load(path, 16000); n = 1600; r = np.array([np.sqrt(np.mean(y[i:i + n] ** 2) + 1e-12) for i in range(0, len(y) - n, n)])
    dur = len(y) / 16000; pts = [lead_silence(path)]
    while dur - pts[-1] > max_len:
        a, b = int((pts[-1] + max_len * 0.5) * 10), int((pts[-1] + max_len) * 10)
        pts.append(round((a + int(np.argmin(r[a:b]))) / 10, 2))
    return pts + [dur]

def transcribe(path, offset=None):
    """whisper-1 word timestamps, transcribed in <=28 s chunks cut at vocal gaps (parallel), offsets added back."""
    if not os.environ.get("OPENAI_API_KEY"): return None
    pts = chunk_points(path) if offset is None else [offset, 1e9]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as ex: parts = list(ex.map(lambda ab: transcribe_one(path, ab[0], ab[1]), zip(pts[:-1], pts[1:])))
    words = [w for p in parts for w in p.get("words", [])]; segs = [s for p in parts for s in p.get("segments", [])]
    return {"text": " ".join(p.get("text", "") for p in parts), "words": words, "segments": segs, "offset": round(pts[0], 2), "chunks": len(parts)}

def transcribe_one(path, off, end):
    key = os.environ.get("OPENAI_API_KEY")
    b = "----" + uuid.uuid4().hex; body = bytearray()
    def field(n, v): body.extend(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    field("model", "whisper-1"); field("response_format", "verbose_json")
    field("timestamp_granularities[]", "word"); field("timestamp_granularities[]", "segment")
    mp3 = "/tmp/_songmap_" + uuid.uuid4().hex + ".mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{off:.3f}", "-i", path, "-t", f"{min(end - off, 3600):.3f}", "-ac", "1", "-b:a", "64k", mp3], check=True)
    body.extend(f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode())
    body.extend(open(mp3, "rb").read()); body.extend(f"\r\n--{b}--\r\n".encode()); os.remove(mp3)
    req = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=bytes(body),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={b}"})
    for attempt in range(3):
        try: tr = json.load(urllib.request.urlopen(req, timeout=180)); break
        except Exception:
            if attempt == 2: raise
            import time as _t; _t.sleep(3 * (attempt + 1))
    for w in tr.get("words", []): w["start"] += off; w["end"] += off
    for s in tr.get("segments", []): s["start"] += off; s["end"] += off
    tr["offset"] = round(off, 2); return tr

norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())

def align(words, lyrics):
    """Map whisper words onto lyric tokens; interpolate times for lyric words whisper missed."""
    lines = [l.strip() for l in lyrics.splitlines() if l.strip() and not l.strip().startswith("[")]
    toks = [(li, w) for li, l in enumerate(lines) for w in l.split()]
    A = [norm(w["word"]) for w in words]; B = [norm(w) for _, w in toks]
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False); times = [None] * len(toks)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): times[blk.b + k] = (words[blk.a + k]["start"], words[blk.a + k]["end"], True)
    # interpolate gaps
    known = [i for i, t in enumerate(times) if t]
    for i, t in enumerate(times):
        if t: continue
        p = max([k for k in known if k < i], default=None); n = min([k for k in known if k > i], default=None)
        if p is not None and n is not None:
            a, b = times[p][1], times[n][0]; frac = (i - p) / (n - p)
            s = a + (b - a) * frac; times[i] = (s, s + max(0.12, (b - a) / (n - p)), False)
        elif p is not None: times[i] = (times[p][1], times[p][1] + 0.25, False)
        elif n is not None: times[i] = (max(0, times[n][0] - 0.25), times[n][0], False)
    out = [{"w": w, "t0": round(t[0], 3), "t1": round(t[1], 3), "line": li, "matched": t[2]} for (li, w), t in zip(toks, times) if t]
    L = []
    for li, l in enumerate(lines):
        ws = [w for w in out if w["line"] == li]
        if ws: L.append({"i": li, "text": l, "t0": ws[0]["t0"], "t1": ws[-1]["t1"]})
    cov = sum(1 for w in out if w["matched"]) / max(1, len(out))
    return out, L, round(cov, 3)

def align_lrc(words, lrc):
    """Align whisper words line by line inside each LRCLIB line's window [t_i - 1.5, t_(i+1) + 0.5]: repeated choruses
    can't be matched to the wrong repetition. Unmatched words are spread between their matched neighbours or from
    the LRC line time."""
    lines = [dict(l) for l in lrc if re.search(r"[A-Za-z0-9]", l["text"])]; out, L = [], []
    shift = lrc_offset(words, lines)
    for l in lines: l["t"] = round(l["t"] + shift, 3)
    used_until = -1.0
    for i, l in enumerate(lines):
        t0 = l["t"]; t1 = lines[i + 1]["t"] if i + 1 < len(lines) else t0 + 8
        # monotonic: a repeated chorus line may not reuse the previous line's words
        cand = [w for w in words if max(t0 - 1.5, used_until) <= w["start"] < t1 + 0.5]; toks = l["text"].split()
        sm = difflib.SequenceMatcher(a=[norm(w["word"]) for w in cand], b=[norm(x) for x in toks], autojunk=False)
        times = [None] * len(toks)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size): times[blk.b + k] = (cand[blk.a + k]["start"], cand[blk.a + k]["end"], True)
        known = [k for k, t in enumerate(times) if t]
        for k in range(len(toks)):
            if times[k]: continue
            p = max([j for j in known if j < k], default=None); n = min([j for j in known if j > k], default=None)
            if p is not None and n is not None: a, b = times[p][1], times[n][0]; s = a + (b - a) * (k - p) / (n - p)
            elif p is not None: s = times[p][1] + 0.2 * (k - p)
            elif n is not None: s = max(t0, times[n][0] - 0.25 * (n - k))
            else: s = t0 + k * min(0.35, (t1 - t0) / max(1, len(toks)))
            times[k] = (s, s + 0.2, False)
        ws = [{"w": w, "t0": round(t[0], 3), "t1": round(t[1], 3), "line": i, "matched": t[2]} for w, t in zip(toks, times)]
        if any(w["matched"] for w in ws): used_until = max(w["t0"] for w in ws if w["matched"]) + 0.05
        out += ws; L.append({"i": i, "text": l["text"], "t0": ws[0]["t0"], "t1": ws[-1]["t1"], "lrc_t": t0, "heard": ws[0]["matched"]})
    cov = sum(1 for w in out if w["matched"]) / max(1, len(out))
    for x in L: x["lrc_shift"] = shift
    return out, L, round(cov, 3)

def lrc_offset(words, lines):
    """LRC timings often belong to ANOTHER edit of the song (measured: LRCLIB's Get Lucky lines are the album edit,
    16 s late on the 4:08 radio edit). Offset = the most common (whisper time - LRC time) over every place a line's
    first three words occur in the transcript, histogrammed at 0.5 s."""
    W = [norm(w["word"]) for w in words]; deltas = []
    for l in lines:
        k = [norm(x) for x in l["text"].split()][:3]
        if len(k) < 2: continue
        for j in range(len(W) - len(k) + 1):
            if W[j:j + len(k)] == k: deltas.append(words[j]["start"] - l["t"])
    if len(deltas) < 3: return 0.0
    d = np.round(np.array(deltas) * 2) / 2; vals, cnt = np.unique(d, return_counts=True)
    best = vals[np.argmax(cnt)]; near = np.array(deltas)[np.abs(np.array(deltas) - best) <= 0.5]
    return round(float(np.median(near)), 2) if abs(best) >= 0.25 else 0.0

def snap_to_onsets(words, vocals, win=0.15):
    """Pull each word start onto the nearest vocal onset within +-win s (whisper drifts on sung audio)."""
    v = load(vocals); fps = SR / HOP
    env, _, _, _ = onset_env(v)
    pk, _ = find_peaks(env, height=0.08, distance=int(0.06 * fps)); pt = pk / fps + LAT
    moved = 0
    for w in words:
        if not len(pt): break
        j = np.argmin(np.abs(pt - w["t0"]))
        if abs(pt[j] - w["t0"]) <= win:
            if abs(pt[j] - w["t0"]) > 0.02: moved += 1
            w["t0"] = round(float(pt[j]), 3); w["t1"] = max(w["t1"], w["t0"] + 0.08)
    return moved

def analyze(path, out, lyrics=None, bpm=None, words=True, vocals=None, drums=None, beats_json=None, lrc=None):
    y = load(path); dur = len(y) / SR; fps = SR / HOP
    env, low, S, f = onset_env(load(drums) if drums else y)
    env_mix, low_mix, _, _ = onset_env(y) if drums else (env, low, None, None)
    cands = []; grid_src = "dp"
    if beats_json:
        bj = json.load(open(beats_json)); beats = np.array(bj["beats"]); dbs = np.array(bj["downbeats"]); grid_src = bj.get("model", "external")
        bpm = float(bpm) if bpm else fit_tempo(beats)[0]   # beat_this is 50 fps: a median IBI reads 171 as 166.67
        _, cands = tempo(env, fps)
    else:
        if bpm: bpm = float(bpm)
        else: bpm, cands = tempo(env, fps)
        beats = beat_track(env, fps, bpm, tight=400)
        dbs = downbeats(beats, low, fps, y=y)
    bpm_tracked, grid_resid = fit_tempo(beats, bpm)
    secs, F = sections(y, beats, dbs, fps)
    frame = int(SR / 10); rms = [float(np.sqrt(np.mean(y[i:i + frame] ** 2))) for i in range(0, len(y), frame)]
    mx = max(rms) or 1; energy = [round(r / mx, 3) for r in rms]
    sec_objs = []
    for a, b in zip(secs[:-1], secs[1:]):
        e = energy[int(a * 10):int(b * 10)] or [0]
        sec_objs.append({"t0": round(a, 3), "t1": round(b, 3), "bars": int(round((b - a) / (4 * 60 / bpm))), "energy": round(float(np.mean(e)), 3), "label": None})
    label_sections(sec_objs, F, beats)
    key, key_conf, key_top, chroma = key_detect(y); key_src = "profiles"
    try:  # Essentia EDMA profile (measured 3 songs: better than KK/Temperley on the one they disagreed on); optional dep
        import essentia, essentia.standard as es; essentia.log.infoActive = False; essentia.log.warningActive = False
        a44 = es.MonoLoader(filename=path, sampleRate=44100)(); ek, escale, estr = es.KeyExtractor(profileType="edma")(a44)
        ek = f"{ek} {escale}".replace("Bb", "A#").replace("Eb", "D#").replace("Ab", "G#").replace("Db", "C#").replace("Gb", "F#")
        key_top = [ek] + [k for k in key_top if k != ek][:2]; key, key_conf, key_src = ek, round(float(estr), 3), "essentia-edma"
    except Exception: pass
    hits, changes = hits_and_drops(env_mix, low_mix, energy, beats, dbs, fps, bpm)
    song = {"source": os.path.basename(path), "duration": round(dur, 3), "bpm": round(float(bpm), 2), "bpm_candidates": cands, "bpm_tracked": bpm_tracked, "grid_resid_ms": grid_resid,
            "grid_source": grid_src, "key": key, "key_confidence": key_conf, "key_source": key_src, "key_candidates": key_top, "chroma": chroma, **loudness(path),
            "beat": round(60 / bpm, 4), "beats": [round(float(b), 3) for b in beats],
            "downbeats": [round(float(b), 3) for b in dbs], "sections": sec_objs, "hits": hits, "energy_changes": changes, "energy_10hz": energy,
            "words": [], "lines": [], "lyric_coverage": None}
    if words:
        tr = transcribe(vocals or path)
        if tr:
            ws = tr.get("words", []); song["asr_offset"] = tr.get("offset")
            if lrc:
                song["words"], song["lines"], song["lyric_coverage"] = align_lrc(ws, json.load(open(lrc))); song["alignment"] = "lrc-anchored"
            elif lyrics:
                song["words"], song["lines"], song["lyric_coverage"] = align(ws, open(lyrics).read())
            else:
                song["words"] = [{"w": w["word"], "t0": round(w["start"], 3), "t1": round(w["end"], 3), "line": None, "matched": True} for w in ws]
                song["lines"] = [{"i": i, "text": s["text"].strip(), "t0": round(s["start"], 3), "t1": round(s["end"], 3)} for i, s in enumerate(tr.get("segments", []))]
            if vocals and song["words"]:
                song["onset_snapped"] = snap_to_onsets(song["words"], vocals)
                for L in song["lines"]:
                    ws = [w for w in song["words"] if w["line"] == L["i"]]
                    if ws: L["t0"], L["t1"] = ws[0]["t0"], ws[-1]["t1"]
    if lrc and song["lines"]:
        song["lrc_check"] = lrc_compare(song["lines"], json.load(open(lrc)))
    json.dump(song, open(out, "w"), indent=1)
    print(json.dumps({k: song.get(k) for k in ("duration", "bpm", "bpm_tracked", "bpm_candidates", "key", "key_confidence", "lufs", "true_peak_db", "lyric_coverage", "lrc_check")}
                     | {"beats": len(song["beats"]), "sections": [f"{s['t0']:.0f}-{s['t1']:.0f} {s['group']}:{s['label']}" for s in sec_objs], "drops": [c for c in changes if c['kind'] == 'drop'][:6], "words": len(song["words"])}))

def lrc_compare(lines, lrc):
    """Match song lines to LRCLIB lines by text order; report start-time differences (LRC is human-timed, ~0.1-0.3 s)."""
    shift = lines[0].get("lrc_shift", 0.0) if lines else 0.0
    A = [norm(l["text"])[:30] for l in lines]; B = [norm(l["text"])[:30] for l in lrc]
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False); d = []
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            if lines[blk.a + k].get("heard", True): d.append(lines[blk.a + k]["t0"] - lrc[blk.b + k]["t"] - shift)
    if not d: return {"heard_lines": 0}
    d = np.array(d)
    return {"heard_lines": int(len(d)), "of": len(lrc), "lrc_shift_s": shift, "median_s": round(float(np.median(d)), 3), "mae_s": round(float(np.mean(np.abs(d))), 3),
            "within_0.3s": round(float(np.mean(np.abs(d) <= 0.3)), 3), "within_1s": round(float(np.mean(np.abs(d) <= 1.0)), 3), "worst_s": round(float(d[np.argmax(np.abs(d))]), 2)}

def fmeasure(est, ref, tol=0.07):
    est, ref = np.asarray(est), np.asarray(ref); used = set(); hit = 0
    for r in ref:
        j = int(np.argmin(np.abs(est - r))) if len(est) else -1
        if j >= 0 and abs(est[j] - r) <= tol and j not in used: used.add(j); hit += 1
    p = hit / max(1, len(est)); rc = hit / max(1, len(ref))
    return round(2 * p * rc / (p + rc + 1e-9), 3)

def evaluate(song_path, ref=None, lrc=None, bpm_true=None, key_true=None):
    s = json.load(open(song_path)); out = {"bpm": s["bpm"], "key": s.get("key")}
    if bpm_true:
        bt = float(bpm_true); out["bpm_err_pct"] = round(100 * (s["bpm"] - bt) / bt, 2)
        out["bpm_octave_ok"] = any(abs(s["bpm"] * m - bt) / bt < 0.04 for m in (0.5, 1, 2))
    if key_true: out["key_ok"] = (s.get("key") or "").lower() == key_true.lower(); out["key_in_top3"] = key_true.lower() in [k.lower() for k in s.get("key_candidates", [])]
    if ref:
        r = json.load(open(ref)); b = np.array(s["beats"]); rb = np.array(r["beats"])
        lo, hi = max(b[0], rb[0]), min(b[-1], rb[-1]); b = b[(b >= lo) & (b <= hi)]; rb = rb[(rb >= lo) & (rb <= hi)]
        out["beat_F_70ms"] = fmeasure(b, rb); off = [float(x - rb[np.argmin(np.abs(rb - x))]) for x in b]
        out["beat_median_offset_ms"] = round(1000 * float(np.median(off)), 1)
        d = np.array(s["downbeats"]); rd = np.array(r["downbeats"]); d = d[(d >= lo) & (d <= hi)]; rd = rd[(rd >= lo) & (rd <= hi)]
        out["downbeat_F_70ms"] = fmeasure(d, rd)
    if lrc and s.get("lines"): out["lrc"] = lrc_compare(s["lines"], json.load(open(lrc)))
    print(json.dumps(out)); return out

def slice_audio(path, t0, t1, out, pad=0.0):
    t0 = max(0.0, float(t0) - pad); d = float(t1) + pad - t0
    args = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", path, "-t", f"{d:.3f}"]
    args += (["-c:a", "pcm_s16le"] if out.endswith(".wav") else ["-c:a", "libmp3lame", "-b:a", "192k"]) + [out]
    subprocess.run(args, check=True); print(json.dumps({"out": out, "t0": round(t0, 3), "dur": round(d, 3)}))

def grid(song, a=0, b=1e9):
    s = json.load(open(song))
    for x in s["beats"]:
        if a <= x <= b: print(f"{x:8.3f} {'BAR' if x in s['downbeats'] else 'beat'}")
    for w in s["words"]:
        if a <= w["t0"] <= b: print(f"{w['t0']:8.3f}-{w['t1']:.3f} {w['w']}{'' if w.get('matched', True) else ' (interp)'}")

def click(song, audio, out):
    s = json.load(open(song)); y = load(audio, 44100); sr = 44100
    def blip(t, fr, amp, dur=0.03):
        i = int(t * sr); n = int(dur * sr)
        if i + n < len(y): y[i:i + n] += amp * np.sin(2 * np.pi * fr * np.arange(n) / sr) * np.hanning(n)
    for b in s["beats"]: blip(b, 1500 if b in s["downbeats"] else 1000, 0.35)
    for w in s["words"]: blip(w["t0"], 2600, 0.25, 0.02)
    y = np.clip(y, -1, 1); pcm = (y * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-", out], input=pcm, check=True)
    print(out)

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    if a[0] == "analyze": analyze(a[1], opt("--out", "song.json"), opt("--lyrics"), opt("--bpm"), "--no-words" not in a, opt("--vocals"), opt("--drums"), opt("--beats"), opt("--lrc"))
    elif a[0] == "eval": evaluate(a[1], opt("--ref"), opt("--lrc"), opt("--bpm-true"), opt("--key-true"))
    elif a[0] == "slice": slice_audio(a[1], a[2], a[3], a[4], float(opt("--pad", 0)))
    elif a[0] == "grid": grid(a[1], float(opt("--from", 0)), float(opt("--to", 1e9)))
    elif a[0] == "click": click(a[1], a[2], a[3])
    else: print(__doc__)
