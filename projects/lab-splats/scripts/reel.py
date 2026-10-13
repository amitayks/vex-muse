#!/usr/bin/env python3
"""reel.py - cut the lab-splats proof reel: clips in order, a two-line label per chapter (fades in/out), hard cuts,
light grain + vignette, 1920x1080 30 fps, optional music bed.

  $PY reel.py reel.json out.mp4
reel.json: {"clips":[{"file":"renders/r1_lane.mp4","t0":0,"t1":6,"k":"GENERATE","l":"World Labs Marble · 2M splats"}], "music": "x.mp3"}
"""
import json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FONT = os.path.join(ROOT, "studio/assets/fonts/IBMPlexMono-Medium.ttf")

def label(k, l, path, W=1920, H=1080):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, 26); f2 = ImageFont.truetype(FONT, 22)
    x, y = 64, H - 132
    d.rectangle([x - 18, y - 16, x + 12 + max(d.textlength(k, font=f1), d.textlength(l, font=f2)) + 18, y + 72], fill=(0, 0, 0, 120))
    d.text((x, y), k, font=f1, fill=(255, 196, 120, 255)); d.text((x, y + 38), l, font=f2, fill=(235, 235, 235, 255))
    im.save(path)

def main():
    R = json.load(open(sys.argv[1])); out = sys.argv[2]; tmp = tempfile.mkdtemp(prefix="reel_")
    parts = []
    for i, c in enumerate(R["clips"]):
        png = f"{tmp}/l{i}.png"; label(c.get("k", ""), c.get("l", ""), png)
        d = c["t1"] - c["t0"]; p = f"{tmp}/p{i:02d}.mp4"
        vf = (f"[0:v]trim={c['t0']}:{c['t1']},setpts=PTS-STARTPTS,scale=1920:1080,fps=30,format=yuv420p[v];"
              f"[1:v]format=rgba,fade=t=in:st=0.4:d=0.4:alpha=1,fade=t=out:st={max(d - 0.8, 0.5)}:d=0.4:alpha=1[l];"
              f"[v][l]overlay=0:0:shortest=1,noise=alls=2:allf=t,vignette=PI/6[o]")
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", c["file"], "-loop", "1", "-t", str(d), "-i", png,
                        "-filter_complex", vf, "-map", "[o]", "-t", str(d), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-r", "30", p], check=True)
        parts.append(p)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = f"{tmp}/silent.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    if R.get("music"):
        dur = sum(c["t1"] - c["t0"] for c in R["clips"])
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", silent, "-i", R["music"], "-filter_complex",
                        f"[1:a]atrim=0:{dur},afade=t=in:st=0:d=0.5,afade=t=out:st={dur - 2}:d=2,loudnorm=I=-14:TP=-1.5[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", out], check=True)
    else:
        os.replace(silent, out)
    print(json.dumps({"out": out, "clips": len(parts)}))

if __name__ == "__main__":
    main()
