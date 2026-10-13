#!/usr/bin/env python3
"""colmap_cameras.py - write cameras.json for a Brush run, in the same shape modal_splat.py writes for gsplat runs.

Brush trains in the raw COLMAP world frame (no normalisation), so the PLY frame = the COLMAP frame and
"transform" is identity. gsplat runs on Modal use Parser(normalize=True); their cameras.json "transform"
maps COLMAP -> gsplat frame. To place a Brush PLY in a gsplat shot, use that transform as the layer "xform".

usage: colmap_cameras.py <scene_dir with sparse/0> <image_dir_name e.g. images_4> <out cameras.json>
Pure stdlib (struct), no numpy.
"""
import json, math, os, struct, sys

CAM_PARAMS = {0: 3, 1: 4, 2: 4, 3: 5, 4: 8, 5: 8, 6: 12, 7: 5, 8: 4, 9: 5, 10: 12}  # model id -> n params

def read_cameras(p):
    out = {}
    with open(p, "rb") as f:
        n, = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            cid, model, w, h = struct.unpack("<iiQQ", f.read(24))
            k = CAM_PARAMS[model]
            out[cid] = dict(model=model, w=w, h=h, params=struct.unpack(f"<{k}d", f.read(8 * k)))
    return out

def read_images(p):
    out = []
    with open(p, "rb") as f:
        n, = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            iid, qw, qx, qy, qz, tx, ty, tz, cid = struct.unpack("<idddddddi", f.read(64))
            name = b""
            while (c := f.read(1)) != b"\x00":
                name += c
            n2d, = struct.unpack("<Q", f.read(8)); f.seek(24 * n2d, 1)
            out.append(dict(id=iid, q=(qw, qx, qy, qz), t=(tx, ty, tz), cam=cid, name=name.decode()))
    return out

def read_points(p, every=1):
    pts = []
    with open(p, "rb") as f:
        n, = struct.unpack("<Q", f.read(8))
        for i in range(n):
            _id, x, y, z, r, g, b, _err = struct.unpack("<QdddBBBd", f.read(43))
            tl, = struct.unpack("<Q", f.read(8)); f.seek(8 * tl, 1)
            if i % every == 0: pts.append((x, y, z))
    return pts

def qrot(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]

def main(scene, imgdir, out):
    sp = os.path.join(scene, "sparse", "0")
    cams = read_cameras(os.path.join(sp, "cameras.bin")); imgs = sorted(read_images(os.path.join(sp, "images.bin")), key=lambda i: i["name"])
    # scale intrinsics to the image folder actually used (images_N)
    from struct import unpack
    sample = os.path.join(scene, imgdir, imgs[0]["name"])
    W1 = H1 = None
    try:
        with open(sample, "rb") as f:  # JPEG SOF scan for size
            d = f.read()
        i = 2
        while i < len(d):
            if d[i] != 0xFF: i += 1; continue
            m = d[i + 1]; L = unpack(">H", d[i + 2:i + 4])[0]
            if m in (0xC0, 0xC1, 0xC2): H1, W1 = unpack(">HH", d[i + 5:i + 9]); break
            i += 2 + L
    except OSError:
        pass
    res = []
    for k, im in enumerate(imgs):
        c = cams[im["cam"]]; R = qrot(im["q"]); t = im["t"]
        Rt = [[R[j][i] for j in range(3)] for i in range(3)]            # R^T
        C = [-sum(Rt[i][j] * t[j] for j in range(3)) for i in range(3)]  # -R^T t
        c2w = [Rt[0] + [C[0]], Rt[1] + [C[1]], Rt[2] + [C[2]], [0, 0, 0, 1]]
        p = c["params"]
        fx, fy, cx, cy = (p[0], p[0], p[1], p[2]) if c["model"] in (0, 2, 3) else (p[0], p[1], p[2], p[3])
        s = (W1 / c["w"]) if W1 else 1.0
        w, h = (W1, H1) if W1 else (c["w"], c["h"])
        res.append({"name": im["name"], "c2w": c2w, "K": [[fx * s, 0, cx * s], [0, fy * s, cy * s], [0, 0, 1]], "w": w, "h": h,
                    "eval": k % 8 == 0})
    pts = read_points(os.path.join(sp, "points3D.bin"))
    def pct(vals, q): v = sorted(vals); return v[min(len(v) - 1, int(q / 100 * len(v)))]
    info = {"frame": "COLMAP (Brush PLY frame, no normalisation)", "image_dir": imgdir, "cams": res,
            "transform": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "scene_scale": None,
            "points_bbox": [[pct([p[i] for p in pts], 2) for i in range(3)], [pct([p[i] for p in pts], 98) for i in range(3)]],
            "points_median": [pct([p[i] for p in pts], 50) for i in range(3)], "n_points": len(pts)}
    ups = [[-c["c2w"][i][1] for i in range(3)] for c in res]; u = [sum(x[i] for x in ups) for i in range(3)]
    nrm = math.sqrt(sum(v * v for v in u)); info["auto_up"] = [v / nrm for v in u]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(info, open(out, "w"))
    print(json.dumps({"cams": len(res), "size": [res[0]["w"], res[0]["h"]], "auto_up": info["auto_up"],
                      "points": len(pts), "median": info["points_median"], "bbox": info["points_bbox"]}))

if __name__ == "__main__":
    main(*sys.argv[1:4])
