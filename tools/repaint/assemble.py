#!/usr/bin/env python3
"""Assemble painted chunks into one continuous take, with a smoothstep cross-fade at each seam.

Each chunk dir (from paint_chunks.py) has out.mp4 and meta.json: frames [a, b], pre, post, so out.mp4
covers global frames a-pre .. b+post. Where two chunks overlap, the frames blend with a smoothstep
ramp over the overlap. A seam listed in --cuts is a hard cut instead (for a seam behind a door that
blocks the view). Frames stream through numpy; the film is never held in memory.

Usage:
  assemble.py <out.mp4> <chunkdir> [<chunkdir> ...] [--first F] [--last L] [--size 1280x720]
              [--fps 24] [--crf 14] [--cuts 1969,2286]
Prints JSON with the frame range and the seams (overlap ranges) it blended.
"""
import json, os, shutil, subprocess, sys
import numpy as np

FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"


def reader(path, W, H):
    fs = W * H * 3
    p = subprocess.Popen([FF, "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-"],
                         stdout=subprocess.PIPE)
    last = None
    while True:
        b = p.stdout.read(fs)
        if len(b) < fs:
            break
        last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        yield last
    while True:  # a short file is padded with its last frame
        yield last


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    out = a[0]
    opt = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    vals = {a[i + 1] for i, x in enumerate(a[:-1]) if x.startswith("--")}
    dirs = [x for x in a[1:] if not x.startswith("--") and x not in vals and os.path.isdir(x)]
    W, H = (int(v) for v in opt("--size", "1280x720").lower().split("x"))
    fps = opt("--fps", 24); crf = opt("--crf", 14)
    cuts = [int(x) for x in opt("--cuts", "").split(",") if x.strip()]  # first frame of the next chunk
    chunks = []
    for d in dirs:
        m = json.load(open(os.path.join(d, "meta.json")))
        fa, fb = m["frames"]
        chunks.append({"dir": d, "s": fa - m["pre"], "e": fb + m["post"], "a": fa, "b": fb,
                       "gen": reader(os.path.join(d, "out.mp4"), W, H), "pos": fa - m["pre"]})
    if not chunks:
        sys.exit("no chunk dirs")
    chunks.sort(key=lambda c: c["a"])
    first = opt("--first", chunks[0]["a"]); last = opt("--last", chunks[-1]["b"])
    enc = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                            "-i", "-", "-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    seams = []
    for f in range(first, last + 1):
        act = []
        for c in chunks:
            if c["s"] <= f <= c["e"]:
                while c["pos"] < f:
                    next(c["gen"]); c["pos"] += 1
                fr = next(c["gen"]); c["pos"] += 1
                act.append((c, fr.astype(np.float32)))
        if not act:
            sys.exit(f"no chunk covers frame {f}")
        if len(act) == 1:
            img = act[0][1]
        else:
            (c0, f0), (c1, f1) = act[0], act[1]
            o0, o1 = c1["s"], c0["e"]  # the overlap range
            if c1["a"] in cuts:
                img = f0 if f < c1["a"] else f1
            else:
                u = (f - o0 + 0.5) / (o1 - o0 + 1); u = u * u * (3 - 2 * u)
                img = f0 * (1 - u) + f1 * u
            if f == o0:
                seams.append([int(o0), int(o1)])
        enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    print(json.dumps({"out": out, "first": first, "last": last, "frames": last - first + 1, "seams": seams}))


if __name__ == "__main__":
    main()
