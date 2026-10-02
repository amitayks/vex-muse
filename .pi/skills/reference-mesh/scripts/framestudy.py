#!/usr/bin/env python3
"""framestudy.py — break a reference video into evidence a director can read.

  $PY framestudy.py VIDEO [--out DIR] [--fps 6] [--cut 0.18] [--no-audio]

Writes to DIR (default: <video dir>/study/):
  sheets/sheet_NN.jpg   timecoded contact sheets (5x4 tiles, 384 px) at --fps
  keys/shot_NN.jpg      960 px frame at the middle of every shot
  trans/cut_NN.jpg      transition strip: every 2nd native frame from cut-0.15 s to cut+0.25 s
  motion.png            motion-energy curve (per native frame) with cuts and audio beats
  study.json            fps, duration, shots [t0,t1,dur,palette], cuts, motion stats,
                        audio bpm + beats + onset->cut alignment (how many cuts land on a beat)
Reading order for a study: study.json -> motion.png -> sheets in order -> trans/ -> keys/.
Needs tools/env.sh (ffmpeg) and the studio python ($PY: numpy, opencv, pillow).
"""
import json, os, sys, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

a = sys.argv[1:]
if not a or a[0] in ("-h", "--help"): print(__doc__); sys.exit(0)
opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
VID = a[0]; OUT = opt("--out", os.path.join(os.path.dirname(VID) or ".", "study"))
SFPS = float(opt("--fps", 6)); CUT = float(opt("--cut", 0.18))
for d in ("sheets", "keys", "trans"): os.makedirs(os.path.join(OUT, d), exist_ok=True)
FONT = None
for p in ("/data/workspaces/<workspace>/studio/assets/fonts/Anton.ttf",):
    if os.path.exists(p): FONT = ImageFont.truetype(p, 22)
FONT = FONT or ImageFont.load_default()

# ---- pass 1: decode every frame small, keep motion + scene signals; keep sheet frames ------------
cap = cv2.VideoCapture(VID); fps = cap.get(cv2.CAP_PROP_FPS) or 30; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
prev = None; prevh = None; motion = []; histd = []; sheet = []; step = fps / SFPS; nxt = 0.0; i = 0
small_all = []
while True:
    ok, f = cap.read()
    if not ok: break
    s = cv2.resize(f, (160, 90), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(s, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [8, 4, 4], [0, 180, 0, 256, 0, 256]).flatten(); h /= h.sum() + 1e-9
    motion.append(0.0 if prev is None else float(np.mean(np.abs(g - prev))) / 255)
    histd.append(0.0 if prevh is None else float(0.5 * np.abs(h - prevh).sum()))
    prev, prevh = g, h; small_all.append(s)
    if i >= nxt - 1e-6:
        sheet.append((i / fps, cv2.cvtColor(cv2.resize(f, (384, int(384 * H / W))), cv2.COLOR_BGR2RGB))); nxt += step
    i += 1
cap.release(); n = i; dur = n / fps
motion = np.array(motion); histd = np.array(histd)

# cuts = colour-histogram jumps (robust to fast motion inside a shot); merge within 0.1 s
cand = [k for k in range(1, n) if histd[k] > CUT and histd[k] >= histd[max(0, k - 1)] and histd[k] >= histd[min(n - 1, k + 1)]]
cuts = []
for k in cand:
    if not cuts or (k - cuts[-1]) / fps > 0.1: cuts.append(k)
bounds = [0] + cuts + [n]

def palette(frames, k=5):
    px = np.concatenate([fr.reshape(-1, 3) for fr in frames]).astype(np.float32)
    if len(px) > 20000: px = px[np.random.default_rng(0).choice(len(px), 20000, replace=False)]
    _, lab, cen = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab.flatten(), minlength=k); order = np.argsort(-cnt)
    return [{"hex": "#%02x%02x%02x" % tuple(int(c) for c in cen[j][::-1]), "share": round(float(cnt[j] / cnt.sum()), 3)} for j in order]

