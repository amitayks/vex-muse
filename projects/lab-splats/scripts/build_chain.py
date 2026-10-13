#!/usr/bin/env python3
"""build_chain.py - join several splat worlds into ONE unbroken camera move (shot JSON for modal_splat.py).

Each world has its own local camera keys (its own frame: OpenCV, y down, camera of the source image at the origin).
At each cut time D_i the next world is placed so that its local camera pose at D_i equals the current world's
camera pose at D_i: P_{i+1} = P_i . C_i(D_i) . C_{i+1}(D_i)^-1. The global camera follows world i before D_i and
world i+1 after it, blended over +-blend s, so position, aim and speed stay continuous.

Transitions at every cut: world i dissolves far-to-near into motes, a morph carries motes from i to i+1, world
i+1 assembles far-to-near. The film opens with world 0 assembling from dust and ends with the last world dissolving.

  python3 build_chain.py chain.json out_shot.json [--width 1920 --height 1080 --samples 8 --preview]
"""
import json, math, sys, argparse
import numpy as np

def norm(v): return v / max(np.linalg.norm(v), 1e-12)

def look_c2w(pos, look, up=(0, -1, 0), roll=0.0):
    pos, look, up = (np.asarray(x, float) for x in (pos, look, up))
    f = norm(look - pos); d = -norm(up); r = norm(np.cross(d, f)); d = np.cross(f, r)
    if roll:
        a = math.radians(roll); r, d = r * math.cos(a) + d * math.sin(a), -r * math.sin(a) + d * math.cos(a)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = r, d, f, pos
    return M

def catmull(P, T, t):
    P = np.asarray(P, float); n = len(P)
    if n == 1 or t <= T[0]: return P[0]
    if t >= T[-1]:   # extrapolate gently along the last segment so a world can be held past its last key
        v = (P[-1] - P[-2]) / max(T[-1] - T[-2], 1e-9) if n > 1 else 0
        return P[-1] + v * (t - T[-1])
    i = max(j for j in range(n - 1) if T[j] <= t); u = (t - T[i]) / max(T[i + 1] - T[i], 1e-9)
    tm = lambda a, b: T[min(max(b, 0), n - 1)] - T[min(max(a, 0), n - 1)]
    dt = T[i + 1] - T[i]; p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n - 1)]
    m1 = (p2 - p0) / max(tm(i - 1, i + 1), 1e-9) * dt; m2 = (p3 - p1) / max(tm(i, i + 2), 1e-9) * dt
    u2, u3 = u * u, u ** 3
    return (2*u3 - 3*u2 + 1) * p1 + (u3 - 2*u2 + u) * m1 + (-2*u3 + 3*u2) * p2 + (u3 - u2) * m2

def local_pose(w, t):
    K = w["keys"]; T = [k["t"] for k in K]
    pos = catmull([k["pos"] for k in K], T, t); look = catmull([k["look"] for k in K], T, t)
    fov = float(catmull([[k.get("fov", 55)] for k in K], T, t)[0]); roll = float(catmull([[k.get("roll", 0)] for k in K], T, t)[0])
    return look_c2w(pos, look, roll=roll), fov, float(np.linalg.norm(look - pos))

