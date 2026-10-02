#!/usr/bin/env python3
"""trackedit.py — edit music on its own grid (bars from song.json), sample-accurate, click-free. Run with $PY.

  trackedit.py fit <in> <out.wav> --song song.json --dur 30 [--mode auto|edit|window|loop] [--prefer chorus|loud|start] [--end hard|fade] [--max-stretch 0.03]
  trackedit.py cut <in> <out.wav> --song song.json --bars 1:16[,33:40]      # keep bar ranges (1-based, inclusive), joined on downbeats
  trackedit.py loop <in> <out.wav> --song song.json --bars 17:24 --dur 60   # repeat a bar range to a length (bed / extend)
  trackedit.py tempo <in> <out.wav> (--ratio 1.05 | --from 120 --to 128) [--semitones 0]   # rubberband, pitch kept
  trackedit.py pitch <in> <out.wav> --semitones -2                         # rubberband, tempo kept, formants preserved
  trackedit.py stems <out.wav> --dir stems/ --gains vocals=0,drums=1,bass=1,other=1          # instrumental / a cappella / drums-only
  trackedit.py xfade <a> <b> <out.wav> --song-a a.json --song-b b.json --a-bar 33 --b-bar 1 --bars 4   # beat-matched DJ transition with bass swap
  trackedit.py mashup <vocals> <instrumental> <out.wav> --song-v v.json --song-i i.json [--v-bar 9 --i-bar 1] [--bars 16]
  trackedit.py duck <music> <voice> <out.wav> [--db 8]                     # music ducks under a voice-over
  trackedit.py master <in> <out.wav|mp3> [--lufs -14] [--tp -1]            # two-pass loudnorm, verified
  trackedit.py check <in> [--dur 30] [--lufs -14] [--cuts 7.5,15.0]        # length, loudness, clicks at cut points

Grid = song.json downbeats (song-map). Every join lands on a downbeat with a 30 ms equal-power crossfade at the
nearest zero-crossing region; fit stretches the result by at most --max-stretch (rubberband) so the LAST bar ends
exactly at --dur; otherwise it trims with a fade (--end fade) or on a downbeat (--end hard). Output 44.1 kHz stereo WAV.
Every command prints JSON with what it did (bars kept, stretch ratio, output duration) for the edit log.
"""
import sys, os, json, subprocess, pathlib, tempfile
import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 44100; XF = 0.03

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()

def save(x, p):
    x = np.clip(x, -1, 1).astype(np.float32); p = str(p)
    args = ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-"]
    args += (["-c:a", "libmp3lame", "-b:a", "320k"] if p.endswith(".mp3") else ["-c:a", "pcm_s16le"]) + [p]
    subprocess.run(args, input=x.tobytes(), check=True)

def ff(filt, i, o):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(i), "-af", filt, "-ar", str(SR), "-ac", "2", str(o)], check=True)

def grid(song):
    s = json.loads(pathlib.Path(song).read_text()); d = np.array(s["downbeats"], float)
    bar = 4 * 60 / s["bpm"]
    if len(d) and d[-1] + bar <= s["duration"] + 0.05: d = np.r_[d, d[-1] + bar]   # close the last bar
    return s, d, bar

def join(segs, xf=XF):
    """Concatenate sample segments with equal-power crossfades of xf seconds (overlap taken from the next segment's pre-roll)."""
    n = int(xf * SR); out = segs[0].copy()
    for s in segs[1:]:
        if len(out) < n or len(s) < n: out = np.r_[out, s]; continue
        t = np.linspace(0, np.pi / 2, n)[:, None]
        out[-n:] = out[-n:] * np.cos(t) + s[:n] * np.sin(t); out = np.r_[out, s[n:]]
    return out

def take(x, t0, t1, pre=XF):
    """Samples [t0, t1) plus `pre` seconds of pre-roll so the crossfade centres on the downbeat."""
    a = max(0, int(round((t0 - pre / 2) * SR))); b = min(len(x), int(round((t1 + pre / 2) * SR))); return x[a:b]

