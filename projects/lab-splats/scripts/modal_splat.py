"""modal_splat.py - Muse's gaussian-splat farm on Modal (gsplat 1.5.3, torch 2.4.1, CUDA 12.4).

Fetch captures, train them with gsplat (MCMC), and render camera paths frame-exact with a film lens
(motion blur, thin-lens depth of field, pixel-jitter antialiasing) and per-splat effects.

  source tools/env.sh
  $PY -m modal run --detach projects/lab-splats/scripts/modal_splat.py::fetch --dataset mipnerf360   # research data: lab study only, never posted
  $PY -m modal run --detach projects/lab-splats/scripts/modal_splat.py::train_run --data 360_v2/garden --name garden \
        --factor 2 --cap 3000000 --steps 30000
  $PY -m modal run projects/lab-splats/scripts/modal_splat.py::render --shot shots/x.json --out renders/x.mp4
  $PY -m modal run projects/lab-splats/scripts/modal_splat.py::url --url <https> --dest worlds/<id>.ply

Volume `muse-splats` (mounted at /vol):
  /vol/data/<dataset>/<scene>/{images*,sparse}       captures in COLMAP layout
  /vol/runs/<name>/{ply,ckpts,stats,renders}          training output (gsplat layout)
  /vol/runs/<name>/cameras.json                       training cameras in the PLY's world frame
  /vol/worlds/<id>.ply                                generated worlds (Marble, TripoSplat, ...)

Shot JSON (paths in "ply" are relative to /vol):
{
 "width":1920, "height":1080, "fps":30, "duration":8, "bg":[0,0,0],
 "lens": {"samples":8, "shutter":0.5, "aperture":0.0, "focus":"look"},    # aperture = lens radius, world units
 "camera": {"type":"keys", "up":[0,0,1] | "auto:<run>", "keys":[{"t":0,"pos":[..],"look":[..],"fov":50,"roll":0}]}
          | {"type":"frames", "c2w":[[16 floats], ...], "fov":[...]}       # OpenCV c2w per frame (Blender export)
 "layers": [{"ply":"runs/garden/ply/point_cloud_29999.ply", "xform":[16 floats] | null,
             "effects":[{"type":"dissolve"|"assemble"|"fade", ...}]}],
 "stills": [t, ...]       # optional: return PNG stills at these times, no video
 "map": {"height":..}     # optional: top-down view with the camera path drawn (for planning)
}
"""
import io, json, math, os, pathlib, subprocess, time
import modal

GSPLAT_TAG = "v1.5.3"
ARCHS = "8.0;8.6;8.9;9.0"
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.10")
    .apt_install("git", "ffmpeg", "wget", "unzip", "libgl1", "libglib2.0-0", "build-essential", "ninja-build")
    .pip_install("torch==2.4.1", "torchvision==0.19.1", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("ninja", "numpy<2.0.0", "jaxtyping", "rich", "plyfile", "imageio[ffmpeg]", "tyro>=0.8.8",
                 "scikit-learn", "tqdm", "torchmetrics[image]", "opencv-python-headless", "Pillow", "tensorboard",
                 "tensorly", "pyyaml", "matplotlib", "splines", "viser", "scipy", "requests")
    .pip_install("gsplat==1.5.3", index_url="https://docs.gsplat.studio/whl/pt24cu124",
                 extra_index_url="https://pypi.org/simple")
    # python-build-standalone reports clang as its compiler; the CUDA image has gcc only
    .env({"TORCH_CUDA_ARCH_LIST": ARCHS, "MAX_JOBS": "8", "CC": "gcc", "CXX": "g++", "LDSHARED": "gcc -pthread -shared"})
    .run_commands(
        "pip install wheel setuptools",
        f"git clone --depth 1 --branch {GSPLAT_TAG} https://github.com/nerfstudio-project/gsplat /opt/gsplat",
        "pip install git+https://github.com/rmbrualla/pycolmap@cc7ea4b7301720ac29287dbe450952511b32125e",
        "pip install git+https://github.com/nerfstudio-project/nerfview@4538024fe0d15fd1a0e4d760f3695fc44ca72787",
        "pip install --no-build-isolation git+https://github.com/rahul-goel/fused-ssim@328dc9836f513d00c4b5bc38fe30478b4435cbb5",
        "pip install --no-build-isolation git+https://github.com/harry7557558/fused-bilagrid@90f9788e57d3545e3a033c1038bb9986549632fe || true",
    )
)
vol = modal.Volume.from_name("muse-splats", create_if_missing=True)
app = modal.App("muse-splats", image=image)

URLS = {
    "mipnerf360": ["http://storage.googleapis.com/gresearch/refraw360/360_v2.zip"],
    "mipnerf360_extra": ["https://storage.googleapis.com/gresearch/refraw360/360_extra_scenes.zip"],
    "zipnerf_undistorted": [f"https://storage.googleapis.com/gresearch/refraw360/zipnerf-undistorted/{s}.zip"
                            for s in ("berlin", "london", "nyc", "alameda")],
}
RENAME = {"mipnerf360": "360_v2", "mipnerf360_extra": "360_v2", "zipnerf_undistorted": "zipnerf_undistorted"}
GPU_RATE = {"L4": 0.80, "L40S": 1.95, "A100-80GB": 2.50, "H100": 3.95}

# ----------------------------------------------------------------------------------------------- fetch
@app.function(timeout=3 * 3600, volumes={"/vol": vol}, cpu=4, memory=8192)
def fetch_dataset(dataset: str, only: str = "") -> dict:
    out = pathlib.Path("/vol/data") / RENAME[dataset]; out.mkdir(parents=True, exist_ok=True)
    got = []
    for url in URLS[dataset]:
        name = url.rsplit("/", 1)[1]
        if only and not any(o in name for o in only.split(",")):
            continue
        z = pathlib.Path("/tmp") / name
        t0 = time.time()
        subprocess.run(["wget", "-q", "-O", str(z), url], check=True)
        subprocess.run(["unzip", "-q", "-o", str(z), "-d", str(out)], check=True)
        z.unlink(); vol.commit()
        got.append({"url": url, "s": round(time.time() - t0, 1)})
    scenes = sorted(p.name for p in out.iterdir() if p.is_dir())
    return {"dir": str(out), "scenes": scenes, "got": got}

