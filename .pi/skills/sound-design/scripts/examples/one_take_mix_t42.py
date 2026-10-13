#!/usr/bin/env python3
# EXAMPLE, NOT A TOOL. This is the sound-design mixer of TOWER 42, a 105 s real-time one-take
# (drone dive -> lobby -> lift -> desk), kept as a worked example of physics-driven sound.
# The event names, zones, timings and file names belong to that film. To reuse it, copy it into
# your project and replace the EVENTS / ZONES / cue tables. The reusable parts are:
#   place()      pan a point sound by its azimuth to the camera (equal power), level it 1/r
#   add_bed()    a bed whose gain follows a curve (camera speed^2, camera height, cab speed)
#   loop_to()    loop a short bed to length with a cross-fade
#   var_lp()     a low-pass whose cut-off moves with time (distance, doors)
#   compress()   a keyed compressor for the ambience stem
# Inputs it expects (exported from the Blender scene, see knowledge/references/blender-field-notes.md,
# "Exports for sound design"): events.json (frame, world position per event), camera.json (per-frame
# camera track), audio/sfx/*, audio/steps/index.json. Level SFX with ebur128 (momentary M), not RMS.
"""TOWER 42 sound design mixer: one take, real time, physics-placed sound.

Reads events (events_v2.json if present, else events.json), the camera track
(camera_v3.json if present; else time-based fallbacks), the SFX library in
audio/sfx and sliced steps in audio/steps. Writes audio/mix.wav (48 kHz
stereo, 105.0 s) and audio/mix_report.json.

Placement: point sounds with a world position are panned by their azimuth to
the camera (equal power) and attenuated by distance (1/r, 1 m reference).
Beds follow the camera: altitude wind by height, dive wind by speed^2, the
street and the lobby by zone, the lift motor and the shaft wind by cab speed.

Usage: mix_t42.py [--target -16] [--out audio/mix.wav] [--seed 7]
"""
import json, os, shutil, subprocess, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(ROOT)
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
SR = 48000
FPS = 24
DUR = 105.0
N = int(DUR * SR)

args = sys.argv[1:]
def opt(k, d):
    return type(d)(args[args.index(k) + 1]) if k in args else d
TARGET = opt("--target", -18.0)
OUT = opt("--out", os.path.join(ROOT, "mix.wav"))
rng = np.random.default_rng(opt("--seed", 7))

# ---------- io ----------
_cache = {}
def load(name, mono=True):
    f = name if os.path.isabs(name) else os.path.join(ROOT, name)
    key = (f, mono)
    if key not in _cache:
        ch = "1" if mono else "2"
        raw = subprocess.run([FF, "-loglevel", "error", "-i", f, "-ac", ch, "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).copy()
        _cache[key] = x if mono else x.reshape(-1, 2)
    return _cache[key]

def db(g):
    return 10 ** (g / 20)

def t2n(t):
    return int(round(t * SR))

# ---------- filters (cheap, causal one-pole / biquad) ----------
def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x, axis=0)

def biquad(x, kind, fc, q=0.707, gain_db=0.0):
    from scipy.signal import lfilter
    A = 10 ** (gain_db / 40); w = 2 * np.pi * fc / SR; c = np.cos(w); s = np.sin(w); al = s / (2 * q)
    if kind == "lp":
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == "hp":
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == "bp":
        b = [al, 0, -al]; a = [1 + al, -2 * c, 1 - al]
    elif kind == "lowshelf":
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * c + sq), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sq)]
        a = [(A + 1) + (A - 1) * c + sq, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sq]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * c + sq), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sq)]
        a = [(A + 1) - (A - 1) * c + sq, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sq]
    else:
        raise ValueError(kind)
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)

def var_lp(x, fc_curve, block=2400):
    """Time-varying one-pole low-pass on a 1-D signal, coefficient per 50 ms block, state carried."""
    from scipy.signal import lfilter
    y = np.empty_like(x, dtype=float); zi = np.zeros(1)
    for s in range(0, len(x), block):
        e = min(len(x), s + block); fc = float(np.mean(fc_curve[s:e])); a = np.exp(-2 * np.pi * fc / SR)
        y[s:e], zi = lfilter([1 - a], [1, -a], x[s:e], zi=zi)
    return y