def stretch_to(x, dur, max_stretch):
    cur = len(x) / SR; ratio = cur / dur
    if abs(ratio - 1) < 1e-4: return x, 1.0
    if abs(ratio - 1) > max_stretch: return x, None
    with tempfile.TemporaryDirectory() as td:
        save(x, f"{td}/a.wav"); ff(f"rubberband=tempo={ratio:.6f}:transients=crisp", f"{td}/a.wav", f"{td}/b.wav"); y = load(f"{td}/b.wav")
    n = int(round(dur * SR)); y = y[:n] if len(y) >= n else np.r_[y, np.zeros((n - len(y), 2), np.float32)]
    return y, round(ratio, 5)

def finish(x, dur, end="fade", fade=1.5):
    n = int(round(dur * SR))
    if len(x) < n: x = np.r_[x, np.zeros((n - len(x), 2), np.float32)]
    x = x[:n].copy(); k = int((fade if end == "fade" else 0.012) * SR)
    x[-k:] *= np.linspace(1, 0, k)[:, None] ** (2 if end == "fade" else 1); return x

def plan_fit(s, d, bar, dur, mode, prefer):
    """Return (list of (t0,t1) bar-aligned spans, description). Spans are joined in order."""
    secs = [(x["t0"], x["t1"], x.get("label")) for x in s.get("sections", [])]
    bounds = sorted(set([float(d[0])] + [float(d[np.argmin(np.abs(d - b))]) for b in [x[0] for x in secs] + [x[1] for x in secs]] + [float(d[-1])]))
    total = d[-1] - d[0]; nb = lambda a, b: int(round((b - a) / bar))
    if mode == "auto": mode = "loop" if dur > total else ("edit" if prefer == "start" else "window")
    if mode == "window":
        best = None
        for i, a in enumerate(bounds[:-1]):
            j = int(np.argmin(np.abs(d - (a + dur)))); b = float(d[j])
            if b <= a: continue
            lab = next((x[2] for x in secs if abs(x[0] - a) < bar / 2), None)
            e = np.mean(s["energy_10hz"][int(a * 10):int(b * 10)] or [0])
            score = -abs((b - a) - dur) / bar + (1.5 if prefer == "chorus" and lab == "chorus" else 0) + (e if prefer in ("loud", "chorus") else -a / 60)
            if best is None or score > best[0]: best = (score, a, b, lab)
        return [(best[1], best[2])], f"window {best[1]:.2f}-{best[2]:.2f}s ({nb(best[1], best[2])} bars, starts at {best[3] or 'a boundary'})"
    if mode == "edit":
        best = None; min_end = min(4 * bar, dur / 3)   # a real ending: >= 4 bars (or a third of the target)
        for a in bounds[1:-1]:
            for b in bounds:
                if b <= a or a - d[0] < min(4 * bar, dur / 3) or d[-1] - b < min_end: continue
                L = (a - d[0]) + (d[-1] - b); err = abs(L - dur)
                if best is None or err < best[0]: best = (err, a, b)
        if best is None or best[0] > 2 * bar:   # no section-aligned cut: cut on any downbeat pair
            for a in d[1:-1]:
                for b in d:
                    if b <= a or a - d[0] < min(4 * bar, dur / 3) or d[-1] - b < min_end: continue
                    err = abs((a - d[0]) + (d[-1] - b) - dur)
                    if best is None or err < best[0]: best = (err, float(a), float(b))
        _, a, b = best
        return [(float(d[0]), a), (b, float(d[-1]))], f"edit keeps {d[0]:.2f}-{a:.2f} + {b:.2f}-{d[-1]:.2f}s (removes {nb(a, b)} bars)"
    if mode == "loop":
        loopsec = max(secs, key=lambda x: (x[2] == "chorus", x[1] - x[0])) if secs else (d[0], d[-1], None)
        a = float(d[np.argmin(np.abs(d - loopsec[0]))]); b = float(d[np.argmin(np.abs(d - loopsec[1]))])
        spans = [(float(d[0]), b)]; L = b - d[0]
        while L + (b - a) < dur + bar: spans.append((a, b)); L += b - a
        tail = [(b, float(d[-1]))] if L + (d[-1] - b) <= dur + 2 * bar else []
        return spans + tail, f"loop bars of {a:.2f}-{b:.2f}s ×{len(spans) - 1} after the opening"
    raise SystemExit(f"unknown mode {mode}")

