#!/usr/bin/env python3
"""musiceval.py — score a generated (or edited) track against its brief, objectively. Run with $PY.

  musiceval.py measure <audio> <brief.json> [--out metrics.json] [--spectro out.png] [--no-asr] [--ledger L]
  musiceval.py table <metrics_dir_or_files...>                 # markdown table of every metrics.json given

Measures: duration (vs brief), loudness (LUFS-I, true peak, LRA), tempo (spectral-flux autocorrelation + DP
beat tracker; octave-aware error vs brief bpm) and beat steadiness (IBI jitter), key (vs brief; relative/fifth
flagged), hits (strongest transient within +/-1 s of each requested time: error ms + jump dB), ending (hard
stop vs fade: last-300 ms level vs peak), bandwidth (99% spectral roll-off: <16 kHz = lossy/low-res), clipping,
stereo width, lyrics (OpenAI whisper-1 transcript -> word error rate vs brief lyrics; for instrumentals, the count
of phantom words), style distance to a reference song.json (tempo, key, chroma cosine, brightness, density).
Needs ffmpeg; OPENAI_API_KEY for ASR (~$0.006/min, logged to --ledger).
"""
import sys, os, json, re, subprocess, pathlib, time, uuid, urllib.request
import numpy as np
from scipy.signal import stft, find_peaks

HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / ".pi/skills/song-map/scripts"))
import songmap as sm  # noqa: E402

def load_stereo(path, sr=44100):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()

def words(s): return [w for w in re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("\n", " ")).split() if w]
def wer(ref, hyp):
    r, h = words(ref), words(hyp); d = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        prev = d.copy(); d[0] = i
        for j in range(1, len(h) + 1): d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
    return round(float(d[len(h)]) / max(1, len(r)), 3)

def asr(path, ledger=None, tag=None):
    tr = sm.transcribe(path)
    if ledger and tr is not None:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout or 0)
        with open(ledger, "a") as f: f.write(json.dumps({"ts": int(time.time()), "endpoint": "openai/whisper-1", "tag": tag, "est_usd": round(0.006 * dur / 60, 4)}) + "\n")
    return (tr or {}).get("text", "") if tr else None

REL = lambda k: k  # placeholder for readability
def key_relation(a, b):
    if not a or not b: return None
    if a.lower() == b.lower(): return "same"
    ta, ma = sm.PC.index(a.split()[0]), a.split()[1]; tb, mb = sm.PC.index(b.split()[0]), b.split()[1]
    if ma != mb and ((ma == "major" and (ta + 9) % 12 == tb) or (ma == "minor" and (ta + 3) % 12 == tb)): return "relative"
    if ma == mb and (ta - tb) % 12 in (5, 7): return "fifth"
    if ta == tb: return "parallel"
    return "other"

