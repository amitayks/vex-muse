#!/usr/bin/env python3
"""roto.py — extract drawing guides from a video plate for the p5 overlay.

  $PY roto.py frames <video> <dir> [--fps 12] [--w 960]           # numbered PNGs (paint on twos)
  $PY roto.py trace <alpha_dir|alpha_video> <out.json> [--eps 2.5] [--min-area 400] [--smooth 2] [--fps 12] [--scale 1920]
        -> {fps, size, frames:[{i, t, shapes:[{outer:[[x,y]...], holes:[[...]], area}], bbox, centroid}]}
           coordinates scaled to --scale wide (studio canvas is 1920x1080)
  $PY roto.py flow <video> <out.json> [--fps 12]                    # global camera dx,dy,zoom per frame (ORB + affine)
  $PY roto.py palette <dir|video> [--k 5] [--bible bible_palette.json]   # dominant colors (+ nearest bible ink)
  $PY roto.py onion <plate_frame.png> <painted_frame.png> <out.png> [--a 0.35]   # alignment check image
"""
import sys, os, json, glob, subprocess, shutil, tempfile
import numpy as np, cv2

def frames(video, d, fps=12, w=960):
    if os.path.isdir(d) and d.startswith(tempfile.gettempdir()): shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},scale={w}:-2", os.path.join(d, "f%05d.png")], check=True)
    print(json.dumps({"dir": d, "frames": len(glob.glob(os.path.join(d, "f*.png")))}))

def read_alpha(src, fps):
    if os.path.isdir(src):
        for f in sorted(glob.glob(os.path.join(src, "*.png"))):
            im = cv2.imread(f, cv2.IMREAD_UNCHANGED)
            yield (im[:, :, 3] if im.ndim == 3 and im.shape[2] == 4 else (im if im.ndim == 2 else cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)))
    else:
        tmp = tempfile.mkdtemp(prefix="roto_a_"); frames(src, tmp, fps); yield from read_alpha(tmp, fps)

def trace(src, out, eps=2.5, min_area=400, smooth=2, fps=12, scale=1920):
    masks = list(read_alpha(src, fps))
    if not masks: print(json.dumps({"error": "no frames"})); return
    h, w = masks[0].shape[:2]; k = scale / w
    if smooth > 0:  # temporal median over +-smooth frames removes matte flicker
        st = np.stack(masks).astype(np.uint8); sm = []
        for i in range(len(st)):
            a, b = max(0, i - smooth), min(len(st), i + smooth + 1); sm.append(np.median(st[a:b], axis=0).astype(np.uint8))
        masks = sm
    res = []
    for i, m in enumerate(masks):
        _, bw = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        cs, hier = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        shapes = []
        if hier is not None:
            hier = hier[0]
            for j, c in enumerate(cs):
                if hier[j][3] != -1 or cv2.contourArea(c) < min_area: continue
                outer = (cv2.approxPolyDP(c, eps, True)[:, 0, :] * k).round(1).tolist()
                holes = []; ch = hier[j][2]
                while ch != -1:
                    if cv2.contourArea(cs[ch]) >= min_area / 4: holes.append((cv2.approxPolyDP(cs[ch], eps, True)[:, 0, :] * k).round(1).tolist())
                    ch = hier[ch][0]
                shapes.append({"outer": outer, "holes": holes, "area": round(cv2.contourArea(c) * k * k)})
        ys, xs = np.nonzero(bw)
        bbox = [round(xs.min() * k, 1), round(ys.min() * k, 1), round((xs.max() - xs.min()) * k, 1), round((ys.max() - ys.min()) * k, 1)] if len(xs) else None
        cen = [round(xs.mean() * k, 1), round(ys.mean() * k, 1)] if len(xs) else None
        res.append({"i": i, "t": round(i / fps, 4), "shapes": sorted(shapes, key=lambda s: -s["area"]), "bbox": bbox, "centroid": cen})
    json.dump({"fps": fps, "size": [scale, round(h * k)], "frames": res}, open(out, "w"))
    print(json.dumps({"out": out, "frames": len(res), "avg_shapes": round(np.mean([len(r["shapes"]) for r in res]), 2)}))

