#!/usr/bin/env python3
"""cutout.py — turn a generated image into a collage element (PNG with alpha).

  # object on a white ground -> die-cut sticker (white rough border)
  $PY cutout.py raw/cassette.png assets/cassette.png --matte white --shape die --border 14 --max 900
  # photo -> torn-paper print with a fibre rim
  $PY cutout.py raw/bedroom.png assets/bedroom.png --shape torn --inset 0.04 --tear 16 --max 1100
  # hard matte (hair, hands, busy edges) -> Bria through fal.py (paid, ledgered)
  $PY cutout.py raw/hand.png assets/hand.png --matte fal --ledger projects/<slug>/ledger.jsonl --tag hand

--matte  none  | white (flood-fill the near-white ground from the image edges, $0) | fal (Bria, $0.018,
         isolated objects only - a busy scene comes back ~97 % foreground) | sam:<prompt> (SAM 3 text
         prompt, e.g. sam:person, $0.005 - the one for a subject inside a full scene)
--mask   FILE  reuse a saved mask (white = keep) instead of paying again; --savemask FILE keeps one
         An input that already has alpha keeps it.
--shape  die   (subject + rough paper border, the sticker look) | torn (rectangle, torn edges + rim) |
         cut   (subject edge only, no border)
--grade  keep | bw (warm-black newsprint: ink ~#1c1a18, paper ~#efe6d6) | sepia
--inset  crop this fraction from every side first (removes model-made borders on photos)
--tear   torn-edge amplitude px · --rim torn-rim width px · --border die border px · --rough 0..1
--max    longest side after processing · --seed  edge pattern
--notrim keep the full canvas (no pad, no trim): a `cut` subject layer then stays pixel-aligned with the
         `torn` print of the same source + same --inset/--max (depth sandwich: room < year < person)
Prints the output size; LOOK at the result on a dark and a light ground before using it.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes, distance_transform_edt, gaussian_filter, label, zoom

HERE = os.path.dirname(os.path.abspath(__file__))
FAL = os.path.join(HERE, "..", "..", "fal-media", "scripts", "fal.py")
PAPER = np.array([244, 238, 226], np.float32)


def noise(h, w, rng, cell=24, octaves=3):
    out, amp = np.zeros((h, w), np.float32), 1.0
    for _ in range(octaves):
        gh, gw = h // cell + 3, w // cell + 3
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        out += amp * zoom(g, (h / (gh - 2), w / (gw - 2)), order=3)[:h, :w]
        amp *= 0.5
        cell = max(2, cell // 2)
    return out / (np.abs(out).max() + 1e-6)


def matte_white(rgb, tol=18):
    """Near-white pixels connected to the border become background."""
    g = rgb.astype(np.float32)
    white = (g.min(axis=2) > 255 - tol * 2.2) & ((g.max(axis=2) - g.min(axis=2)) < tol)
    lab, _ = label(white)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, edge[edge > 0])
    fg = binary_fill_holes(~bg)
    lab2, n = label(fg)                                   # keep the largest island (+ big ones)
    if n > 1:
        sizes = np.bincount(lab2.ravel()); sizes[0] = 0
        fg = sizes[lab2] >= 0.02 * sizes.max()
    a = gaussian_filter(fg.astype(np.float32), 0.8)
    return np.clip((a - 0.5) * 2.5 + 0.5, 0, 1)


def matte_fal(path, ledger, tag):
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, "in.json")
        json.dump({"image_url": "@file:" + os.path.abspath(path)}, open(inp, "w"))
        cmd = [sys.executable, FAL, "run", "fal-ai/bria/background/remove", inp, "--out", d]
        if ledger: cmd += ["--ledger", ledger, "--tag", tag or "cutout"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        pngs = [f for f in os.listdir(d) if f.endswith(".png")]
        if not pngs: sys.exit("fal matte returned no png")
        im = Image.open(os.path.join(d, pngs[0])).convert("RGBA")
        return np.asarray(im)[..., 3].astype(np.float32) / 255


def matte_sam(path, prompt, ledger, tag):
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, "in.json")
        json.dump({"image_url": "@file:" + os.path.abspath(path), "prompt": prompt, "apply_mask": False}, open(inp, "w"))
        cmd = [sys.executable, FAL, "run", "fal-ai/sam-3/image", inp, "--out", d]
        if ledger: cmd += ["--ledger", ledger, "--tag", tag or "sam"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        pngs = [f for f in os.listdir(d) if f.endswith(".png")]
        if not pngs: sys.exit("sam returned no mask")
        return Image.open(os.path.join(d, pngs[0])).convert("L")


def grade(rgb, mode):
    if mode == "keep": return rgb.astype(np.float32)
    y = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32) / 255
    y = np.clip((y - 0.04) / 0.92, 0, 1) ** 1.05
    ink = np.array([28, 26, 24], np.float32) if mode == "bw" else np.array([52, 36, 24], np.float32)
    paper = np.array([239, 230, 214], np.float32) if mode == "bw" else np.array([236, 214, 178], np.float32)
    return ink + (paper - ink) * y[..., None]


def torn_mask(h, w, amp, rim, rng, rough):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    n1, n2 = noise(h, w, rng, 40), noise(h, w, rng, 12)
    jag = amp * (0.55 + 0.45 * n1 + 0.25 * rough * n2)
    outer = d > jag
    inner = d > jag + rim * (0.7 + 0.6 * np.abs(noise(h, w, rng, 18)))
    return gaussian_filter(outer.astype(np.float32), 0.7), gaussian_filter(inner.astype(np.float32), 0.6)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--matte", default="none")
    ap.add_argument("--mask"); ap.add_argument("--savemask")
    ap.add_argument("--shape", default="die", choices=["die", "torn", "cut"])
    ap.add_argument("--grade", default="keep", choices=["keep", "bw", "sepia"])
    ap.add_argument("--inset", type=float, default=0.0)
    ap.add_argument("--tear", type=float, default=16); ap.add_argument("--rim", type=float, default=9)
    ap.add_argument("--border", type=float, default=14); ap.add_argument("--rough", type=float, default=0.6)
    ap.add_argument("--max", type=int, default=1200); ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--notrim", action="store_true")
    ap.add_argument("--ledger"); ap.add_argument("--tag")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    im = Image.open(a.src)
    mask = Image.open(a.mask).convert("L") if a.mask else None
    if a.matte.startswith("sam:") and mask is None:
        mask = matte_sam(a.src, a.matte[4:], a.ledger, a.tag)
        if a.savemask: mask.save(a.savemask)
    if mask is not None: mask = mask.resize(im.size)
    if a.inset > 0:
        dx, dy = int(im.width * a.inset), int(im.height * a.inset)
        im = im.crop((dx, dy, im.width - dx, im.height - dy))
        if mask is not None: mask = mask.crop((dx, dy, mask.width - dx, mask.height - dy))
    s = min(1.0, a.max / max(im.size))
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        if mask is not None: mask = mask.resize(im.size, Image.LANCZOS)
    has_alpha = im.mode in ("RGBA", "LA")
    rgba = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb = rgba[..., :3]
    if mask is not None: alpha = gaussian_filter(np.asarray(mask).astype(np.float32) / 255, 0.7)
    elif has_alpha and a.matte == "none": alpha = rgba[..., 3] / 255
    elif a.matte == "white": alpha = matte_white(rgb)
    elif a.matte == "fal":
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        im.convert("RGB").save(tmp); alpha = matte_fal(tmp, a.ledger, a.tag); os.unlink(tmp)
    else: alpha = np.ones(rgb.shape[:2], np.float32)
    col = grade(rgb, a.grade)

    if a.shape == "torn":
        pad = int(a.tear)
        h, w = alpha.shape
        outer, inner = torn_mask(h, w, a.tear, a.rim, rng, a.rough)
        fib = 1 + 0.05 * noise(h, w, rng, 6)
        out = PAPER * fib[..., None] * (1 - inner[..., None]) + col * inner[..., None]
        A = outer
    else:
        pad = 0 if a.notrim else int(a.border * 1.6) + 4
        alpha = np.pad(alpha, pad); col = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        h, w = alpha.shape
        if a.shape == "die":
            dist = distance_transform_edt(alpha < 0.5)
            wob = a.border * (1 + 0.35 * a.rough * noise(h, w, rng, 30))
            border = gaussian_filter((dist <= wob).astype(np.float32), 0.8)
            fib = 1 + 0.04 * noise(h, w, rng, 6)
            out = PAPER * fib[..., None] * (1 - alpha[..., None]) + col * alpha[..., None]
            A = np.maximum(border, alpha)
        else:
            out, A = col, alpha
    ys, xs = np.where(A > 0.02)                            # trim to content
    y0, y1, x0, x1 = max(0, ys.min() - 2), ys.max() + 3, max(0, xs.min() - 2), xs.max() + 3
    if a.notrim: y0, y1, x0, x1 = 0, A.shape[0], 0, A.shape[1]
    res = np.dstack([np.clip(out, 0, 255), np.clip(A * 255, 0, 255)])[y0:y1, x0:x1].astype(np.uint8)
    Image.fromarray(res, "RGBA").save(a.out, optimize=True)
    print("wrote", a.out, res.shape[1], "x", res.shape[0])


if __name__ == "__main__":
    main()