# ---------- timeline helpers ----------
tt = np.arange(N) / SR
def ramp(t0, t1, v0, v1):
    """Piecewise curve helper: smoothstep from v0 at t0 to v1 at t1 (per sample)."""
    u = np.clip((tt - t0) / max(1e-6, t1 - t0), 0, 1); u = u * u * (3 - 2 * u)
    return v0 + (v1 - v0) * u

def curve(points):
    """points: [(t, dB), ...] smooth-stepped between keys; returns linear gain per sample."""
    g = np.full(N, points[0][1], float)
    for (t0, v0), (t1, v1) in zip(points[:-1], points[1:]):
        m = (tt >= t0) & (tt <= t1)
        u = (tt[m] - t0) / max(1e-6, t1 - t0); u = u * u * (3 - 2 * u)
        g[m] = v0 + (v1 - v0) * u
    g[tt > points[-1][0]] = points[-1][1]
    return db(g)

def loop_to(x, n, xfade=0.5):
    """Loop a mono bed to n samples with equal-power crossfades."""
    if len(x) >= n:
        return x[:n].astype(float).copy()
    xf = int(xfade * SR); step = len(x) - xf
    fin = np.sqrt(np.linspace(0, 1, xf)); fout = np.sqrt(np.linspace(1, 0, xf))
    out = np.zeros(n + len(x)); pos = 0; k = 0
    while pos < n:
        seg = x.astype(float).copy()
        if k:
            seg[:xf] *= fin
        seg[-xf:] *= fout
        out[pos:pos + len(seg)] += seg; pos += step; k += 1
    return out[:n]

# ---------- events and camera ----------
ev_path = os.path.join(P, "mac/stage4/events_v2.json")
if not os.path.exists(ev_path):
    ev_path = os.path.join(P, "mac/stage4/events.json")
EV = json.load(open(ev_path))
events = EV["events"]
def ev_t(name, default=None):
    for e in events:
        if e["event"] == name:
            return e["t"]
    return default

cam_path = os.path.join(P, "mac/stage4/camera_v3.json")
CAM = None
if os.path.exists(cam_path):
    c = json.load(open(cam_path))
    frames = c.get("frames", c) if isinstance(c, dict) else c
    def get(fr, *keys):
        for k in keys:
            if k in fr:
                return fr[k]
        return None
    pos = np.array([get(f, "pos", "position", "loc", "location") for f in frames], float)
    yaw = np.array([get(f, "yaw", "yaw_deg") for f in frames], float)
    CAM = {"pos": pos, "yaw": yaw}

def cam_at(t):
    if CAM is None:
        return None, None
    i = int(np.clip(round(t * FPS), 0, len(CAM["pos"]) - 1))
    return CAM["pos"][i], CAM["yaw"][i]

def place(t, pos=None, ref_dist=1.0):
    """Return (gain_lin, pan -1..1) for a point source at world pos heard from the camera at time t."""
    cp, cy = cam_at(t)
    if pos is None or cp is None:
        return 1.0, 0.0
    d = np.array(pos, float) - cp
    r = max(ref_dist, float(np.linalg.norm(d)))
    az = np.degrees(np.arctan2(d[1], d[0]))           # world azimuth of the source
    rel = ((az - cy + 180) % 360) - 180                 # relative to camera forward (deg, +left)
    pan = float(np.clip(-np.sin(np.radians(rel)), -1, 1))
    return ref_dist / r, pan

L = np.zeros(N); R = np.zeros(N)
stems = {}
# zone reverb: RT60 (s) and send level (dB) per zone; sends are summed per zone and convolved once at the end
ZONES = {"plaza": (0.35, -20), "lobby": (1.7, -9), "lift_lobby_L1": (1.2, -11), "cab": (0.22, -18),
         "lift_lobby_L42": (0.6, -15), "office": (0.5, -16)}
