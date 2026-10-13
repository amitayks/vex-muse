#!/usr/bin/env python3
"""LTX 2.3 render-to-real paint pass for one shot: Blender clip -> photoreal first-frame anchor -> render-to-real.

Route (knowledge/references/render-repaint.md, "LTX 2.3 render-to-real paint pass"):
  - render-to-real alone turns people and objects real, but keeps CG landscapes CG;
  - with a photoreal first frame as image_url (a Nano Banana Pro "strict repaint" of the render's
    first frame) the landscape goes real and the Blender motion stays;
  - the anchor prompt must say "strict repaint", or the model re-composes the frame;
  - never use intensity "light" (it burned fake watermark text into a take); use "strong-v2";
  - a big fast mover against empty sky freezes with an anchor: use --no-anchor for it;
  - describe only what is in the frame (a full vehicle description paints a second vehicle);
  - the anchor frame must belong to the shot: trim handles that show another shot (--trim).

Usage:
  ltx_paint.py <clip.mp4> <outdir> --desc "what is in this shot" [--look "..."] [--avoid "..."] [--neg "..."]
               [--seed 92] [--take t1] [--trim first:last] [--no-anchor] [--ledger L] [--fps 24]
  Or put the texts in a JSON file: --prompt-file p.json with keys desc, look, avoid, neg.

Output: <outdir>/<take>_painted.mp4 at 1280x720 with the clip's own frame count. The model wants
8k+1 frames, so the source is padded and the result trimmed. Billing: $0.0024075 per output video
megapixel (about $0.08 for 41 frames at 720p); the anchor edit is about $0.15.
"""
import argparse, json, math, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FP = os.environ.get("FFPROBE") or shutil.which("ffprobe") or "ffprobe"
PY = os.environ.get("PY") or sys.executable
FAL = os.environ.get("FAL_PY") or f"{ROOT}/.pi/skills/fal-media/scripts/fal.py"

STRICT = ("Repaint this exact frame as a real photograph. This is a strict repaint, not a new picture: "
          "do not zoom, do not crop, do not move the camera, do not add or remove large shapes. "
          "Every shape stays in the same pixel position; only the surfaces, light and texture change. ")
LOOK = "Cinematic film still shot on 35mm colour negative film, fine natural grain, soft highlight roll-off. "
AVOID = ("No CGI or video-game look, no 3D render, no plastic, no lens flare, no god rays, no teal-and-orange grade, "
         "no text, no letters, no numbers, no logos, no watermark.")
NEG = "CGI, video game, 3D render, cartoon, plastic, glossy skin, lens flare, god rays, teal and orange, text, letters, numbers, watermark, logo, blurry, low quality"


def sh(*a):
    return subprocess.run(list(a), check=True, capture_output=True, text=True).stdout


def nframes(f):
    return int(sh(FP, "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", f).strip())


def run(endpoint, inp, out, tag, ledger):
    os.makedirs(out, exist_ok=True)
    jp = os.path.join(out, "input.json")
    json.dump(inp, open(jp, "w"))
    sh(PY, FAL, "run", endpoint, jp, "--out", out, "--ledger", ledger, "--tag", tag)
    files = [os.path.join(out, x) for x in os.listdir(out) if x.endswith((".png", ".jpg", ".mp4"))]
    if not files:
        sys.exit(f"{endpoint}: no output in {out}")
    return sorted(files, key=os.path.getmtime)[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip"); ap.add_argument("outdir")
    ap.add_argument("--desc", default=""); ap.add_argument("--look", default=LOOK)
    ap.add_argument("--avoid", default=AVOID); ap.add_argument("--neg", default=NEG)
    ap.add_argument("--prompt-file"); ap.add_argument("--seed", type=int, default=92)
    ap.add_argument("--take", default="t1"); ap.add_argument("--trim", help="first:last clip frames, inclusive")
    ap.add_argument("--no-anchor", action="store_true"); ap.add_argument("--ledger")
    ap.add_argument("--fps", type=int, default=24)
    o = ap.parse_args()
    if o.prompt_file:
        pf = json.load(open(o.prompt_file))
        for k in ("desc", "look", "avoid", "neg"):
            if k in pf:
                setattr(o, k, pf[k])
    if not o.desc:
        sys.exit("--desc (or desc in --prompt-file) is required: say only what is in the frame")
    clip, outdir = os.path.abspath(o.clip), os.path.abspath(o.outdir)
    os.makedirs(outdir, exist_ok=True)
    ledger = os.path.abspath(o.ledger or os.path.join(outdir, "ledger.jsonl"))
    if o.trim:
        t0, t1 = (int(x) for x in o.trim.split(":"))
        cut = os.path.join(outdir, f"trim_{o.take}.mp4")
        sh(FF, "-y", "-v", "error", "-i", clip, "-vf", f"select='between(n\\,{t0}\\,{t1})',setpts=N/{o.fps}/TB", "-r", str(o.fps),
           "-an", "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", cut)
        clip = cut
    n = nframes(clip)
    n8 = 8 * math.ceil((n - 1) / 8) + 1  # the model wants 8k+1 frames
    src = os.path.join(outdir, f"src_{o.take}.mp4")
    sh(FF, "-y", "-v", "error", "-i", clip, "-vf", f"scale=1280:720:flags=lanczos,tpad=stop_mode=clone:stop={n8 - n}",
       "-frames:v", str(n8), "-an", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", src)
    anchor = None
    if not o.no_anchor:
        f0 = os.path.join(outdir, f"f0_{o.take}.png")
        sh(FF, "-y", "-v", "error", "-i", src, "-frames:v", "1", f0)
        edit = run("fal-ai/nano-banana-pro/edit", {
            "image_urls": [f"@file:{f0}"], "aspect_ratio": "16:9", "resolution": "2K", "output_format": "png", "seed": o.seed,
            "prompt": STRICT + o.look + " " + o.desc + " Photoreal, practical, real. " + o.avoid},
            os.path.join(outdir, f"anchor_{o.take}"), f"repaint:anchor:{o.take}", ledger)
        anchor = os.path.join(outdir, f"anchor720_{o.take}.png")
        sh(FF, "-y", "-v", "error", "-i", edit, "-vf", "scale=1280:720:flags=lanczos", anchor)
    vid = run("fal-ai/ltx-2.3-quality/render-to-real", {
        "video_url": f"@file:{src}", **({"image_url": f"@file:{anchor}"} if anchor else {}),
        "prompt": "3DREAL. " + o.look + " " + o.desc, "negative_prompt": o.neg, "resolution": "720p",
        "intensity": "strong-v2", "num_frames": n8, "frames_per_second": o.fps, "generate_audio": False, "seed": o.seed},
        os.path.join(outdir, f"r2r_{o.take}"), f"repaint:r2r:{o.take}", ledger)
    final = os.path.join(outdir, f"{o.take}_painted.mp4")
    # 1280x720 in comes back as 1152x704 (resized, not cropped): scale back and keep the clip's frame count
    sh(FF, "-y", "-v", "error", "-i", vid, "-vf", "scale=1280:720:flags=lanczos,setsar=1", "-frames:v", str(n),
       "-an", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(o.fps), final)
    print(json.dumps({"take": o.take, "frames": n, "anchor": anchor, "painted": final}))


if __name__ == "__main__":
    main()