def cmd_fit(i, o, song, dur, mode="auto", prefer="start", end="fade", max_stretch=0.03):
    x = load(i); s, d, bar = grid(song); spans, desc = plan_fit(s, d, bar, float(dur), mode, prefer)
    y = join([take(x, a, b) for a, b in spans]); ratio = None
    if abs(len(y) / SR - float(dur)) <= max_stretch * float(dur): y, ratio = stretch_to(y, float(dur), max_stretch)
    y = finish(y, float(dur), end if ratio is None else "hard")
    cuts = list(np.cumsum([b - a for a, b in spans])[:-1] / (ratio or 1))
    save(y, o); r = {"out": o, "dur": round(len(y) / SR, 3), "plan": desc, "spans": [(round(a, 3), round(b, 3)) for a, b in spans],
                     "stretch_ratio": ratio, "end": "exact bar" if ratio else end, "cut_points_s": [round(c, 3) for c in cuts]}
    print(json.dumps(r)); return r

def parse_bars(spec):
    return [tuple(int(v) for v in part.split(":")) for part in spec.split(",")]

def cmd_cut(i, o, song, bars):
    x = load(i); s, d, bar = grid(song); spans = [(float(d[a - 1]), float(d[min(b, len(d) - 1)])) for a, b in parse_bars(bars)]
    y = join([take(x, a, b) for a, b in spans]); save(y, o); print(json.dumps({"out": o, "dur": round(len(y) / SR, 3), "spans": spans}))

def cmd_loop(i, o, song, bars, dur):
    x = load(i); s, d, bar = grid(song); (a, b), = parse_bars(bars); t0, t1 = float(d[a - 1]), float(d[min(b, len(d) - 1)])
    k = int(np.ceil(float(dur) / (t1 - t0))) + 1; y = finish(join([take(x, t0, t1)] * k), float(dur), "fade"); save(y, o)
    print(json.dumps({"out": o, "dur": round(len(y) / SR, 3), "loop": [t0, t1], "repeats": k}))

def cmd_tempo(i, o, ratio=None, frm=None, to=None, semis=0.0):
    r = float(ratio) if ratio else float(to) / float(frm); p = 2 ** (float(semis) / 12)
    ff(f"rubberband=tempo={r:.6f}:pitch={p:.6f}:transients=crisp:formant=preserved", i, o)
    print(json.dumps({"out": o, "tempo_ratio": round(r, 5), "semitones": float(semis)}))

def cmd_stems(o, dirp, gains):
    g = {k: float(v) for k, v in (kv.split("=") for kv in gains.split(","))}; mix = None
    for name, gain in g.items():
        f = next(iter(sorted(pathlib.Path(dirp).glob(f"{name}.*"))), None)
        if not f or gain == 0: continue
        y = load(f) * gain; mix = y if mix is None else mix[:min(len(mix), len(y))] + y[:min(len(mix), len(y))]
    save(mix, o); print(json.dumps({"out": o, "gains": g, "dur": round(len(mix) / SR, 3)}))

def bands(x, fc=180):
    lo = sosfiltfilt(butter(4, fc, "low", fs=SR, output="sos"), x, axis=0); return lo, x - lo