@app.function(timeout=3600, volumes={"/vol": vol}, cpu=2, memory=4096)
def fetch_url(url: str, dest: str) -> dict:
    p = pathlib.Path("/vol") / dest; p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["wget", "-q", "-O", str(p), url], check=True); vol.commit()
    return {"dest": str(p), "bytes": p.stat().st_size}

# ----------------------------------------------------------------------------------------------- train
def _export_cameras(data_dir: str, factor: int, out: pathlib.Path):
    import sys, numpy as np
    sys.path.insert(0, "/opt/gsplat/examples")
    from datasets.colmap import Parser
    p = Parser(data_dir=data_dir, factor=factor, normalize=True, test_every=8)
    cams = []
    for i, name in enumerate(p.image_names):
        cid = p.camera_ids[i]; K = p.Ks_dict[cid]; w, h = p.imsize_dict[cid]
        cams.append({"name": name, "c2w": p.camtoworlds[i].tolist(), "K": K.tolist(), "w": w, "h": h})
    pts = p.points
    info = {"cams": cams, "transform": p.transform.tolist(), "scene_scale": float(p.scene_scale),
            "points_bbox": [np.percentile(pts, 2, axis=0).tolist(), np.percentile(pts, 98, axis=0).tolist()],
            "points_median": np.median(pts, axis=0).tolist()}
    (out / "cameras.json").write_text(json.dumps(info))
    return info