shots = []
for j in range(len(bounds) - 1):
    t0, t1 = bounds[j], bounds[j + 1]
    fr = small_all[t0:t1:max(1, (t1 - t0) // 12)]
    m = motion[t0 + 1:t1] if t1 - t0 > 1 else np.array([0])
    shots.append({"i": j + 1, "t0": round(t0 / fps, 3), "t1": round(t1 / fps, 3), "dur": round((t1 - t0) / fps, 3),
                  "motion_mean": round(float(m.mean()), 4), "motion_peak": round(float(m.max()), 4),
                  "hold_frac": round(float((m < 0.002).mean()), 3), "palette": palette(fr)})

# ---- pass 2: one sequential decode collects keyframes + transition frames (seeking is too slow) ---
def label(im, txt):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 8 + 13 * len(txt), 28], fill=(0, 0, 0)); d.text((5, 2), txt, fill=(255, 255, 0), font=FONT); return im

keyidx = {int((s["t0"] + s["t1"]) / 2 * fps): s for s in shots}
transidx = {}
for c, k in enumerate(cuts):
    for d in range(-int(0.15 * fps), int(0.25 * fps) + 1, 2):
        if 0 <= k + d < n: transidx.setdefault(k + d, []).append(c)
transfr = {c: [] for c in range(len(cuts))}
cap = cv2.VideoCapture(VID); i = 0
while True:
    ok, f = cap.read()
    if not ok: break
    if i in keyidx:
        s = keyidx[i]; im = Image.fromarray(cv2.cvtColor(cv2.resize(f, (960, int(960 * H / W))), cv2.COLOR_BGR2RGB))
        label(im, f"shot {s['i']}  {s['t0']:.2f}-{s['t1']:.2f}s").save(os.path.join(OUT, "keys", f"shot_{s['i']:02d}.jpg"), quality=88)
    for c in transidx.get(i, []):
        transfr[c].append(label(Image.fromarray(cv2.cvtColor(cv2.resize(f, (320, int(320 * H / W))), cv2.COLOR_BGR2RGB)), f"{i / fps:.3f}"))
    i += 1