def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def blend_pose(A, B, w):
    """Blend two c2w poses: positions and forward/down axes lerped, then re-orthonormalised."""
    p = A[:3, 3] * (1 - w) + B[:3, 3] * w
    f = norm(A[:3, 2] * (1 - w) + B[:3, 2] * w); d = A[:3, 1] * (1 - w) + B[:3, 1] * w
    r = norm(np.cross(d, f)); d = np.cross(f, r)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = r, d, f, p
    return M

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("chain"); ap.add_argument("out")
    ap.add_argument("--width", type=int); ap.add_argument("--height", type=int); ap.add_argument("--samples", type=int)
    ap.add_argument("--fov-scale", type=float, default=1.0, help="e.g. vertical cut: wider vertical fov")
    a = ap.parse_args()
    C = json.load(open(a.chain)); W = C["worlds"]; fps = C.get("fps", 30); dur = C["duration"]
    cuts = [w["cut"] for w in W[:-1]]            # time world i hands over to world i+1
    blend = C.get("blend", 0.6)
    # placements
    P = [np.eye(4)]
    for i in range(len(W) - 1):
        Ci, _, _ = local_pose(W[i], cuts[i]); Cn, _, _ = local_pose(W[i + 1], cuts[i])
        P.append(P[i] @ Ci @ np.linalg.inv(Cn))
    # per-frame global camera
    frames, fovs, focus = [], [], []
    n = int(round(dur * fps))
    for fi in range(n):
        t = fi / fps
        i = sum(1 for c in cuts if t >= c)
        G, fov, fd = local_pose(W[i], t); G = P[i] @ G
        for j, c in enumerate(cuts):   # blend around each cut
            if abs(t - c) < blend:
                A, fa, da = local_pose(W[j], t); B, fb, db = local_pose(W[j + 1], t)
                w = smooth((t - (c - blend)) / (2 * blend))
                G = blend_pose(P[j] @ A, P[j + 1] @ B, w); fov = fa * (1 - w) + fb * w; fd = da * (1 - w) + db * w
        frames.append([round(float(x), 6) for x in G.reshape(-1)]); fovs.append(round(fov * a.fov_scale, 4)); focus.append(round(fd, 4))
    cam_at = lambda t: np.asarray(frames[min(int(round(t * fps)), n - 1)]).reshape(4, 4)
    # layers with effects
    tr = C.get("transition", {}); pre, post = tr.get("pre", 1.4), tr.get("post", 0.7)
    mote = tr.get("mote", 0.0025); layers = []; morphs = []
    for i, w in enumerate(W):
        fx = []
        t_in = cuts[i - 1] if i > 0 else None; t_out = cuts[i] if i < len(W) - 1 else None
        if i == 0 and C.get("open"):
            o = C["open"]; org = cam_at(o.get("t1", 2.0))[:3, 3].tolist()
            fx.append({"type": "assemble", "t0": o.get("t0", 0.0), "t1": o.get("t1", 2.0), "origin": org, "order": o.get("order", "far"),
                       "spread": 0.7, "drift": [0, -0.05, -0.5], "turb": 0.15, "mote": mote, "keep": 0.05, "fade_pow": 2.0,
                       "gain": o.get("gain", tr.get("dust_gain", 1.4)), "seed": 101})
        if t_in is not None:
            org = cam_at(t_in)[:3, 3].tolist()
            fx.append({"type": "assemble", "t0": t_in - pre + tr.get("b_start", 0.45), "t1": t_in + post, "origin": org, "order": "far", "spread": 0.7,
                       "drift": [0, -0.05, -0.5], "turb": 0.12, "mote": mote, "keep": 0.03, "fade_pow": 2.0, "gain": tr.get("dust_gain", 1.4), "seed": 200 + i})
        if t_out is not None:
            org = cam_at(t_out)[:3, 3].tolist()
            fx.append({"type": "dissolve", "t0": t_out - pre, "t1": t_out + post - tr.get("a_trim", 0.45), "origin": org, "order": "far", "spread": 0.7,
                       "drift": [0, -0.05, -0.5], "turb": 0.12, "mote": mote, "keep": 0.03, "fade_pow": 2.6, "gain": tr.get("dust_gain", 1.4), "seed": 300 + i})
            morphs.append({"from": i, "to": i + 1, "t0": t_out - pre, "t1": t_out + post, "n": tr.get("n", 55000), "spread": 0.6,
                           "stagger": "wave", "lag": 0.25, "min_flight": 0.45, "cam_t": t_out, "pull": 0.18, "turb": 0.12,
                           "mote": mote, "gain": tr.get("gain", 1.6), "glow": tr.get("glow", [0.35, 0.28, 0.18]), "rmin": 0.45, "seed": 400 + i})
        if i == len(W) - 1 and C.get("close"):
            c = C["close"]; org = cam_at(c.get("t0", dur - 2))[:3, 3].tolist()
            fx.append({"type": "dissolve", "t0": c["t0"], "t1": c["t1"], "origin": org, "order": c.get("order", "far"), "spread": 0.7,
                       "drift": [0, -0.05, -0.5], "turb": 0.15, "mote": mote, "keep": 0.05, "fade_pow": 2.0,
                       "gain": c.get("gain", tr.get("dust_gain", 1.4)), "seed": 500})
        a0 = (t_in - pre - 0.1) if t_in is not None else -10.0   # sub-frame shutter samples before t=0 must still see world 0
        a1 = (t_out + post + 0.1) if t_out is not None else dur + 1
        L = {"ply": w["ply"], "xform": [round(float(x), 7) for x in P[i].reshape(-1)], "effects": fx, "active": [a0, a1]}
        if w.get("grade"): L["grade"] = w["grade"]
        layers.append(L)
    shot = {"width": a.width or C.get("width", 1920), "height": a.height or C.get("height", 1080), "fps": fps, "duration": dur,
            "bg": C.get("bg", [0, 0, 0]),
            "lens": dict(C.get("lens", {"samples": 8, "shutter": 0.5}), **({"samples": a.samples} if a.samples else {})),
            "camera": {"type": "frames", "fps": fps, "c2w": frames, "fov": fovs, "focus": focus},
            "layers": layers, "morphs": morphs}
    light = C.get("transition", {}).get("light")   # rgb of the light behind each cut (None = black)
    haze = (C.get("open") or {}).get("haze")       # rgb behind the opening assembly: the world condenses out of haze, not out of black
    if light or haze:
        o = C.get("open") or {}
        bk = [[-10.0, *haze], [o.get("t1", 2.0) - 0.2, *haze], [o.get("t1", 2.0) + 0.5, 0, 0, 0]] if haze else [[0.0, 0, 0, 0]]
    if light:
        for c in cuts:
            bk += [[c - pre, 0, 0, 0], [c - pre + 0.55, *light], [c + 0.3, *light], [c + post + 0.4, 0, 0, 0]]
    if light or haze:
        shot["bg_keys"] = bk
    json.dump(shot, open(a.out, "w"))
    print(json.dumps({"frames": n, "cuts": cuts, "placements": [np.round(p[:3, 3], 3).tolist() for p in P]}))

if __name__ == "__main__":
    main()