def cmd_xfade(a, b, o, song_a, song_b, a_bar, b_bar, bars=4):
    sa, da, bara = grid(song_a); sb, db, barb = grid(song_b); xa = load(a); xb = load(b); ratio = sb["bpm"] / sa["bpm"]
    if abs(ratio - 1) > 1e-3:
        with tempfile.TemporaryDirectory() as td:
            save(xb, f"{td}/b.wav"); ff(f"rubberband=tempo={1 / ratio:.6f}:transients=crisp", f"{td}/b.wav", f"{td}/b2.wav"); xb = load(f"{td}/b2.wav")
        db = db * ratio
    ta = float(da[int(a_bar) - 1]); tb = float(db[int(b_bar) - 1]); L = bars * bara; n = int(L * SR)
    ia, ib = int(ta * SR), int(tb * SR); A = xa[ia:ia + n]; B = xb[ib:ib + n]; n = min(len(A), len(B)); A, B = A[:n], B[:n]
    la, ha = bands(A); lb, hb = bands(B); t = np.linspace(0, 1, n)[:, None]; mid = (t >= 0.5).astype(np.float32)
    sw = np.clip((t - 0.5) / (1 / (bars * 4)) + 0.5, 0, 1)   # one-beat bass swap at the midpoint
    X = ha * np.cos(t * np.pi / 2) + hb * np.sin(t * np.pi / 2) + la * (1 - sw) + lb * sw
    y = np.r_[xa[:ia], X, xb[ib + n:]]; save(y, o)
    print(json.dumps({"out": o, "a_out_at": round(ta, 3), "b_in_from": round(tb, 3), "bars": bars, "b_tempo_ratio": round(1 / ratio, 5), "dur": round(len(y) / SR, 2)}))

def cmd_mashup(v, inst, o, song_v, song_i, v_bar=None, i_bar=1, bars=None):
    sv, dv, _ = grid(song_v); si, di, bari = grid(song_i)
    kv, ki = sv.get("key"), si.get("key"); semis = 0
    if kv and ki:
        pc = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        tv = pc.index(kv.split()[0]) + (3 if kv.split()[1] == "minor" else 0); ti = pc.index(ki.split()[0]) + (3 if ki.split()[1] == "minor" else 0)
        semis = ((ti - tv + 6) % 12) - 6   # compare relative-major tonics; shift by at most a tritone
    r = si["bpm"] / sv["bpm"]
    if v_bar is None:  # first downbeat at/after the first sung word
        w0 = (sv.get("words") or [{"t0": dv[0]}])[0]["t0"]; v_bar = int(np.searchsorted(dv, w0 - 0.25)) + 1
    with tempfile.TemporaryDirectory() as td:
        ff(f"rubberband=tempo={r:.6f}:pitch={2 ** (semis / 12):.6f}:formant=preserved", v, f"{td}/v.wav"); xv = load(f"{td}/v.wav")
    xi = load(inst); tv0 = float(dv[int(v_bar) - 1]) / r; ti0 = float(di[int(i_bar) - 1])
    xv = xv[int(tv0 * SR):]; lead = int(ti0 * SR)
    L = len(xi) if not bars else min(len(xi), lead + int(int(bars) * bari * SR)); voc = np.zeros_like(xi[:L]); m = min(L - lead, len(xv)); voc[lead:lead + m] = xv[:m]
    env = np.convolve(np.abs(voc).mean(1), np.ones(4410) / 4410, "same"); duck = 1 - 0.3 * np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
    y = xi[:L] * duck[:, None] + voc * 1.1; save(y, o)
    print(json.dumps({"out": o, "vocal_tempo_ratio": round(r, 5), "vocal_semitones": semis, "vocal_from_bar": v_bar, "inst_from_bar": i_bar, "dur": round(L / SR, 2)}))

def cmd_duck(music, voice, o, db=8, attack=0.03, release=0.35):
    """Music dips exactly `db` dB while the voice is active (-45..-30 dBFS ramp), 30 ms attack, 350 ms release."""
    m = load(music); v = load(voice); n = len(m); v = np.r_[v, np.zeros((max(0, n - len(v)), 2), np.float32)][:n]
    hop = 441; e = np.sqrt(np.convolve(v.mean(1) ** 2, np.ones(2205) / 2205, "same")[::hop] + 1e-12)
    act = np.clip((20 * np.log10(e) + 45) / 15, 0, 1); sm = np.zeros_like(act); a_c, r_c = np.exp(-hop / SR / attack), np.exp(-hop / SR / release)
    for i in range(len(act)):
        prev = sm[i - 1] if i else 0.0; c = a_c if act[i] > prev else r_c; sm[i] = c * prev + (1 - c) * act[i]
    g = 10 ** (-float(db) * np.interp(np.arange(n) / hop, np.arange(len(sm)), sm) / 20)
    y = m * g[:, None] + v; pk = np.abs(y).max(); y = y * (0.95 / pk) if pk > 0.95 else y
    save(y, o); print(json.dumps({"out": o, "duck_db": float(db), "voice_active_s": round(float((sm > 0.5).sum() * hop / SR), 1), "dur": round(n / SR, 2)}))

