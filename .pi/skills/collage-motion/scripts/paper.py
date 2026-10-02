#!/usr/bin/env python3
"""paper.py — procedural paper textures for collage motion ($0, deterministic).

  $PY paper.py --kind bg    --size 1080x1920 --tone "#D8CAB3" --out assets/paper_bg.jpg
  $PY paper.py --kind sheet --size 1200x1600 --tone "#EAE0CD" --out assets/paper_sheet.jpg
  $PY paper.py --kind stock --size 1400x1400 --tone "#1D4F91" --out assets/paper_blue.jpg
  $PY paper.py --kind kraft --size 600x200   --tone "#C9A66B" --out assets/tape.png   (alpha ~0.8)
  $PY paper.py --kind ink   --size 1024x1024 --out assets/ink.png   (white mask with speckle holes,
                                                                     use as CSS mask-image on type)
Kinds: bg = aged backdrop (mottling, stains, vignette) · sheet = cleaner page stock with fibres ·
stock = dyed construction paper (tone = dye colour) · kraft = masking-tape strip, semi-opaque PNG ·
ink = letterpress speckle mask. --seed changes the pattern; same seed = same pixels.
Needs numpy, scipy, pillow (tools/env.sh $PY).
"""
import argparse
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def fbm(h, w, rng, octaves=5, base=256, gain=0.55):
    """Fractal value noise in [-1, 1] (bicubic-upsampled random grids)."""
    out = np.zeros((h, w), np.float32)
    amp, tot, cell = 1.0, 0.0, base
    for _ in range(octaves):
        gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        up = zoom(g, (h / (gh - 1) + 0.01, w / (gw - 1) + 0.01), order=3)[:h, :w]
        out += amp * up
        tot += amp
        amp *= gain
        cell = max(2, cell // 2)
    out /= tot
    return out / (np.abs(out).max() + 1e-6)


def fibres(h, w, rng, n, length=(8, 40), alpha=0.06):
    """Thin random strokes, the visible fibre of real paper."""
    f = np.zeros((h, w), np.float32)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, np.pi)
        L = rng.uniform(*length)
        t = np.linspace(0, L, int(L) + 1)
        xs = np.clip((x + t * np.cos(a) + np.sin(t * 0.3) * 1.5).astype(int), 0, w - 1)
        ys = np.clip((y + t * np.sin(a)).astype(int), 0, h - 1)
        f[ys, xs] += rng.choice([-1, 1]) * alpha
    return gaussian_filter(f, 0.6)


def make(kind, w, h, tone, seed):
    rng = np.random.default_rng(seed)
    if kind == "ink":
        n = fbm(h, w, rng, octaves=4, base=64)
        speck = gaussian_filter(rng.random((h, w)).astype(np.float32), 1.2)
        speck = (speck - speck.mean()) / (speck.std() + 1e-6)
        holes = (speck + 0.9 * n) > 2.1  # sparse holes, clustered where the noise is high
        a = np.where(holes, 0.0, 1.0).astype(np.float32)
        a = gaussian_filter(a, 0.7)
        a = np.clip((a - 0.25) * 1.6, 0, 1)
        rgba = np.dstack([np.full((h, w), 255, np.uint8)] * 3 + [(a * 255).astype(np.uint8)])
        return Image.fromarray(rgba, "RGBA")

    c = hex_rgb(tone)
    lum = np.zeros((h, w), np.float32)
    if kind in ("bg", "sheet"):
        lum += 0.030 * fbm(h, w, rng, 6, 512)            # broad unevenness
        lum += 0.018 * fbm(h, w, rng, 3, 16)             # tooth
        lum += fibres(h, w, rng, int(w * h / 900), alpha=0.05)
    if kind == "bg":
        stains = fbm(h, w, rng, 3, 384)
        lum -= 0.06 * np.clip(stains - 0.35, 0, 1) * 2.2  # tea-stain mottling
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        lum -= 0.08 * np.clip(r - 0.6, 0, 1) ** 1.5       # aged edges
    if kind == "stock":
        lum += 0.05 * fbm(h, w, rng, 5, 256)
        lum += 0.035 * fbm(h, w, rng, 2, 8)              # felt texture
        lum += fibres(h, w, rng, int(w * h / 500), alpha=0.09)
    if kind == "kraft":
        lum += 0.05 * fbm(h, w, rng, 4, 64)
        lum += 0.04 * np.sin(np.linspace(0, 60, w))[None, :] * fbm(h, w, rng, 2, 32)  # crepe ridges
    rgb = np.clip(c[None, None, :] * (1 + lum[..., None]), 0, 255).astype(np.uint8)
    if kind == "kraft":
        a = np.clip(0.78 + 0.08 * fbm(h, w, rng, 3, 32), 0, 1)
        return Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA")
    return Image.fromarray(rgb, "RGB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", required=True, choices=["bg", "sheet", "stock", "kraft", "ink"])
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--tone", default="#D8CAB3")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    w, h = map(int, a.size.lower().split("x"))
    im = make(a.kind, w, h, a.tone, a.seed)
    if a.out.lower().endswith((".jpg", ".jpeg")):
        im.convert("RGB").save(a.out, quality=90)
    else:
        im.save(a.out, optimize=True)
    print("wrote", a.out, im.size, im.mode)