sends = {z: np.zeros(N) for z in ZONES}
def ir(rt60, seed):
    r = np.random.default_rng(seed); n = int(min(3.0, rt60 * 1.2) * SR)
    t_ = np.arange(n) / SR; e = np.exp(-6.91 * t_ / rt60)
    a = r.standard_normal(n) * e; b = r.standard_normal(n) * e
    pre = int(0.012 * SR); a[:pre] = 0; b[:pre] = 0
    return np.stack([a, b], 1) / np.sqrt((e ** 2).sum())
def add(x, t0, gain=1.0, pan=0.0, stem="sfx", zone=None):
    if zone in sends and x.ndim == 1:
        s0 = max(0, t2n(t0)); e0 = min(N, s0 + len(x)); sends[zone][s0:e0] += x[:e0 - s0] * gain * db(ZONES[zone][1])
    s = t2n(t0)
    if s < 0:
        x = x[-s:]; s = 0
    e = min(N, s + len(x))
    if e <= s:
        return
    th = (pan + 1) * np.pi / 4
    gl, gr = np.cos(th) * np.sqrt(2) * gain, np.sin(th) * np.sqrt(2) * gain
    seg = x[:e - s]
    if seg.ndim == 2:
        L[s:e] += seg[:, 0] * gain; R[s:e] += seg[:, 1] * gain
        a = stems.setdefault(stem, np.zeros((N, 2))); a[s:e, 0] += seg[:, 0] * gain; a[s:e, 1] += seg[:, 1] * gain
    else:
        L[s:e] += seg * gl; R[s:e] += seg * gr
        a = stems.setdefault(stem, np.zeros((N, 2))); a[s:e, 0] += seg * gl; a[s:e, 1] += seg * gr

def add_bed(x, g, stem, width=0.6):
    """Mono bed to a pseudo-stereo bed (short decorrelation delay), with a gain curve."""
    x = loop_to(x, N) * g
    d = int(0.011 * SR)
    l = x; r = np.concatenate([np.zeros(d), x[:-d]])
    m = (l + r) / 2; s = (l - r) / 2 * width
    add(np.stack([m + s, m - s], 1), 0.0, 1.0, 0.0, stem)

def peak_offset(x):
    """Seconds from file start to the energy peak (cue by the peak, not the file start)."""
    hop = 240; env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))
    return float(np.argmax(env)) / SR

def onset_offset(x, rel_db=-25):
    hop = 240; env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same")); pk = env.max()
    idx = np.where(env > pk * db(rel_db))[0]
    return float(idx[0]) / SR if len(idx) else 0.0

def norm_peak(x, to=0.5):
    p = float(np.abs(x).max()) or 1.0
    return x * (to / p)

# ---------- key times ----------
T_DOOR = ev_t("door_push", 19.792)
T_PASS = ev_t("door_pass", 20.208)
T_TURN = ev_t("turnstile_tap", 23.833)
T_CALL = ev_t("call_button_press", 29.875)
T_DING1 = ev_t("lift_ding_L1", 36.875)
T_OPEN1 = ev_t("lift_doors_open_start_L1", 37.042)
T_CLOSE1 = ev_t("lift_doors_close_start_L1", 44.417)
T_CLOSED1 = ev_t("lift_doors_close_end_L1", 47.417)
T_START = [e["t"] for e in events if e["event"] == "cab_start" and e.get("trip") == 1][0]
T_STOP = [e["t"] for e in events if e["event"] == "cab_stop" and e.get("trip") == 1][0]
T_DING42 = ev_t("lift_ding_L42", 82.208)
T_OPEN42 = ev_t("lift_doors_open_start_L42", 82.417)
T_OPENED42 = ev_t("lift_doors_open_end_L42", 84.417)
T_CLOSE42 = ev_t("lift_doors_close_start_L42", 88.417)
T_RAIL = ev_t("chair_contact", 94.833)
T_SIT0 = ev_t("sit_start", 97.083)
T_SIT = ev_t("sit_down", 98.375)
T_CUP = ev_t("cup_land", 98.0)
T_DRIFT = ev_t("end_drift_start", 100.417)
report = {"events_file": os.path.basename(ev_path), "camera": CAM is not None, "cues": []}