cap.release()
for c, k in enumerate(cuts):
    t = k / fps; ims = transfr[c]
    if not ims: continue
    cols = 6; rows = math.ceil(len(ims) / cols); tw, th = ims[0].size
    strip = Image.new("RGB", (cols * tw, rows * th))
    for q, im in enumerate(ims): strip.paste(im, ((q % cols) * tw, (q // cols) * th))
    strip.save(os.path.join(OUT, "trans", f"cut_{c + 1:02d}_{t:.2f}s.jpg"), quality=85)

# ---- contact sheets -------------------------------------------------------------------------------
per = 20
for sidx in range(math.ceil(len(sheet) / per)):
    chunk = sheet[sidx * per:(sidx + 1) * per]; tw, th = 384, chunk[0][1].shape[0]
    im = Image.new("RGB", (5 * tw, 4 * th), (20, 20, 20))
    for q, (t, fr) in enumerate(chunk): im.paste(label(Image.fromarray(fr), f"{t:.2f}s"), ((q % 5) * tw, (q // 5) * th))
    im.save(os.path.join(OUT, "sheets", f"sheet_{sidx + 1:02d}.jpg"), quality=85)

# ---- audio: onset envelope, tempo, beats; cut/motion alignment ------------------------------------
audio = None
if "--no-audio" not in a:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", VID, "-vn", "-ac", "1", "-ar", "22050", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(r.stdout, np.float32)
    if len(y) > 22050:
        hop, nfft, sr = 256, 1024, 22050
        frames = np.lib.stride_tricks.sliding_window_view(y, nfft)[::hop] * np.hanning(nfft)
        S = np.log1p(np.abs(np.fft.rfft(frames, axis=1)) * 10)
        flux = np.maximum(0, np.diff(S, axis=0)).sum(1); flux = np.concatenate([[0], flux]); flux /= flux.max() + 1e-9
        fr_t = np.arange(len(flux)) * hop / sr
        env = flux - np.convolve(flux, np.ones(16) / 16, "same"); env = np.maximum(env, 0)
        ac = np.correlate(env, env, "full")[len(env) - 1:]
        lo, hi = int(60 / 180 * sr / hop), int(60 / 70 * sr / hop)
        lag = lo + int(np.argmax(ac[lo:hi])); bpm0 = 60 * sr / hop / lag
        # integer lags quantise tempo (~1 BPM steps): refine by fitting a beat grid over +-2 BPM in 0.05 steps
        grid_score = lambda b, o: float(np.interp(np.arange(o, dur, 60 / b), fr_t, env).mean())
        best_b, best, best_s = bpm0, 0.0, -1.0
        for b in np.arange(bpm0 - 2, bpm0 + 2.001, 0.05):
            for o in np.linspace(0, 60 / b, 32, endpoint=False):
                sc = grid_score(b, o)
                if sc > best_s: best_b, best, best_s = b, o, sc
        bpm = round(float(best_b), 2)
        if abs(bpm - round(bpm)) <= 0.15: bpm = float(round(bpm))   # produced music sits on integer tempi
        period = 60 / bpm
        best = max(np.linspace(0, period, 96, endpoint=False), key=lambda o: sum(np.interp(np.arange(o, dur, period), fr_t, env)))
        beats = [round(float(b), 3) for b in np.arange(best, dur, period)]
        peaks = [float(fr_t[k]) for k in range(1, len(env) - 1) if env[k] > 0.25 and env[k] >= env[k - 1] and env[k] >= env[k + 1]]
        tol = 2.5 / fps
        on_beat = [c / fps for c in cuts if min(abs(c / fps - b) for b in beats) <= max(tol, 0.05)]
        audio = {"bpm": round(bpm, 2), "beat_period": round(period, 4), "beat_phase": round(float(best), 3), "beats": beats,
                 "onsets": [round(p, 3) for p in peaks][:400],
                 "cuts_on_beat": f"{len(on_beat)}/{len(cuts)}",
                 "cut_offsets_ms": [round(1000 * (c / fps - min(beats, key=lambda b: abs(b - c / fps)))) for c in cuts]}
        audio["_env"], audio["_t"] = env, fr_t

# ---- motion chart ---------------------------------------------------------------------------------
Wc, Hc = 1800, 420; im = Image.new("RGB", (Wc, Hc), (17, 17, 17)); d = ImageDraw.Draw(im)
X = lambda t: 60 + (Wc - 80) * t / dur; mm = max(1e-6, float(np.percentile(motion, 99.5)))
if audio:
    for b in audio["beats"]: d.line([(X(b), 30), (X(b), Hc - 40)], fill=(45, 45, 70))
    e = audio["_env"]; em = e.max() + 1e-9
    d.line([(X(t), Hc - 40 - 80 * v / em) for t, v in zip(audio["_t"], e)], fill=(78, 205, 196), width=1)
d.line([(X(k / fps), Hc - 130 - 250 * min(1, v / mm)) for k, v in enumerate(motion)], fill=(255, 165, 2), width=2)
for c in cuts: d.line([(X(c / fps), 20), (X(c / fps), Hc - 30)], fill=(255, 71, 87), width=2)
for t in range(int(dur) + 1): d.text((X(t) - 6, Hc - 28), f"{t}s", fill=(200, 200, 200), font=FONT)
d.text((60, 2), f"orange=motion energy  red=cuts  teal=audio onsets  grey=beats {audio['bpm'] if audio else '-'} bpm", fill=(230, 230, 230), font=FONT)
im.save(os.path.join(OUT, "motion.png"))

if audio: audio.pop("_env"); audio.pop("_t")
study = {"video": VID, "size": [W, H], "fps": round(fps, 3), "frames": n, "duration": round(dur, 3),
         "cuts": [round(c / fps, 3) for c in cuts], "n_shots": len(shots),
         "avg_shot_s": round(dur / len(shots), 3), "motion_mean": round(float(motion.mean()), 4),
         "hold_frac": round(float((motion < 0.002).mean()), 3), "shots": shots, "audio": audio}
json.dump(study, open(os.path.join(OUT, "study.json"), "w"), indent=1)
print(json.dumps({k: study[k] for k in ("duration", "fps", "n_shots", "avg_shot_s", "cuts", "hold_frac")} | {"bpm": audio and audio["bpm"], "cuts_on_beat": audio and audio["cuts_on_beat"], "out": OUT}))