@app.function(gpu="L40S", timeout=6 * 3600, volumes={"/vol": vol}, memory=65536)
def train(data: str, name: str, factor: int = 4, cap: int = 3_000_000, steps: int = 30_000,
          extra: str = "", gpu_name: str = "L40S") -> dict:
    vol.reload()
    data_dir = f"/vol/data/{data}"; res = pathlib.Path(f"/vol/runs/{name}"); res.mkdir(parents=True, exist_ok=True)
    cmd = ["python", "simple_trainer.py", "mcmc", "--data_dir", data_dir, "--data_factor", str(factor),
           "--result_dir", str(res), "--disable_viewer", "--save_ply", "--antialiased",
           "--max_steps", str(steps), "--strategy.cap-max", str(cap),
           "--eval_steps", str(steps), "--save_steps", str(steps), "--ply_steps", str(steps)] + (extra.split() if extra else [])
    t0 = time.time()
    log = open(res / "train.log", "w")
    pr = subprocess.Popen(cmd, cwd="/opt/gsplat/examples", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    last = 0.0
    for line in pr.stdout:   # tee: the file keeps everything, stdout (modal app logs) gets a line every 60 s
        log.write(line)
        if time.time() - last > 60: print(line.strip()[-200:], flush=True); last = time.time()
    pr.wait(); r = pr
    log.close(); wall = time.time() - t0
    out = {"rc": r.returncode, "wall_s": round(wall, 1), "cmd": " ".join(cmd),
           "est_usd": round(wall / 3600 * GPU_RATE.get(gpu_name, 2.0), 3)}
    try:
        out["cameras"] = len(_export_cameras(data_dir, factor, res)["cams"])
    except Exception as e:
        out["cameras_err"] = repr(e)
    stats = sorted((res / "stats").glob("val_step*.json")) if (res / "stats").exists() else []
    if stats: out["val"] = json.loads(stats[-1].read_text())
    plys = sorted((res / "ply").glob("*.ply")) if (res / "ply").exists() else []
    out["ply"] = [str(p.relative_to("/vol")) for p in plys]
    out["log_tail"] = (res / "train.log").read_text()[-2500:]
    (res / "run.json").write_text(json.dumps({k: v for k, v in out.items() if k != "log_tail"}, indent=1))
    vol.commit()
    return out

# ----------------------------------------------------------------------------------------------- render core
C0 = 0.28209479177387814

def load_ply(path):
    import numpy as np
    from plyfile import PlyData
    v = PlyData.read(path)["vertex"].data
    names = v.dtype.names
    g = lambda k: np.asarray(v[k], dtype=np.float32)
    means = np.stack([g("x"), g("y"), g("z")], 1)
    sh0 = np.stack([g("f_dc_0"), g("f_dc_1"), g("f_dc_2")], 1)[:, None, :]
    rest = sorted([n for n in names if n.startswith("f_rest_")], key=lambda s: int(s.split("_")[-1]))
    if rest:
        fr = np.stack([g(n) for n in rest], 1)
        shN = fr.reshape(len(means), 3, len(rest) // 3).transpose(0, 2, 1)
    else:
        shN = np.zeros((len(means), 0, 3), np.float32)
    scales = np.stack([g(f"scale_{i}") for i in range(3)], 1)     # log
    quats = np.stack([g(f"rot_{i}") for i in range(4)], 1)         # wxyz
    opac = g("opacity")                                             # logit
    return dict(means=means, sh0=sh0, shN=shN, scales=scales, quats=quats, opac=opac)

def _norm(v):
    import numpy as np
    return v / max(np.linalg.norm(v), 1e-12)

def look_c2w(pos, look, up, roll_deg=0.0):
    import numpy as np
    pos, look, up = (np.asarray(x, np.float64) for x in (pos, look, up))
    f = _norm(look - pos); d = -_norm(up)
    r = _norm(np.cross(d, f)); d = np.cross(f, r)
    if roll_deg:
        a = math.radians(roll_deg); r, d = r * math.cos(a) + d * math.sin(a), -r * math.sin(a) + d * math.cos(a)
    c2w = np.eye(4); c2w[:3, 0], c2w[:3, 1], c2w[:3, 2], c2w[:3, 3] = r, d, f, pos
    return c2w

def _catmull(P, times, t):
    """Centripetal-free uniform Catmull-Rom through points P at key times; clamps at the ends."""
    import numpy as np
    P = np.asarray(P, np.float64); n = len(P)
    if n == 1 or t <= times[0]: return P[0]
    if t >= times[-1]: return P[-1]
    i = max(j for j in range(n - 1) if times[j] <= t)
    u = (t - times[i]) / max(times[i + 1] - times[i], 1e-9)
    p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(i + 2, n - 1)]
    # tangents scaled by segment durations (non-uniform timing keeps speed continuous)
    tm = lambda a, b: times[min(max(b, 0), n - 1)] - times[min(max(a, 0), n - 1)]
    dt = times[i + 1] - times[i]
    m1 = (p2 - p0) / max(tm(i - 1, i + 1), 1e-9) * dt
    m2 = (p3 - p1) / max(tm(i, i + 2), 1e-9) * dt
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2

def _ease(x, kind):
    if kind == "linear": return x
    if kind == "in": return x * x * x
    if kind == "out": return 1 - (1 - x) ** 3
    return x * x * (3 - 2 * x) if kind == "smooth" else (4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2)

def camera_at(cam: dict, t: float, up):
    """Returns (c2w 4x4, vfov deg, focus dist) at time t."""
    import numpy as np
    if cam["type"] == "frames":   # per-frame c2w; sub-frame times blend the two neighbours (motion blur)
        n = len(cam["c2w"]); x = min(max(t * cam["fps"], 0.0), n - 1.0); i0 = int(math.floor(x)); i1 = min(i0 + 1, n - 1); w = x - i0
        A = np.asarray(cam["c2w"][i0], np.float64).reshape(4, 4); B = np.asarray(cam["c2w"][i1], np.float64).reshape(4, 4)
        if w > 1e-6 and i1 != i0:
            p = A[:3, 3] * (1 - w) + B[:3, 3] * w; f = _norm(A[:3, 2] * (1 - w) + B[:3, 2] * w)
            d = A[:3, 1] * (1 - w) + B[:3, 1] * w; r = _norm(np.cross(d, f)); d = np.cross(f, r)
            A = np.eye(4); A[:3, 0], A[:3, 1], A[:3, 2], A[:3, 3] = r, d, f, p
        lerp = lambda v: (v[i0] * (1 - w) + v[i1] * w) if isinstance(v, list) else v
        return A, lerp(cam["fov"]), lerp(cam.get("focus", 3.0))
    keys = cam["keys"]; T = [k["t"] for k in keys]
    if cam.get("ease"):   # one global time warp over the whole move
        a, b = T[0], T[-1]; x = min(max((t - a) / max(b - a, 1e-9), 0), 1); t = a + _ease(x, cam["ease"]) * (b - a)
    pos = _catmull([k["pos"] for k in keys], T, t)
    look = _catmull([k["look"] for k in keys], T, t)
    fov = float(_catmull([[k.get("fov", 50)] for k in keys], T, t)[0])
    roll = float(_catmull([[k.get("roll", 0)] for k in keys], T, t)[0])
    focus = np.linalg.norm(look - pos)
    return look_c2w(pos, look, up, roll), fov, focus

def apply_effects(L, effects, t, torch):
    """Per-splat effects as pure functions of time. L holds torch tensors (means, sh0, shN, scales, quats, opac)."""
    means, sh0, scales, opac = L["means"], L["sh0"], L["scales"], L["opac"]
    alpha = torch.sigmoid(opac)
    for fx in effects or []:
        ty = fx["type"]
        if ty == "fade":
            x = min(max((t - fx["t0"]) / max(fx["t1"] - fx["t0"], 1e-9), 0), 1)
            a = fx.get("from", 0.0) + (fx.get("to", 1.0) - fx.get("from", 0.0)) * x
            alpha = alpha * a
            continue
        if ty not in ("dissolve", "assemble"): continue
        t0, t1 = fx["t0"], fx["t1"]; dur = max(t1 - t0, 1e-6); spread = fx.get("spread", 0.6)
        key = L["_key_" + str(id(fx))] if ("_key_" + str(id(fx))) in L else None
        if key is None:
            g = torch.Generator(device=means.device).manual_seed(int(fx.get("seed", 7)))
            if "dir" in fx:
                d = torch.tensor(fx["dir"], device=means.device, dtype=means.dtype); d = d / d.norm()
                k = (L["means0"] @ d)
            else:
                o = torch.tensor(fx.get("origin", [0, 0, 0]), device=means.device, dtype=means.dtype)
                k = (L["means0"] - o).norm(dim=1)
            if fx.get("norm", "rank") == "rank":   # even sweep through the population (a far sky dome cannot stretch it)
                k = torch.argsort(torch.argsort(k)).float() / max(len(k) - 1, 1)
            else:
                lo, hi = torch.quantile(k[::max(1, len(k) // 200000)], 0.02), torch.quantile(k[::max(1, len(k) // 200000)], 0.98)
                k = ((k - lo) / (hi - lo + 1e-9)).clamp(0, 1)
            if fx.get("order", "near") == "far": k = 1 - k   # far splats go first
            k = (k + fx.get("jitter", 0.08) * torch.randn(len(k), device=means.device, generator=g)).clamp(0, 1)
            rnd = torch.randn(len(k), 3, device=means.device, generator=g)
            L["_key_" + str(id(fx))] = key = (k, rnd)
        k, rnd = key
        s = t0 + k * spread * dur
        p = ((t - s) / ((1 - spread) * dur)).clamp(0, 1)
        if ty == "assemble": p = 1 - p   # disassembled before t0, whole after t1
        p = p * p * (3 - 2 * p)
        drift = torch.tensor(fx.get("drift", [0, 0, 0]), device=means.device, dtype=means.dtype)
        turb = fx.get("turb", 0.3)
        means = means + (p ** 2)[:, None] * (drift[None] + turb * rnd)
        if "mote" in fx:   # kept fraction becomes small round specks; the rest thins out fast
            thr = float(torch.special.ndtri(torch.tensor((1 + fx.get("keep", 0.12)) / 2)))
            keepm = (rnd[:, 0].abs() < thr).float()   # exactly the 'keep' fraction of splats become motes
            w = (p * 3).clamp(0, 1)[:, None]
            scales = scales * (1 - w) + math.log(fx["mote"]) * w
            alpha = alpha * (keepm * (1 - p) ** 0.6 * fx.get("mote_alpha", 1.0) + (1 - keepm) * (1 - p) ** fx.get("fade_pow", 2.0))
        else:
            scales = scales + torch.log(1 + (fx.get("shrink", 0.3) - 1) * p)[:, None]
            alpha = alpha * (1 - p) ** fx.get("fade_pow", 1.5)
        if fx.get("gain"):   # dust glows in its own colour while it flies (dark walls make bright dust, not soot)
            gb = fx["gain"] * (4 * p * (1 - p))[:, None, None]
            sh0 = ((sh0 * C0 + 0.5) * (1 + gb) + 0.08 * gb - 0.5) / C0
        if "glow" in fx:
            gl = torch.tensor(fx["glow"], device=means.device, dtype=means.dtype)
            bump = 4 * p * (1 - p)
            sh0 = sh0 + (bump[:, None, None] * gl[None, None] / C0)
    return means, sh0, scales, alpha

@app.function(gpu="L40S", timeout=3 * 3600, volumes={"/vol": vol}, memory=49152)
def render_shot(shot: dict) -> dict:
    import numpy as np, torch
    from gsplat import rasterization
    vol.reload()
    dev = "cuda"
    W, H, fps = int(shot.get("width", 1920)), int(shot.get("height", 1080)), float(shot.get("fps", 30))
    lens = shot.get("lens", {}); S = int(lens.get("samples", 8)); shutter = float(lens.get("shutter", 0.5))
    aperture = float(lens.get("aperture", 0.0))
    bg = torch.tensor(shot.get("bg", [0, 0, 0]), device=dev, dtype=torch.float32)[None]
    cam = shot["camera"]
    up = cam.get("up", [0, 0, 1])
    if isinstance(up, str) and up.startswith("auto:"):
        info = json.loads(pathlib.Path(f"/vol/runs/{up[5:]}/cameras.json").read_text())
        ups = np.array([-np.array(c["c2w"])[:3, 1] for c in info["cams"]]); up = _norm(ups.mean(0)).tolist()
    layers = []
    t_load = time.time()
    def proc_shadow(sp):   # flat dark gaussians on the ground: a soft contact shadow for an inserted object
        rng0 = np.random.default_rng(int(sp.get("seed", 1))); n = int(sp.get("n", 20000))
        cx, cy, cz = sp["center"]; rx, rz = sp["radii"]
        r = np.sqrt(rng0.random(n)) * 1.6; th = rng0.random(n) * 2 * np.pi
        x, z = cx + rx * r * np.cos(th), cz + rz * r * np.sin(th)
        means = np.stack([x, np.full(n, cy - 0.002), z], 1).astype(np.float32)
        a = sp.get("opacity", 0.5) * np.exp(-0.5 * (r / 0.8) ** 2) * 0.12
        sz = sp.get("size", max(rx, rz) * 0.18)
        return dict(means=means, sh0=np.full((n, 1, 3), -0.5 / C0, np.float32), shN=np.zeros((n, 0, 3), np.float32),
                    scales=np.log(np.tile([[sz, sz * 0.05, sz]], (n, 1))).astype(np.float32),
                    quats=np.tile([[1, 0, 0, 0]], (n, 1)).astype(np.float32),
                    opac=np.log(np.clip(a, 1e-4, 0.999) / (1 - np.clip(a, 1e-4, 0.999))).astype(np.float32))
    for spec in shot["layers"]:
        d = proc_shadow(spec["shadow"]) if "shadow" in spec else load_ply(f"/vol/{spec['ply']}")
        if spec.get("grade"):   # colour match an inserted object: rgb * mul + add on the DC term
            g = spec["grade"]; rgb = d["sh0"] * C0 + 0.5
            rgb = rgb * np.array(g.get("mul", [1, 1, 1]), np.float32) + np.array(g.get("add", [0, 0, 0]), np.float32)
            d["sh0"] = ((rgb - 0.5) / C0).astype(np.float32)
        L = {k: torch.from_numpy(np.ascontiguousarray(v)).to(dev) for k, v in d.items()}
        if spec.get("xform"):
            M = torch.tensor(spec["xform"], device=dev, dtype=torch.float32).reshape(4, 4)
            sc = M[:3, :3].norm(dim=0).mean(); R = M[:3, :3] / sc
            L["means"] = L["means"] @ M[:3, :3].T + M[:3, 3]
            L["scales"] = L["scales"] + torch.log(sc)
            # rotate quats: q' = qR * q
            from scipy.spatial.transform import Rotation as Rot
            qr = Rot.from_matrix(R.cpu().numpy()).as_quat()  # xyzw
            qr = torch.tensor([qr[3], qr[0], qr[1], qr[2]], device=dev, dtype=torch.float32)
            q = L["quats"] / L["quats"].norm(dim=1, keepdim=True)
            w1, x1, y1, z1 = qr; w2, x2, y2, z2 = q.unbind(1)
            L["quats"] = torch.stack([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2,
                                      w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2], 1)
            # note: view-dependent SH is not rotated (small error for strong rotations)
        if spec.get("crop"):   # axis-aligned keep box [[x0,y0,z0],[x1,y1,z1]]
            lo = torch.tensor(spec["crop"][0], device=dev); hi = torch.tensor(spec["crop"][1], device=dev)
            keep = ((L["means"] >= lo) & (L["means"] <= hi)).all(1)
            L = {k: v[keep] for k, v in L.items()}
        L["means0"] = L["means"]
        L["effects"] = spec.get("effects", [])
        L["active"] = spec.get("active")   # [t0, t1]: the layer is skipped outside this window
        layers.append(L)
    t_load = time.time() - t_load

    # ---- morphs: n splats of layer A fly as motes and land as n splats of layer B
    morphs = []
    for mp in shot.get("morphs", []):
        A, B = layers[mp["from"]], layers[mp["to"]]; n = int(mp.get("n", 300000))
        g = torch.Generator(device=dev).manual_seed(int(mp.get("seed", 11)))
        c2w_m, _, _ = camera_at(cam, float(mp.get("cam_t", (mp["t0"] + mp["t1"]) / 2)), up)
        w2c = torch.tensor(np.linalg.inv(c2w_m), device=dev, dtype=torch.float32)
        def pick(L):
            P = L["means"] @ w2c[:3, :3].T + w2c[:3, 3]; z = P[:, 2]
            u, v = P[:, 0] / z.clamp(min=1e-3), P[:, 1] / z.clamp(min=1e-3)
            fov_ok = (z > 0.15) & (u.abs() < mp.get("u_max", 1.4)) & (v.abs() < mp.get("v_max", 0.9))
            wgt = torch.sigmoid(L["opac"]) * fov_ok.float() / (z.clamp(min=0.15) ** mp.get("near_bias", 0.5))
            idx = torch.multinomial(wgt / wgt.sum(), n, replacement=False, generator=g)
            return idx, u[idx], v[idx]
        ia, ua, va = pick(A); ib, ub, vb = pick(B)
        def order(u, v):   # 2D rank: equal-count rows by v, then u inside each row -> layout-keeping pairs
            rows = int(math.sqrt(n)); ov = torch.argsort(v); r = torch.empty_like(ov); r[ov] = torch.arange(n, device=dev)
            row = (r * rows) // n
            return torch.argsort(row.double() * 10.0 + (u.double() - u.min()) / (u.max() - u.min() + 1e-9))
        if mp.get("pairing", "screen") == "screen":
            ia = ia[order(ua, va)]; ib = ib[order(ub, vb)]
        dur = mp["t1"] - mp["t0"]; spread = mp.get("spread", 0.5)
        cpos = torch.tensor(c2w_m[:3, 3], device=dev, dtype=torch.float32)
        if mp.get("stagger") == "wave":   # launch when A's far-to-near front passes, land when B's front passes
            def kd(P):
                d = (P - cpos).norm(dim=1)
                return 1 - torch.argsort(torch.argsort(d)).float() / max(len(d) - 1, 1)   # rank: 0 = far, 1 = near
            s0 = mp["t0"] + kd(A["means0"][ia]) * spread * dur
            land = mp["t0"] + mp.get("lag", 0.4) * dur + kd(B["means0"][ib]) * spread * dur
            land = torch.maximum(land, s0 + mp.get("min_flight", 0.35))
            fl = land - s0
        else:
            key = torch.rand(n, device=dev, generator=g)
            s0 = mp["t0"] + key * spread * dur; fl = torch.full_like(s0, (1 - spread) * dur)
        off = torch.randn(n, 3, device=dev, generator=g)
        towards = torch.tensor(c2w_m[:3, 3], device=dev, dtype=torch.float32)
        morphs.append(dict(mp=mp, ia=ia, ib=ib, s0=s0, land=s0 + fl, fl=fl, off=off, cam=towards,
                           PA=A["means0"][ia], PB=B["means0"][ib], cA=A["sh0"][ia], cB=B["sh0"][ib],
                           sA=A["scales"][ia], sB=B["scales"][ib], qA=A["quats"][ia], qB=B["quats"][ib],
                           aA=torch.sigmoid(A["opac"][ia]), aB=torch.sigmoid(B["opac"][ib])))

    def motes_at(M, t):
        mp = M["mp"]; q = ((t - M["s0"]) / M["fl"]).clamp(0, 1); qe = q * q * (3 - 2 * q); arc = torch.sin(math.pi * qe)
        PA, PB = M["PA"], M["PB"]
        mid_pull = mp.get("pull", 0.35)   # bow the path toward the lens so motes stream past the viewer
        pos = PA * (1 - qe)[:, None] + PB * qe[:, None]
        pos = pos + arc[:, None] * (mid_pull * (M["cam"][None] - pos) + mp.get("turb", 0.25) * M["off"])
        ls = M["sA"] * (1 - qe)[:, None] + M["sB"] * qe[:, None]
        w = (arc ** 0.5)[:, None]; ls = ls * (1 - w) + math.log(mp.get("mote", 0.006)) * w
        col = M["cA"] * (1 - qe)[:, None, None] + M["cB"] * qe[:, None, None]
        if mp.get("gain"):   # luminous in flight: lift the colour around its own hue
            rgb = (col * C0 + 0.5) * (1 + mp["gain"] * arc[:, None, None]); col = (rgb - 0.5) / C0
        if "glow" in mp:
            col = col + arc[:, None, None] * torch.tensor(mp["glow"], device=dev)[None, None] / C0
        cp = torch.tensor(camera_at(cam, t, up)[0][:3, 3], device=dev, dtype=torch.float32)
        d = pos - cp; r = d.norm(dim=1, keepdim=True).clamp(min=1e-6); rmin = mp.get("rmin", 0.35)
        pos = torch.where(r < rmin, cp + d / r * rmin, pos)   # no mote closer than rmin to the lens
        al = M["aA"] * (1 - qe) + M["aB"] * qe
        al = torch.maximum(al, arc * mp.get("mote_alpha", 0.9))
        live = ((t >= M["s0"]) & (t < M["land"])).float()
        quat = torch.where((qe < 0.5)[:, None], M["qA"], M["qB"])
        return pos, quat, ls, al * live, col
    deg = max(int(round(math.sqrt(L["shN"].shape[1] + 1))) - 1 for L in layers) if layers else 0

    def splats_at(t):
        parts = {k: [] for k in ("means", "quats", "scales", "alpha", "colors")}
        K = (deg + 1) ** 2
        for li, L in enumerate(layers):
            if L["active"] and not (L["active"][0] <= t <= L["active"][1]): continue
            m, sh0, sc, al = apply_effects(L, L["effects"], t, torch)
            for M in morphs:   # a mote leaves its source splat at launch and becomes its target splat on landing
                if M["mp"]["from"] == li: al = al.clone(); al[M["ia"]] = al[M["ia"]] * (t < M["s0"]).float()
                if M["mp"]["to"] == li: al = al.clone(); al[M["ib"]] = al[M["ib"]] * (t >= M["land"]).float()
            col = torch.cat([sh0, L["shN"]], 1)
            if col.shape[1] < K:
                col = torch.cat([col, torch.zeros(len(col), K - col.shape[1], 3, device=dev)], 1)
            parts["means"].append(m); parts["quats"].append(L["quats"]); parts["scales"].append(torch.exp(sc))
            parts["alpha"].append(al); parts["colors"].append(col)
        for M in morphs:
            if t < M["s0"].min().item() or t > M["land"].max().item(): continue
            pos, quat, ls, al, col = motes_at(M, t)
            if col.shape[1] < K:
                col = torch.cat([col, torch.zeros(len(col), K - col.shape[1], 3, device=dev)], 1)
            parts["means"].append(pos); parts["quats"].append(quat); parts["scales"].append(torch.exp(ls))
            parts["alpha"].append(al); parts["colors"].append(col)
        if not parts["means"]:   # nothing active: one invisible splat keeps the rasterizer happy
            parts = {"means": [torch.zeros(1, 3, device=dev) + 1e3], "quats": [torch.tensor([[1., 0, 0, 0]], device=dev)],
                     "scales": [torch.full((1, 3), 1e-3, device=dev)], "alpha": [torch.zeros(1, device=dev)],
                     "colors": [torch.zeros(1, K, 3, device=dev)]}
        return {k: torch.cat(v, 0) for k, v in parts.items()}

    bgk = shot.get("bg_keys")   # [[t, r, g, b], ...]: e.g. light behind a transition instead of black
    def bg_at(t):
        if not bgk: return bg[0]
        if t <= bgk[0][0]: v = bgk[0][1:]
        elif t >= bgk[-1][0]: v = bgk[-1][1:]
        else:
            j = max(i for i in range(len(bgk) - 1) if bgk[i][0] <= t); a, b = bgk[j], bgk[j + 1]
            w = (t - a[0]) / max(b[0] - a[0], 1e-9); w = w * w * (3 - 2 * w)
            v = [a[k] * (1 - w) + b[k] * w for k in (1, 2, 3)]
        return torch.tensor(v, device=dev, dtype=torch.float32)
    rng = np.random.default_rng(int(shot.get("seed", 1)))
    def frame(tc, samples):
        acc = torch.zeros(H, W, 3, device=dev)
        for s in range(samples):
            # stratified shutter time, lens point and pixel jitter
            ts = tc + ((s + rng.random()) / samples - 0.5) * (shutter / fps) if samples > 1 else tc
            c2w, fov, focus = camera_at(cam, ts, up)
            fy = (H / 2) / math.tan(math.radians(fov) / 2); fx = fy
            cx, cy = W / 2, H / 2
            if samples > 1:
                cx += rng.random() - 0.5; cy += rng.random() - 0.5
            if aperture > 0 and samples > 1:
                fd = lens.get("focus", "look"); F = focus if fd == "look" else float(fd)
                rr = aperture * math.sqrt((s + rng.random()) / samples); th = 2 * math.pi * rng.random()
                dx, dy = rr * math.cos(th), rr * math.sin(th)
                c2w = c2w.copy(); c2w[:3, 3] += dx * c2w[:3, 0] + dy * c2w[:3, 1]
                cx += fx * dx / F; cy += fy * dy / F
            vm = torch.tensor(np.linalg.inv(c2w), device=dev, dtype=torch.float32)[None]
            Kt = torch.tensor([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], device=dev, dtype=torch.float32)[None]
            sp = splats_at(ts)
            img, al, _ = rasterization(sp["means"], sp["quats"], sp["scales"], sp["alpha"], sp["colors"], vm, Kt,
                                       W, H, sh_degree=deg, near_plane=0.01, far_plane=1e10,
                                       rasterize_mode="antialiased", render_mode="RGB")
            # gsplat 1.5.3 packed mode rejects a [C,3] background: composite over bg here
            acc += (img[0, ..., :3] + (1 - al[0]) * bg_at(ts)).clamp(0, 1)
        return (acc / samples)

    out = {"n_splats": int(sum(len(L["means"]) for L in layers)), "load_s": round(t_load, 1), "deg": deg}
    if "stills" in shot:
        from PIL import Image
        pngs = []
        for t in shot["stills"]:
            im = (frame(float(t), S).cpu().numpy() * 255 + 0.5).astype("uint8")
            b = io.BytesIO(); Image.fromarray(im).save(b, "PNG"); pngs.append(b.getvalue())
        out["stills"] = pngs
        return out
    if "map" in shot:   # top-down planning view with the camera path drawn on it
        from PIL import Image, ImageDraw
        mp = shot["map"]; ctr = np.array(mp["center"], np.float64); upv = _norm(np.array(up, np.float64))
        eye = ctr + upv * mp.get("height", 5.0)
        fwd_hint = np.array(mp.get("north", [0, 1, 0]), np.float64)
        c2w = look_c2w(eye, ctr, fwd_hint, 0)
        fov = mp.get("fov", 70); fy = (H / 2) / math.tan(math.radians(fov) / 2)
        vm = torch.tensor(np.linalg.inv(c2w), device=dev, dtype=torch.float32)[None]
        Kt = torch.tensor([[fy, 0, W / 2], [0, fy, H / 2], [0, 0, 1]], device=dev, dtype=torch.float32)[None]
        sp = splats_at(0.0)
        img, al, _ = rasterization(sp["means"], sp["quats"], sp["scales"], sp["alpha"], sp["colors"], vm, Kt, W, H,
                                   sh_degree=deg, rasterize_mode="antialiased")
        img = img[0, ..., :3] + (1 - al[0]) * bg[0]
        im = Image.fromarray((img.clamp(0, 1).cpu().numpy() * 255).astype("uint8")); dr = ImageDraw.Draw(im)
        w2c = np.linalg.inv(c2w)
        def proj(p):
            q = w2c @ np.array([*p, 1.0]); return (fy * q[0] / q[2] + W / 2, fy * q[1] / q[2] + H / 2)
        dur = float(shot.get("duration", 8)); n = 120
        pts = [proj(camera_at(cam, dur * i / n, up)[0][:3, 3]) for i in range(n + 1)]
        dr.line(pts, fill=(255, 60, 60), width=3)
        for i in range(0, n + 1, 20):
            c2 = camera_at(cam, dur * i / n, up)[0]; a = proj(c2[:3, 3]); b = proj(c2[:3, 3] + c2[:3, 2] * mp.get("arrow", 0.3))
            dr.line([a, b], fill=(255, 220, 0), width=3); dr.text(a, f"{dur * i / n:.1f}s", fill=(255, 255, 255))
        for c in mp.get("cams", []):
            dr.ellipse([proj(c)[0] - 2, proj(c)[1] - 2, proj(c)[0] + 2, proj(c)[1] + 2], fill=(80, 200, 255))
        b = io.BytesIO(); im.save(b, "PNG"); out["map_png"] = b.getvalue()
        return out
    dur = float(shot.get("duration", 8)); f0 = int(shot.get("frame0", 0)); f1 = int(shot.get("frame1", round(dur * fps)))
    tmp = f"/tmp/shot_{f0}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(shot.get("crf", 14)),
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(f0, f1):
        im = (frame(fi / fps, S) * 255 + 0.5).clamp(0, 255).to(torch.uint8).cpu().numpy()
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    wall = time.time() - t0
    out.update({"frames": f1 - f0, "render_s": round(wall, 1), "s_per_frame": round(wall / max(f1 - f0, 1), 3),
                "mp4": open(tmp, "rb").read(), "est_usd": round((wall + t_load) / 3600 * GPU_RATE["L40S"], 4)})
    return out


@app.function(timeout=900, volumes={"/vol": vol}, memory=16384)
def ply_stats(ply: str, radius: float = 1.5, cx: float = 0.0, cz: float = 0.0) -> dict:
    """Bounds, and the ground under the origin (y-down worlds: the ground is the dense layer at +y below the camera)."""
    import numpy as np
    vol.reload(); d = load_ply(f"/vol/{ply}"); m = d["means"]; a = 1 / (1 + np.exp(-d["opac"]))
    out = {"n": len(m), "p1": np.percentile(m, 1, 0).round(3).tolist(), "p99": np.percentile(m, 99, 0).round(3).tolist(),
           "median": np.median(m, 0).round(3).tolist(), "sh_rest": int(d["shN"].shape[1]),
           "scale_med": float(np.exp(np.median(d["scales"]))), "opac_med": float(np.median(a))}
    near = (np.hypot(m[:, 0] - cx, m[:, 2] - cz) < radius) & (a > 0.3)
    if near.sum() > 100:
        y = m[near, 1]; h, e = np.histogram(y, bins=80)
        out["y_hist_near"] = {"edges": e.round(3).tolist(), "counts": h.tolist()}
        out["y_pct_near"] = np.percentile(y, [5, 25, 50, 75, 95]).round(3).tolist()
    for ax, nm in ((0, "x"), (1, "y"), (2, "z")):
        out[f"{nm}_range"] = [float(m[:, ax].min()), float(m[:, ax].max())]
    return out

@app.local_entrypoint()
def stats(ply: str, radius: float = 1.5, cx: float = 0.0, cz: float = 0.0):
    r = ply_stats.remote(ply, radius, cx, cz); h = r.pop("y_hist_near", None)
    print(json.dumps(r))
    if h:
        top = sorted(zip(h["counts"], h["edges"]), reverse=True)[:6]
        print("densest y bins near origin:", [(round(e, 3), c) for c, e in top])


# ----------------------------------------------------------------------------------------------- capture: video -> COLMAP
colmap_image = modal.Image.debian_slim(python_version="3.11").apt_install("colmap", "ffmpeg", "wget").env({"QT_QPA_PLATFORM": "offscreen"})

@app.function(image=colmap_image, cpu=16, memory=32768, timeout=4 * 3600, volumes={"/vol": vol})
def sfm(src: str, name: str, fps: float = 3.0, max_side: int = 1920, overlap: int = 20) -> dict:
    """src: a video under /vol (e.g. uploads/x.mov) or a URL. Writes /vol/data/capture/<name>/{images,sparse/0}."""
    import glob, shutil
    vol.reload(); root = pathlib.Path(f"/vol/data/capture/{name}"); shutil.rmtree(root, ignore_errors=True)
    img = root / "images"; img.mkdir(parents=True)
    if src.startswith("http"):
        subprocess.run(["wget", "-q", "-O", "/tmp/src.mp4", src], check=True); src_path = "/tmp/src.mp4"
    else:
        src_path = f"/vol/{src}"
    t0 = time.time()
    if pathlib.Path(src_path).is_dir():
        for f in sorted(pathlib.Path(src_path).iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic"): shutil.copy(f, img / f.name)
    else:
        vf = f"fps={fps},scale='if(gt(iw,ih),min({max_side},iw),-2)':'if(gt(iw,ih),-2,min({max_side},ih))'"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src_path, "-vf", vf, "-q:v", "2", str(img / "f%05d.jpg")], check=True)
    n = len(list(img.glob("*")))
    db = str(root / "db.db"); sp = root / "sparse"; sp.mkdir()
    def run(*a):
        r = subprocess.run(["colmap", *a], capture_output=True, text=True)
        if r.returncode: raise RuntimeError(" ".join(a[:1]) + ": " + (r.stdout + r.stderr)[-1500:])
        return r
    run("feature_extractor", "--database_path", db, "--image_path", str(img), "--ImageReader.single_camera", "1",
        "--ImageReader.camera_model", "OPENCV", "--SiftExtraction.use_gpu", "0", "--SiftExtraction.max_image_size", str(max_side))
    t1 = time.time()
    run("sequential_matcher", "--database_path", db, "--SiftMatching.use_gpu", "0", "--SequentialMatching.overlap", str(overlap))
    t2 = time.time()
    run("mapper", "--database_path", db, "--image_path", str(img), "--output_path", str(sp))
    t3 = time.time()
    models = sorted(sp.iterdir(), key=lambda d: sum(f.stat().st_size for f in d.iterdir()), reverse=True)
    if models and models[0].name != "0":   # gsplat reads sparse/0: make the biggest model that one
        tmp = sp / "_big"; models[0].rename(tmp)
        for m in sp.iterdir():
            if m != tmp: shutil.rmtree(m)
        tmp.rename(sp / "0")
    an = run("model_analyzer", "--path", str(sp / "0")).stdout + ""
    vol.commit()
    return {"frames": n, "extract_s": round(t1 - t0, 1), "match_s": round(t2 - t1, 1), "map_s": round(t3 - t2, 1),
            "analyzer": an[-900:], "data": f"capture/{name}", "est_usd": round((time.time() - t0) / 3600 * 0.75, 3)}

@app.local_entrypoint()
def capture(src: str, name: str, fps: float = 3.0, max_side: int = 1920):
    print(json.dumps(sfm.remote(src, name, fps, max_side), indent=1))

# ----------------------------------------------------------------------------------------------- local entrypoints
@app.local_entrypoint()
def fetch(dataset: str = "mipnerf360", only: str = ""):
    print(json.dumps(fetch_dataset.remote(dataset, only), indent=1))

@app.local_entrypoint()
def url(url: str, dest: str):
    print(json.dumps(fetch_url.remote(url, dest)))

@app.local_entrypoint()
def train_run(data: str, name: str, factor: int = 4, cap: int = 3_000_000, steps: int = 30_000, extra: str = "",
              gpu: str = "L40S", out: str = ""):
    fn = train.with_options(gpu=gpu) if gpu != "L40S" else train
    res = fn.remote(data, name, factor, cap, steps, extra, gpu)
    print(json.dumps({k: v for k, v in res.items() if k != "log_tail"}, indent=1)); print(res.get("log_tail", "")[-1500:])
    if out:
        pathlib.Path(out).mkdir(parents=True, exist_ok=True)
        pathlib.Path(out, "run.json").write_text(json.dumps(res, indent=1))

@app.local_entrypoint()
def render(shot: str, out: str, frames: str = "", chunks: int = 1):
    spec = json.loads(pathlib.Path(shot).read_text())
    if "stills" in spec:
        res = render_shot.remote(spec); pathlib.Path(out).mkdir(parents=True, exist_ok=True)
        for i, b in enumerate(res.pop("stills")):
            pathlib.Path(out, f"still_{i:02d}.png").write_bytes(b)
        print(json.dumps(res)); return
    if "map" in spec:
        res = render_shot.remote(spec); pathlib.Path(out).write_bytes(res.pop("map_png")); print(json.dumps(res)); return
    fps = float(spec.get("fps", 30)); n = int(round(float(spec.get("duration", 8)) * fps))
    if frames:
        a, b = (int(x) for x in frames.split(":")); spec["frame0"], spec["frame1"] = a, b; n0 = a; n = b
    else:
        n0 = 0
    step = -(-(n - n0) // chunks); jobs = []
    for i in range(chunks):
        a, b = n0 + i * step, min(n, n0 + (i + 1) * step)
        if a < b: jobs.append(dict(spec, frame0=a, frame1=b))
    t0 = time.time(); parts = []; cost = 0.0; stats = []
    for i, res in enumerate(render_shot.map(jobs)):
        p = f"/tmp/splat_part_{os.getpid()}_{i:03d}.mp4"; pathlib.Path(p).write_bytes(res.pop("mp4")); parts.append(p)
        cost += res.get("est_usd", 0); stats.append(res)
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    if len(parts) == 1:
        import shutil; shutil.move(parts[0], out)
    else:
        lst = f"/tmp/splat_parts_{os.getpid()}.txt"; pathlib.Path(lst).write_text("".join(f"file '{p}'\n" for p in parts))
        subprocess.run([os.environ.get("FFMPEG", "ffmpeg"), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", out], check=True)
        for p in parts: os.remove(p)
    print(json.dumps({"out": out, "chunks": len(jobs), "wall_s": round(time.time() - t0, 1), "est_usd": round(cost, 4),
                      "per_chunk": stats}))