# ---------- camera-driven curves ----------
if CAM is not None:
    fr_t = np.arange(len(CAM["pos"])) / FPS
    z = np.interp(tt, fr_t, CAM["pos"][:, 2])
    vel = np.gradient(CAM["pos"], axis=0) * FPS
    spd = np.interp(tt, fr_t, np.linalg.norm(vel, axis=1))
else:
    # fallback: stage-1 numbers (top-down hold 2 s, dive peak ~27 m/s around 6-10 s, at eye height by ~15 s)
    z = np.interp(tt, [0, 2, 8, 12, 15, 19.3, 200], [260, 255, 150, 50, 12, 1.7, 1.7])
    spd = np.interp(tt, [0, 2, 4, 7, 10, 13, 15, 19.3, 200], [0.5, 1, 15, 27, 26, 10, 4, 1.4, 1.4])

# ---------- beds ----------
# 1. altitude wind: strong up high, gone by street level
g_alt = db(np.interp(z, [8, 40, 120, 300], [-60, -24, -6, -4])) * curve([(0, -60), (0.6, 0), (105, 0)])
add_bed(load("sfx/amb_altitude.mp3"), g_alt * db(-12), "amb")
# 1b. the city far below: the roar that says "city", strongest up high, handed to the street bed near the ground
g_city = db(np.interp(z, [5, 30, 100, 300], [-40, -14, -4, -6])) * curve([(0, -60), (0.8, 0), (105, 0)])
add_bed(load("sfx/amb_city_far.mp3"), g_city * db(-8), "amb")
# 2. dive wind: level follows speed^2 (dynamic pressure), with a brighter tone as it rises
w = load("sfx/amb_dive_wind.mp3")
g_dive = db(np.clip(20 * np.log10(np.maximum(spd, 0.3) / 27.0) * 2, -60, 0)) * (tt < 21)
add_bed(w, g_dive * db(-15), "amb")
# 3. street: rises as the camera comes down; after the door it is behind glass
street = loop_to(load("sfx/amb_street.mp3"), N)
g_st = db(np.interp(z, [2, 15, 60, 200], [0, -4, -22, -50]))
door_open = curve([(0, 0), (T_DOOR, 0), (T_PASS + 1.8, -14), (105, -14)])  # closer shuts behind him
g_st = g_st * door_open * curve([(0, 0), (T_CLOSED1, 0), (T_CLOSED1 + 0.1, -30), (105, -30)])
street_glass = var_lp(street, np.interp(tt, [0, T_DOOR, T_PASS + 1.8, 105], [16000, 16000, 700, 700]))
add_bed(street_glass, g_st * db(+9), "amb")
# 4. lobby: in through the door, out behind the lift doors
lobby = loop_to(load("sfx/amb_lobby.mp3"), N)
g_lb = curve([(0, -60), (T_DOOR - 0.6, -30), (T_PASS + 0.4, 0), (T_CLOSE1, 0), (T_CLOSED1, -22), (T_CLOSED1 + 1.5, -60), (105, -60)])
lobby_f = var_lp(lobby, np.interp(tt, [0, T_DOOR, T_PASS + 0.3, T_CLOSE1, T_CLOSED1, 105], [900, 900, 16000, 16000, 500, 500]))
add_bed(lobby_f, g_lb * db(+2), "amb")
# 5. cab: the bed under the motor, from doors closing to doors open + walk out
g_cab = curve([(0, -60), (T_CLOSE1, -60), (T_CLOSED1, -6), (T_START, 0), (T_STOP, -3), (T_OPENED42, -8), (T_OPENED42 + 2.5, -60), (105, -60)])
add_bed(load("sfx/amb_cab_ride.mp3"), g_cab * db(-13), "amb")
# 6. office on 42: through the opening doors, then all around
office = loop_to(load("sfx/amb_office_v2.mp3"), N)
g_of = curve([(0, -60), (T_OPEN42, -60), (T_OPENED42, -2), (T_OPENED42 + 2, 0), (105, 0)])
office_f = var_lp(office, np.interp(tt, [0, T_OPEN42, T_OPENED42, 105], [600, 600, 16000, 16000]))
add_bed(office_f, g_of * db(+10), "amb")
# 7. the ending rhyme: faint high wind on the window glass as his view drifts to the city
g_win = curve([(0, -80), (T_DRIFT, -80), (T_DRIFT + 2.5, -34), (105, -32)])
add_bed(biquad(loop_to(load("sfx/amb_altitude.mp3"), N), "lp", 500), g_win, "amb")

