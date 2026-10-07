#!/usr/bin/env python3
"""sheet.py <dir_of_pngs> <out.jpg> [cols=4] [thumb_w=640] — labelled contact sheet (file stem as label)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
tw = int(sys.argv[4]) if len(sys.argv) > 4 else 640
names = sorted(n for n in os.listdir(d) if n.endswith('.png'))
first = Image.open(os.path.join(d, names[0])); th = round(tw * first.height / first.width)
rows = (len(names) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (24, 24, 24))
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../tools/libs/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf')
font = ImageFont.truetype(FONT, 20) if os.path.exists(FONT) else ImageFont.load_default()
draw = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(d, n)).convert('RGB').resize((tw, th), Image.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * th
    sheet.paste(im, (x, y))
    label = n[:-4]
    draw.rectangle([x, y + th - 28, x + 12 * len(label) + 12, y + th], fill=(0, 0, 0))
    draw.text((x + 6, y + th - 26), label, fill=(255, 255, 0), font=font)
sheet.save(out, quality=86)
print(out, sheet.size, len(names))