def flow(video, out, fps=12):
    tmp = tempfile.mkdtemp(prefix="roto_f_"); frames(video, tmp, fps, 640)
    fs = sorted(glob.glob(os.path.join(tmp, "f*.png"))); orb = cv2.ORB_create(1500); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    prev = None; acc = np.eye(3); res = [{"i": 0, "dx": 0, "dy": 0, "zoom": 1, "rot": 0}]
    for i, f in enumerate(fs):
        g = cv2.imread(f, cv2.IMREAD_GRAYSCALE); kp, de = orb.detectAndCompute(g, None)
        if prev is not None and de is not None and prev[1] is not None:
            ms = sorted(bf.match(prev[1], de), key=lambda x: x.distance)[:300]
            if len(ms) >= 8:
                p0 = np.float32([prev[0][x.queryIdx].pt for x in ms]); p1 = np.float32([kp[x.trainIdx].pt for x in ms])
                M, _ = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC)
                if M is not None: acc = np.vstack([M, [0, 0, 1]]) @ acc
            s = float(np.sqrt(acc[0, 0] ** 2 + acc[1, 0] ** 2)); k = 1920 / g.shape[1]
            res.append({"i": i, "dx": round(float(acc[0, 2]) * k, 2), "dy": round(float(acc[1, 2]) * k, 2), "zoom": round(s, 4), "rot": round(float(np.arctan2(acc[1, 0], acc[0, 0])), 4)})
        prev = (kp, de)
    json.dump({"fps": fps, "frames": res}, open(out, "w")); print(json.dumps({"out": out, "frames": len(res)}))

def palette(src, k=5, bible=None):
    fs = sorted(glob.glob(os.path.join(src, "*.png")))[::6] if os.path.isdir(src) else None
    if fs is None: tmp = tempfile.mkdtemp(prefix="roto_p_"); frames(src, tmp, 2, 320); fs = sorted(glob.glob(os.path.join(tmp, "*.png")))
    px = np.vstack([cv2.resize(cv2.imread(f), (160, 90)).reshape(-1, 3) for f in fs]).astype(np.float32)
    _, lab, cen = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1), 3, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab.ravel(), minlength=k); order = np.argsort(-cnt)
    hexs = ["#%02x%02x%02x" % tuple(int(v) for v in cen[i][::-1]) for i in order]
    out = {"colors": hexs, "share": [round(float(cnt[i] / cnt.sum()), 3) for i in order]}
    if bible:
        inks = json.load(open(bible))  # {"name": "#rrggbb"}
        rgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)])
        out["nearest_ink"] = [min(inks, key=lambda n: np.linalg.norm(rgb(inks[n]) - rgb(h))) for h in hexs]
    print(json.dumps(out))

def onion(a, b, out, alpha=0.35):
    A = cv2.imread(a); B = cv2.imread(b); A = cv2.resize(A, (B.shape[1], B.shape[0]))
    cv2.imwrite(out, cv2.addWeighted(B, 1 - alpha, A, alpha, 0)); print(out)

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    c = a[0]
    if c == "frames": frames(a[1], a[2], float(opt("--fps", 12)), int(opt("--w", 960)))
    elif c == "trace": trace(a[1], a[2], float(opt("--eps", 2.5)), float(opt("--min-area", 400)), int(opt("--smooth", 2)), float(opt("--fps", 12)), float(opt("--scale", 1920)))
    elif c == "flow": flow(a[1], a[2], float(opt("--fps", 12)))
    elif c == "palette": palette(a[1], int(opt("--k", 5)), opt("--bible"))
    elif c == "onion": onion(a[1], a[2], a[3], float(opt("--a", 0.35)))
    else: print(__doc__)