# ---------- lift motor and shaft wind (physics from cab speed) ----------
if CAM is not None:
    cz = np.interp(tt, fr_t, CAM["pos"][:, 2])
    v_cab = np.abs(np.gradient(cz) * SR) * ((tt > T_START - 0.2) & (tt < T_STOP + 0.2))
else:
    # jerk-limited 1.0 m/s^2, 6 m/s profile fitted to the trip duration
    Tt = T_STOP - T_START; ta = 6.0; v_cab = np.zeros(N)
    u = tt - T_START
    v_cab = np.where((u > 0) & (u < ta), 6 * np.sin(np.pi / 2 * u / ta) ** 2, v_cab)
    v_cab = np.where((u >= ta) & (u <= Tt - ta), 6.0, v_cab)
    ud = Tt - u
    v_cab = np.where((u > Tt - ta) & (u < Tt), 6 * np.sin(np.pi / 2 * ud / ta) ** 2, v_cab)
v_cab = np.clip(np.convolve(v_cab, np.ones(4800) / 4800, "same"), 0, 8)
vn = v_cab / 6.0
f0 = 48 + 14 * vn                                    # motor fundamental (Hz)
ph = 2 * np.pi * np.cumsum(f0) / SR
motor = sum((0.6 / k) * np.sin(k * ph + rng.uniform(0, 6.28)) for k in range(1, 7))
whine_ph = 2 * np.pi * np.cumsum(220 + 700 * vn) / SR   # inverter / gear whine rises with speed
motor = motor * (0.25 + 0.75 * vn) + 0.06 * np.sin(whine_ph) * vn
motor *= (tt > T_START - 0.3) & (tt < T_STOP + 0.6)
noise = rng.standard_normal(N)
shaft = biquad(biquad(noise, "hp", 180), "lp", 1800) * (vn ** 2)
rides = (motor * db(-30) + shaft * db(-34)) * curve([(0, 0), (T_STOP + 0.3, 0), (T_STOP + 1.0, -60), (105, -60)])
add_bed(rides, np.ones(N), "lift", width=0.3)
report["lift"] = {"v_peak": float(v_cab.max()), "camera_z": CAM is not None}

# ---------- point cues ----------
def cue(file, t, gain_db, align="onset", pos=None, pan=None, lp=None, stem="sfx", name=None):
    x = load(file)
    if lp:
        x = biquad(x, "lp", lp)
    off = onset_offset(x) if align == "onset" else (peak_offset(x) if align == "peak" else 0.0)
    g, p = place(t, pos)
    if pan is not None:
        p = pan
    add(x, t - off, db(gain_db) * g, p, stem, zone=zone_at(t))
    report.setdefault("cue_peaks", []).append((name or os.path.basename(file), round(t, 2), float(np.abs(x).max() * db(gain_db) * g)))
    report["cues"].append({"name": name or os.path.basename(file), "t": round(t, 3), "start": round(t - off, 3),
                           "gain_db": gain_db, "dist_gain_db": round(20 * np.log10(max(g, 1e-6)), 1), "pan": round(p, 2)})

_hs = [(e["t"], e.get("zone")) for e in events if e["event"] == "heel_strike" and e.get("zone")]
def zone_at(t):
    z_ = None
    for tt_, zz in _hs:
        if tt_ <= t + 0.3: z_ = zz
        else: break
    if z_ is None: return "plaza"
    if T_CLOSE1 + 1.0 < t < T_OPEN42 + 0.5: return "cab"
    return z_

def ev_pos(name):
    for e in events:
        if e["event"] == name and "pos" in e:
            return e["pos"]
    return None