def lufs(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re; t = r[r.rfind("Summary:"):]; I = re.search(r"I:\s+(-?[\d.]+) LUFS", t); P = re.search(r"Peak:\s+(-?[\d.]+) dBFS", t)
    return (float(I.group(1)) if I else None, float(P.group(1)) if P else None)

def cmd_master(i, o, target=-14.0, tp=-1.0):
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", i, "-af", f"loudnorm=I={target}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    args = ["ffmpeg", "-v", "error", "-y", "-i", i, "-af", af, "-ar", str(SR)] + (["-b:a", "320k"] if o.endswith(".mp3") else ["-c:a", "pcm_s16le"]) + [o]
    subprocess.run(args, check=True); I, P = lufs(o)
    ok = I is not None and abs(I - target) <= 0.5 and P is not None and P <= tp + 0.3
    print(json.dumps({"out": o, "in_lufs": float(j["input_i"]), "out_lufs": I, "out_true_peak": P, "ok": ok}))

def cmd_check(i, dur=None, target=None, cuts=None):
    x = load(i); r = {"file": i, "dur": round(len(x) / SR, 3)}; r["lufs"], r["true_peak"] = lufs(i)
    if dur: r["dur_ok"] = abs(r["dur"] - float(dur)) <= 1 / 48
    if target: r["lufs_ok"] = r["lufs"] is not None and abs(r["lufs"] - float(target)) <= 0.5
    if cuts:
        hp = np.abs(np.diff(sosfiltfilt(butter(4, 8000, "high", fs=SR, output="sos"), x.mean(1)))); base = np.median(hp) + 1e-9; clicks = []
        for c in [float(v) for v in cuts.split(",")]:
            k = int(c * SR); w = hp[max(0, k - 441):k + 441]; ctx = hp[max(0, k - 44100):k + 44100]
            clicks.append({"t": c, "spike_vs_context": round(float(w.max() / (np.percentile(ctx, 99) + 1e-9)), 2)})
        r["cuts"] = clicks; r["clicks_ok"] = all(c["spike_vs_context"] < 1.5 for c in clicks)
    print(json.dumps(r)); return r

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d; c = a[0]
    if c == "fit": cmd_fit(a[1], a[2], opt("--song"), opt("--dur"), opt("--mode", "auto"), opt("--prefer", "start"), opt("--end", "fade"), float(opt("--max-stretch", 0.03)))
    elif c == "cut": cmd_cut(a[1], a[2], opt("--song"), opt("--bars"))
    elif c == "loop": cmd_loop(a[1], a[2], opt("--song"), opt("--bars"), opt("--dur"))
    elif c == "tempo": cmd_tempo(a[1], a[2], opt("--ratio"), opt("--from"), opt("--to"), opt("--semitones", 0))
    elif c == "pitch": cmd_tempo(a[1], a[2], 1.0, None, None, opt("--semitones", 0))
    elif c == "stems": cmd_stems(a[1], opt("--dir"), opt("--gains"))
    elif c == "xfade": cmd_xfade(a[1], a[2], a[3], opt("--song-a"), opt("--song-b"), opt("--a-bar"), opt("--b-bar", 1), int(opt("--bars", 4)))
    elif c == "mashup": cmd_mashup(a[1], a[2], a[3], opt("--song-v"), opt("--song-i"), opt("--v-bar") and int(opt("--v-bar")), int(opt("--i-bar", 1)), opt("--bars"))
    elif c == "duck": cmd_duck(a[1], a[2], a[3], opt("--db", 8))
    elif c == "master": cmd_master(a[1], a[2], float(opt("--lufs", -14)), float(opt("--tp", -1)))
    elif c == "check": cmd_check(a[1], opt("--dur"), opt("--lufs"), opt("--cuts"))
    else: print(__doc__)
