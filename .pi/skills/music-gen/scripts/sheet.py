#!/usr/bin/env python3
"""sheet.py — labelled spectrogram contact sheet: sheet.py out.jpg a.mp3 b.wav ... (one row per file, 0-22 kHz, log power)."""
import sys, subprocess, tempfile, pathlib
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]; rows = []
with tempfile.TemporaryDirectory() as td:
    for i, f in enumerate(files):
        p = f"{td}/{i}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-lavfi", "showspectrumpic=s=900x180:legend=0:scale=log:fscale=lin:stop=22000", p], check=True)
        im = Image.open(p).convert("RGB"); d = ImageDraw.Draw(im); d.rectangle([0, 0, 330, 22], fill="black"); d.text((5, 5), pathlib.Path(f).parent.name + "/" + pathlib.Path(f).stem, fill="white"); rows.append(im)
W = max(r.width for r in rows); sh = Image.new("RGB", (W, sum(r.height for r in rows)), "black"); y = 0
for r in rows: sh.paste(r, (0, y)); y += r.height
sh.save(out, quality=85); print(out, sh.size)