cue("sfx/door_glass_v3.mp3", T_DOOR, -21, "onset", ev_pos("door_push"), name="glass door push + closer")
# turnstile: a synthesized reader beep at the tap contact, then flaps on every crossing (placed by lane)
T_TAP = ev_t("reader_tap_contact", T_TURN)
beep = np.sin(2 * np.pi * 2350 * np.arange(int(0.11 * SR)) / SR) * np.hanning(int(0.11 * SR)) ** 0.3
g_, p_ = place(T_TAP, ev_pos("reader_tap_contact") or ev_pos("turnstile_tap"))
add(beep * db(-24), T_TAP + 0.04, g_, p_, "sfx", zone="lobby"); report["cues"].append({"name": "reader beep (synth 2350 Hz)", "t": T_TAP + 0.04})
fl = load("sfx/turnstile_flaps.mp3"); fo_ = onset_offset(fl); nfl = 0
for e in events:
    if e["event"] in ("turnstile_flap_open_start", "turnstile_flap_close_start"):
        g_, p_ = place(e["t"], e.get("pos"))
        add(fl, e["t"] - fo_, db(-26 if "open" in e["event"] else -29) * g_, p_, "sfx", zone="lobby"); nfl += 1
report["turnstile_flap_cues"] = nfl
cue("sfx/call_button.mp3", T_CALL, -22, "onset", ev_pos("call_button_press"), name="call button")
cue("sfx/ding_c.mp3", T_DING1, -21, "onset", ev_pos("lift_ding_L1"), name="ding L1")
cue("sfx/doors_open_b.mp3", T_OPEN1, -14, "start", ev_pos("lift_doors_open_start_L1"), name="doors open L1")
cue("sfx/doors_close_a.mp3", T_CLOSE1, -14, "start", ev_pos("lift_doors_close_start_L1"), name="doors close L1")
cue("sfx/cab_start_up.mp3", T_START - 0.15, -18, "onset", None, 0.0, name="cab start")
xs = load("sfx/cab_stop.mp3"); cue("sfx/cab_stop.mp3", T_STOP - len(xs) / SR + 0.6, -18, "start", None, 0.0, name="cab stop")
cue("sfx/ding_c.mp3", T_DING42, -21, "onset", ev_pos("lift_ding_L42"), name="ding L42")
cue("sfx/doors_open_b.mp3", T_OPEN42, -13, "start", ev_pos("lift_doors_open_start_L42"), name="doors open L42")
cue("sfx/doors_close_a.mp3", T_CLOSE42, -22, "start", ev_pos("lift_doors_close_start_L42"), lp=2500, name="doors close L42 (behind)")
cue("sfx/chair_rail_v2.mp3", T_RAIL, -25, "onset", ev_pos("chair_contact"), name="chair rail")
cue("sfx/cup_down.mp3", T_CUP, -12, "peak", ev_pos("cup_land"), name="cup down")
cue("sfx/sit_chair_v2.mp3", T_SIT, -21, "peak", None, 0.0, name="sit")
# office-chair gas lift: a short bright hiss as his weight lands (synth: band-passed noise, fast decay)
nh = int(0.35 * SR); hiss = biquad(biquad(rng.standard_normal(nh), "hp", 2800), "lp", 7000) * np.exp(-np.arange(nh) / (0.09 * SR))
add(hiss * db(-24), T_SIT + 0.02, 1.0, 0.0, "sfx"); report["cues"].append({"name": "gas-lift hiss (synth)", "t": T_SIT + 0.02})

# ---------- footsteps: his own ----------
STEPS = json.load(open(os.path.join(ROOT, "steps/index.json")))
def pick(kind, last):
    pool = [s for s in STEPS[kind] if s["peak"] > 0.1]
    choices = [s for s in pool if s["file"] != last] or pool
    return choices[rng.integers(len(choices))]

