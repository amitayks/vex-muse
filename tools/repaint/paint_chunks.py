#!/usr/bin/env python3
"""Paint one chunk of a long render with a video-edit model, with seam handles.

The render-repaint method (knowledge/references/render-repaint.md): a long Blender render is painted
in chunks, because one call takes at most 15 s. Separate calls re-dress the same people, so each
chunk is painted with H handle frames from each neighbour. The 2H frames at each seam are then
painted by both neighbours, and assemble.py cross-fades them.

For chunk k (frames a..b) the source sent to the model is [a-H .. b+H], built from the chunk files
in the plan. A neighbour gives handles only when it has the same "version" as chunk k: a draft
neighbour would put stale frames into the join, so a chunk waits for its next neighbour.

Usage:
  paint_chunks.py <plan.json> <k> [--take t1] [--handle 8] [--out-dir DIR] [--ledger L] [--no-post] [--dry]

plan.json (see plan.example.json):
  {"fps": 24, "size": [1280, 720], "model": "blackforestlabs/flux-3/edit-video", "usd_per_s": 0.03,
   "max_frames": 359, "look": "...", "keep": "...",
   "chunks": [{"frames": [1, 340], "src": "draft/c_0001-0340.mp4", "version": "v2",
               "prompt": "what is in this chunk", "text_keep": "optional: on-screen text to keep"}]}
  Chunk "src" files hold exactly the chunk's frames (a..b). Relative paths resolve against the plan.

Writes <out-dir>/c<k>_<take>/{src.mp4, in.json, meta.json, raw/, out.mp4}; out.mp4 has exactly the
source frame count at the plan size. Needs ffmpeg/ffprobe on PATH (or FFMPEG / FFPROBE) and the
fal-media skill (FAL_KEY). Every call is logged to the ledger, plus an estimate row.
"""
import glob, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FP = os.environ.get("FFPROBE") or shutil.which("ffprobe") or "ffprobe"
PY = os.environ.get("PY") or sys.executable
FAL = os.environ.get("FAL_PY") or f"{ROOT}/.pi/skills/fal-media/scripts/fal.py"


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def nframes(f):
    return int(sh([FP, "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", f]).stdout.strip())


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    plan_path = os.path.abspath(a[0]); k = int(a[1])
    opt = lambda key, d: type(d)(a[a.index(key) + 1]) if key in a else d
    plan = json.load(open(plan_path)); base = os.path.dirname(plan_path)
    chunks = plan["chunks"]
    if not 1 <= k <= len(chunks):
        sys.exit(f"chunk {k} out of range 1..{len(chunks)}")
    take = opt("--take", "t1"); H = opt("--handle", 8)
    fps = plan.get("fps", 24); W, Hh = plan.get("size", [1280, 720])
    model = plan.get("model", "blackforestlabs/flux-3/edit-video")
    out_dir = os.path.abspath(opt("--out-dir", os.path.join(base, "chunks")))
    ledger = os.path.abspath(opt("--ledger", os.path.join(base, "ledger.jsonl")))
    max_frames = plan.get("max_frames", 359)

    def src_of(j):  # 1-based
        f = chunks[j - 1].get("src")
        if not f:
            return None
        f = f if os.path.isabs(f) else os.path.join(base, f)
        return f if os.path.exists(f) else None

    ck = chunks[k - 1]; fa, fb = ck["frames"]; ver = ck.get("version")
    cur = src_of(k)
    if not cur:
        sys.exit(f"chunk {k}: source file missing ({ck.get('src')})")
    same = lambda j: src_of(j) and chunks[j - 1].get("version") == ver
    parts = []; pre = post = 0
    if k > 1 and same(k - 1):
        pa, pb = chunks[k - 2]["frames"]; n_prev = pb - pa + 1
        pre = H; parts.append((src_of(k - 1), n_prev - H, n_prev - 1))
    parts.append((cur, 0, fb - fa))
    if "--no-post" not in a and k < len(chunks) and same(k + 1):
        post = H; parts.append((src_of(k + 1), 0, H - 1))
    total = sum(e - s + 1 for _, s, e in parts)
    if total > max_frames:
        sys.exit(f"{total} frames > {max_frames} (the model's 15 s limit): split the chunk")

    out = os.path.join(out_dir, f"c{k:02d}_{take}"); os.makedirs(out, exist_ok=True)
    ins, fc = [], []
    for i, (f, s, e) in enumerate(parts):
        ins += ["-i", f]
        fc.append(f"[{i}:v]trim=start_frame={s}:end_frame={e + 1},setpts=PTS-STARTPTS,setsar=1,fps={fps}[v{i}]")
    fc.append("".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1[v]")
    src = os.path.join(out, "src.mp4")
    sh([FF, "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fc), "-map", "[v]",
        "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p", "-an", src])
    n = nframes(src)
    if n != total:
        sys.exit(f"source has {n} frames, expected {total}")
    if os.path.getsize(src) > 49e6:  # the model takes < 50 MB
        sh([FF, "-y", "-loglevel", "error", "-i", src, "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-an", src + ".tmp.mp4"])
        os.replace(src + ".tmp.mp4", src)

    prompt = " ".join(x for x in (plan.get("look", ""), ck.get("prompt", ""), ck.get("text_keep", ""), plan.get("keep", "")) if x)
    json.dump({"video_url": f"@file:{src}", "prompt": prompt}, open(os.path.join(out, "in.json"), "w"), indent=1)
    meta = {"chunk": k, "frames": [fa, fb], "pre": pre, "post": post, "src_frames": n, "take": take,
            "version": ver, "parts": parts, "model": model, "prompt": prompt}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    if "--dry" in a:
        print(json.dumps(meta)); return

    raw = os.path.join(out, "raw"); os.makedirs(raw, exist_ok=True)
    tag = f"paint:c{k:02d}:{take}"
    r = subprocess.run([PY, FAL, "run", model, os.path.join(out, "in.json"), "--out", raw, "--ledger", ledger, "--tag", tag],
                       capture_output=True, text=True)
    vids = sorted(glob.glob(os.path.join(raw, "*.mp4")), key=os.path.getmtime)
    if not vids:
        print(r.stdout[-800:], r.stderr[-800:]); sys.exit("no output")
    # The model returns its own size (Flux 3: 1248x704) and can be one frame off: scale back, pad, keep exactly n frames.
    sh([FF, "-y", "-loglevel", "error", "-i", vids[-1], "-vf", f"scale={W}:{Hh}:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop=4",
        "-frames:v", str(n), "-r", str(fps), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-an", os.path.join(out, "out.mp4")])
    meta["out_frames"] = nframes(os.path.join(out, "out.mp4")); meta["raw"] = vids[-1]
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    rate = plan.get("usd_per_s", 0.03)
    with open(ledger, "a") as f:
        f.write(json.dumps({"endpoint": "price-estimate", "tag": tag + ":est", "est_usd": round(n / fps * rate, 3),
                            "note": f"{n} frames x ${rate}/s"}) + "\n")
    print(json.dumps({"chunk": k, "src_frames": n, "out_frames": meta["out_frames"], "pre": pre, "post": post}))


if __name__ == "__main__":
    main()
