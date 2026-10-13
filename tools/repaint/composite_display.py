#!/usr/bin/env python3
"""Put story text from the base render back over the painted frames, through a frame-exact matte.

A video paint model invents on-screen numbers and text (a lift's floor display ran backwards). The fix
(knowledge/references/render-repaint.md): render a matte pass from the same Blender camera (every
light and emission off, all shaders black, the display pure emission), then
    out = painted * (1 - m) + base * m,   m = feathered matte (0..1).
The base pixels get a light grain so they sit in the painted frame.

All three inputs must be frame-aligned over the same range (concatenate chunk files first, for
example with assemble.py --cuts on every seam, or ffmpeg concat).

Usage:
  composite_display.py --painted P.mp4 --base B.mp4 --matte M.mp4 --out OUT.mp4
                       [--size 1280x720] [--fps 24] [--feather 1.5] [--grain 2.0] [--threshold 8] [--crf 14]
"""
import argparse, json, os, shutil, subprocess
import numpy as np
from scipy.ndimage import gaussian_filter

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"


def reader(path, W, H, gray=False):
    ch = 1 if gray else 3
    p = subprocess.Popen([FF, "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray" if gray else "rgb24",
                          "-s", f"{W}x{H}", "-"], stdout=subprocess.PIPE)
    n = W * H * ch
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            return
        x = np.frombuffer(b, np.uint8)
        yield x.reshape(H, W) if gray else x.reshape(H, W, 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--painted", required=True); ap.add_argument("--base", required=True)
    ap.add_argument("--matte", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1280x720"); ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--feather", type=float, default=1.5); ap.add_argument("--grain", type=float, default=2.0)
    ap.add_argument("--threshold", type=int, default=8, help="skip frames whose matte max is at or under this (0-255)")
    ap.add_argument("--crf", type=int, default=14); ap.add_argument("--seed", type=int, default=3)
    o = ap.parse_args()
    W, H = (int(v) for v in o.size.lower().split("x"))
    rng = np.random.default_rng(o.seed)
    enc = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(o.fps),
                            "-i", "-", "-c:v", "libx264", "-crf", str(o.crf), "-pix_fmt", "yuv420p", o.out], stdin=subprocess.PIPE)
    frames = used = 0
    for p, b, m in zip(reader(o.painted, W, H), reader(o.base, W, H), reader(o.matte, W, H, gray=True)):
        p = p.astype(np.float32); frames += 1
        if m.max() > o.threshold:
            mm = gaussian_filter(m.astype(np.float32) / 255.0, o.feather)[..., None]
            bb = b.astype(np.float32) + rng.normal(0, o.grain, b.shape).astype(np.float32)
            p = p * (1 - mm) + bb * mm; used += 1
        enc.stdin.write(np.clip(p, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    print(json.dumps({"out": o.out, "frames": frames, "frames_with_matte": used}))


if __name__ == "__main__":
    main()