def surface_of(e):
    s = e.get("surface") or ""
    if s in ("plaza_paver",): return "fs_paver"
    if s in ("entrance_mat",): return "fs_mat"
    if s in ("lobby_stone", "lift_lobby_stone"): return "fs_lobby"
    if s in ("cab_floor",): return "fs_cabfloor"
    if s in ("office_carpet",): return "fs_carpet"
    t = e["t"]  # fallback by story time
    if t < T_PASS: return "fs_paver"
    if t < 50: return "fs_lobby"
    if t < 86.5: return "fs_lobby"
    return "fs_carpet"

SURF_DB = {"fs_paver": -20, "fs_lobby": -18, "fs_mat": -23, "fs_carpet": -21, "fs_cabfloor": -19}
last = None; nsteps = 0
for e in events:
    if e["event"] != "heel_strike":
        continue
    kind = surface_of(e); src = "fs_lobby" if kind == "fs_cabfloor" else kind
    s = pick(src, last); last = s["file"]
    x = norm_peak(load(os.path.join(ROOT, s["file"])), 0.5)
    if kind == "fs_cabfloor":
        x = biquad(biquad(x, "lp", 3200), "lowshelf", 180, gain_db=4)
    g, p = place(e["t"], e.get("pos"), ref_dist=1.6)  # feet are ~1.6 m below his eye
    if CAM is None and e["t"] < 18.0:
        g = db(np.interp(e["t"], [0, 10, 16, 18], [-60, -40, -18, 0]))
    add(x, e["t"] - onset_offset(x), db(SURF_DB[kind] + rng.uniform(-1.5, 1.5)) * g, p * 0.3, "steps", zone=e.get("zone"))
    nsteps += 1
report["his_steps"] = nsteps

# ---------- passers-by ----------
HEEL_VARIANTS = {0, 2, 6, 10, 15, 19}   # skirt variants (sheet v2): low heels / flats
pb_steps = [e for e in events if e["event"] in ("passer_heel_strike", "passerby_heel_strike", "heel_strike_passer_by")]
if pb_steps:
    for e in pb_steps:
        kind = "pass_heels" if (int(e.get("variant", 0)) in HEEL_VARIANTS) else "pass_shoes"
        s = pick(kind, None); x = norm_peak(load(os.path.join(ROOT, s["file"])), 0.4)
        sd = -17
        if e.get("surface") == "office_carpet":
            x = biquad(x, "lp", 1600); sd = -20
        g, p = place(e["t"], e.get("pos"), 1.6)
        add(x, e["t"] - onset_offset(x), db(sd + rng.uniform(-2, 2)) * g, p, "steps", zone=e.get("zone"))
    report["passer_steps"] = len(pb_steps)
else:
    for k, nb in enumerate(EV.get("near_passers_by", [])):
        if nb["dist_to_lens_m"] > 2.5:
            continue
        kind = "pass_heels" if k % 2 else "pass_shoes"
        for j, dt in enumerate((-0.55, 0.0, 0.55)):
            s = pick(kind, None); x = norm_peak(load(os.path.join(ROOT, s["file"])), 0.35)
            g, p = place(nb["t"] + dt, nb.get("pos"), 1.0)
            if CAM is None:
                g = 1.0 / max(1.0, nb["dist_to_lens_m"]); p = 0.6 * (1 if k % 2 else -1) * (-1 if j == 0 else 1)
            add(x, nb["t"] + dt, db(-19) * g, p, "steps")
    report["passer_steps"] = "fallback (near_passers_by)"

# ---------- reverb returns ----------
from scipy.signal import fftconvolve
rev = np.zeros((N, 2))
for k_, (z_, (rt, _)) in enumerate(ZONES.items()):
    if np.abs(sends[z_]).max() == 0: continue
    h = ir(rt, 100 + k_)
    for c in range(2):
        rev[:, c] += fftconvolve(sends[z_], h[:, c])[:N]
L += rev[:, 0]; R += rev[:, 1]; stems["reverb"] = rev
report["reverb_zones"] = {z_: round(float(np.abs(sends[z_]).max()), 4) for z_ in ZONES}