def measure(path, brief, out=None, spectro=None, do_asr=True, ledger=None):
    b = json.loads(pathlib.Path(brief).read_text()) if isinstance(brief, str) else brief
    y = sm.load(path); dur = len(y) / sm.SR; fps = sm.SR / sm.HOP; m = {"file": path, "brief": b.get("id")}
    m["duration"] = round(dur, 2); m["duration_err_s"] = round(dur - float(b["duration"]), 2) if b.get("duration") else None
    m.update(sm.loudness(path))
    env, low, S, f = sm.onset_env(y)
    bpm, cands = sm.tempo(env, fps); beats = sm.beat_track(env, fps, bpm, tight=400)
    m["bpm"], m["grid_resid_ms"] = sm.fit_tempo(beats, bpm); m["bpm_candidates"] = cands
    if b.get("bpm"):
        tgt = float(b["bpm"]); best = min((abs(m["bpm"] * k - tgt) / tgt, k) for k in (0.5, 1, 2, 2 / 3, 1.5))
        m["bpm_err_pct"] = round(100 * (m["bpm"] - tgt) / tgt, 2); m["bpm_octave_err_pct"] = round(100 * best[0], 2); m["bpm_factor"] = best[1]
    key, kc, top, chroma = sm.key_detect(y)
    try:
        import essentia, essentia.standard as es; essentia.log.infoActive = False; essentia.log.warningActive = False
        ek, esc, estr = es.KeyExtractor(profileType="edma")(es.MonoLoader(filename=path, sampleRate=44100)())
        key = f"{ek} {esc}".replace("Bb", "A#").replace("Eb", "D#").replace("Ab", "G#").replace("Db", "C#").replace("Gb", "F#"); kc = round(float(estr), 3)
    except Exception: pass
    m["key"] = key; m["key_conf"] = kc
    if b.get("key"): m["key_relation"] = key_relation(key, b["key"])
    # hits: strongest broadband+low transient near each requested time
    lowb = low / (low.max() + 1e-9); comb = env + 0.5 * lowb
    frame = int(sm.SR / 100); rms = np.array([np.sqrt(np.mean(y[i:i + frame] ** 2) + 1e-12) for i in range(0, len(y), frame)])
    hres = []
    for t in b.get("hits", []):
        a, c = int(max(0, (t - 1.0 - sm.LAT) * fps)), int(min(len(comb), (t + 1.0 - sm.LAT) * fps))
        if c <= a: hres.append({"t": t, "found": None}); continue
        i = a + int(np.argmax(comb[a:c])); th = i / fps + sm.LAT; k = int(th * 100)
        jump = 20 * np.log10(rms[k:k + 20].mean() / (rms[max(0, k - 50):k].mean() + 1e-9)) if k + 20 <= len(rms) else 0.0
        hres.append({"t": t, "found": round(th, 3), "err_ms": round(1000 * (th - t)), "jump_db": round(float(jump), 1), "strength": round(float(comb[i]), 2)})
    if hres:
        m["hits"] = hres; errs = [abs(h["err_ms"]) for h in hres if h.get("err_ms") is not None]
        m["hits_mae_ms"] = round(float(np.mean(errs))) if errs else None; m["hits_within_100ms"] = sum(e <= 100 for e in errs); m["hits_min_jump_db"] = min(h.get("jump_db", 0) for h in hres)
    # ending / start
    peak = rms.max(); m["end_level_db"] = round(float(20 * np.log10(rms[-30:].mean() / peak)), 1)
    nz = np.where(rms > peak * 0.01)[0]; m["lead_silence_s"] = round(nz[0] / 100, 2) if len(nz) else None; m["tail_silence_s"] = round((len(rms) - 1 - nz[-1]) / 100, 2) if len(nz) else None
    # bandwidth, clipping, width
    st = load_stereo(path); mono = st.mean(1)
    F, T, Z = stft(mono[: 44100 * 60], fs=44100, nperseg=4096, noverlap=2048); P = (np.abs(Z) ** 2).mean(1); cp = np.cumsum(P) / P.sum()
    m["rolloff99_hz"] = int(F[np.searchsorted(cp, 0.99)]); hf = P[F > 16000].sum() / P.sum(); m["hf_above_16k_db"] = round(float(10 * np.log10(hf + 1e-12)), 1)
    m["clip_frac"] = round(float(np.mean(np.abs(st) >= 0.999)), 5)
    mid, side = st.mean(1), (st[:, 0] - st[:, 1]) / 2; m["stereo_width"] = round(float(np.sqrt(np.mean(side ** 2)) / (np.sqrt(np.mean(mid ** 2)) + 1e-9)), 3)
    m["centroid_hz"] = int((F[:, None] * np.abs(Z)).sum() / (np.abs(Z).sum() + 1e-9))
    m["onsets_per_s"] = round(len(find_peaks(env, height=0.2, distance=int(0.07 * fps))[0]) / dur, 2)
    # lyrics / phantom vocals
    if do_asr:
        prev = json.loads(pathlib.Path(out).read_text()) if out and pathlib.Path(out).exists() else {}
        txt = prev.get("asr_full", prev.get("asr_text")) if ("asr_full" in prev or "asr_text" in prev) else asr(path, ledger, f"{b.get('id')}:asr:{pathlib.Path(path).stem}")
        m["asr_full"] = txt
        if txt is not None:
            m["asr_text"] = txt[:600]
            if b.get("lyrics") and not b.get("instrumental"): m["wer"] = wer(b["lyrics"].replace("[Verse]", "").replace("[Chorus]", ""), txt)
            else: m["phantom_words"] = len(words(txt))
    # style distance to a reference song map
    ref = (b.get("measure") or {}).get("ref_song")
    if ref:
        r = json.loads((ROOT / ref).read_text()); rc = np.array(r.get("chroma") or [0] * 12)
        m["style"] = {"ref_bpm": r["bpm"], "ref_key": r.get("key"), "key_relation_to_ref": key_relation(key, r.get("key")),
                      "chroma_cos": round(float(np.dot(chroma, rc) / (np.linalg.norm(chroma) * np.linalg.norm(rc) + 1e-9)), 3)}
    if spectro:
        pathlib.Path(spectro).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-lavfi", "showspectrumpic=s=1000x300:legend=1:scale=log:fscale=lin:stop=22000", spectro], check=False)
        m["spectrogram"] = spectro
    if out: pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(out).write_text(json.dumps(m, indent=1))
    print(json.dumps({k: v for k, v in m.items() if k not in ("asr_text", "asr_full", "bpm_candidates", "hits")})); return m

COLS = [("brief", "brief"), ("file", "take"), ("duration", "dur s"), ("duration_err_s", "Δdur"), ("bpm", "bpm"), ("bpm_octave_err_pct", "bpm err %"),
        ("grid_resid_ms", "grid drift ms"), ("key", "key"), ("key_relation", "key vs brief"), ("hits_mae_ms", "hit err ms"), ("hits_min_jump_db", "hit jump dB"),
        ("lufs", "LUFS"), ("true_peak_db", "TP"), ("end_level_db", "end dB"), ("rolloff99_hz", "rolloff Hz"), ("stereo_width", "width"), ("wer", "WER"), ("phantom_words", "phantom words")]

def table(paths):
    fs = []
    for p in paths:
        p = pathlib.Path(p); fs += sorted(p.rglob("*.json")) if p.is_dir() else [p]
    rows = [json.loads(f.read_text()) for f in fs]
    cols = [c for c in COLS if any(r.get(c[0]) is not None for r in rows)]
    print("| " + " | ".join(h for _, h in cols) + " |"); print("|" + "---|" * len(cols))
    for r in rows:
        vals = []
        for k, _ in cols:
            v = r.get(k); v = pathlib.Path(v).stem if k == "file" and v else v; vals.append("" if v is None else str(v))
        print("| " + " | ".join(vals) + " |")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    if a[0] == "measure": measure(a[1], a[2], opt("--out"), opt("--spectro"), "--no-asr" not in a, opt("--ledger"))
    elif a[0] == "table": table(a[1:])
    else: print(__doc__)