# ---------- bed compressor (tame clattery beds before the master) ----------
def compress(a, ratio=3.0, over_db=4.0, att=0.010, rel=0.250, pct=70, win=2400, key="amb"):
    from scipy.signal import lfilter
    m = np.sqrt(np.convolve((a ** 2).mean(1), np.ones(win) / win, "same")) + 1e-9
    act = m[m > m.max() * 1e-3]
    thr = np.percentile(act, pct) * db(over_db)
    g = np.where(m > thr, (thr / m) ** (1 - 1 / ratio), 1.0)
    def smooth(x, tc):
        k = np.exp(-1 / (tc * SR)); y, _ = lfilter([1 - k], [1, -k], x, zi=[x[0] * k]); return y
    gs = np.minimum(smooth(g, att), smooth(g, rel))
    report[key + "_comp_max_gr_db"] = round(float(20 * np.log10(gs.min())), 1)
    return a * gs[:, None]
stems["amb"] = compress(stems["amb"])
stems["amb"] = compress(stems["amb"], ratio=6.0, over_db=9.0, att=0.001, rel=0.060, pct=90, win=96, key="amb_peak")
stems["steps"] = compress(stems["steps"], ratio=4.0, over_db=8.0, att=0.0008, rel=0.080, pct=90, win=96, key="steps")
tot = sum(stems.values()); L = tot[:, 0]; R = tot[:, 1]

# ---------- master ----------
mix = np.stack([L, R], 1)
fade = np.ones(N); fo = int(0.6 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 2; fade[:int(0.02 * SR)] = np.linspace(0, 1, int(0.02 * SR))
mix *= fade[:, None]
tmp = OUT + ".pre.wav"
def write(p, x):
    x = np.clip(x, -1, 1); w = wave.open(p, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype("<i2").tobytes()); w.close()
pk = float(np.abs(mix).max()); mix_s = mix * (0.5 / pk) if pk > 0.5 else mix
write(tmp, mix_s)
meas = subprocess.run([FF, "-nostats", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
import re
I = float(re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", meas, re.M)[-1])
gain = TARGET - I
subprocess.run([FF, "-y", "-loglevel", "error", "-i", tmp, "-af", f"volume={gain:.2f}dB,alimiter=limit=0.79:attack=3:release=60:level=false",
                "-ar", str(SR), "-c:a", "pcm_s24le", OUT], check=True)
os.remove(tmp)
pre = np.abs(mix_s).max(1) * db(gain)
report["limiter_excess_db"] = {i: round(float(20 * np.log10(pre[i * SR:(i + 1) * SR].max() + 1e-9) + 2.05), 1) for i in range(int(DUR)) if pre[i * SR:(i + 1) * SR].max() > db(-2.05)}
fin = subprocess.run([FF, "-nostats", "-i", OUT, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
report["integrated_lufs"] = float(re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", fin, re.M)[-1])
report["true_peak_dbfs"] = float(re.findall(r"^\s+Peak:\s+(-?[\d.]+) dBFS", fin, re.M)[-1])
report["lra"] = float(re.findall(r"^\s+LRA:\s+(-?[\d.]+) LU", fin, re.M)[-1])
for k, a in stems.items():
    report.setdefault("stem_peak_dbfs", {})[k] = round(20 * np.log10(np.abs(a).max() * (0.5 / pk if pk > 0.5 else 1) * db(gain) + 1e-9), 1)
scale_ = (0.5 / pk if pk > 0.5 else 1) * db(gain)
report["stem_sec_peaks"] = {k: [round(20 * np.log10(np.abs(a[i * SR:(i + 1) * SR]).max() * scale_ + 1e-9), 1) for i in range(int(DUR))] for k, a in stems.items()}
bed_rms = float(np.sqrt(np.mean(stems["amb"] ** 2)))
report["cue_peaks"] = sorted([(n_, t_, round(20 * np.log10(p_ / bed_rms + 1e-12), 1)) for n_, t_, p_ in report.get("cue_peaks", [])], key=lambda r: -r[2])
json.dump(report, open(os.path.join(ROOT, "mix_report.json"), "w"), indent=1)
print(json.dumps({k: report[k] for k in ("events_file", "camera", "his_steps", "integrated_lufs", "true_peak_dbfs", "lra")}))
