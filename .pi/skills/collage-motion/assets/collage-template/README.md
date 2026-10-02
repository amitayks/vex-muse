# collage-template — mechanics scaffold (HyperFrames 0.8.78, 1080×1920, 30 fps)

**Its content is the `projects/lab-collage` replica ("THE HOME STUDIO", 2 chapters + end card, 128 BPM,
18.3 s). Reuse the mechanics (`assets/js/collage.js`, the layer structure, the zoom-through carry, the
peel, the stepped build clock) — replace every image, word, colour, face and position.**

Structure of `index.src.html` (bottom → top): end card · ch2 inside `#peel2` · peel flap SVG · ch1 ·
`#carry` (object crossing the ch1→ch2 cut) · grain. Each chapter: `.zoom > .cam > bg, page, chrome,
headline, hero, date, stickers, caption band, progress, corner notes`.

Start a composition:
```bash
P=projects/<slug>/motion/<comp>; S=.pi/skills/collage-motion
mkdir -p $P/assets/{fonts,js} ${P}-src
cp $S/assets/collage-template/hyperframes.json $P/
cp $S/assets/collage-template/assets/js/{gsap.min.js,collage.js} $P/assets/js/
cp .pi/skills/code-motion/assets/reel-template/assets/grain.png $P/assets/
cp studio/assets/fonts/{Anton.ttf,IBMPlexMono-Medium.ttf,InstrumentSerif-Regular.ttf} $P/assets/fonts/   # or the bible's faces
cp $S/assets/collage-template/index.src.html ${P}-src/
ln -sfn ../../lab-motion-tools/node_modules projects/<slug>/node_modules      # adjust depth
# paper (tones from the bible), then the cutouts (skill §3):
$PY $S/scripts/paper.py --kind bg    --size 1080x1920 --tone "<paper>"  --out $P/assets/paper_bg.jpg
$PY $S/scripts/paper.py --kind sheet --size 1040x1600 --tone "<page>"   --out $P/assets/paper_sheet.jpg
$PY $S/scripts/paper.py --kind stock --size 1300x1300 --tone "<accent>" --out $P/assets/paper_blue.jpg
$PY $S/scripts/paper.py --kind stock --size 800x300   --tone "<label>"  --out $P/assets/paper_label.jpg
$PY $S/scripts/paper.py --kind kraft --size 400x110   --tone "<tape>"   --out $P/assets/tape.png
$PY $S/scripts/paper.py --kind ink   --size 1024x1024                   --out $P/assets/ink.png
# edit ${P}-src/index.src.html (images, copy, timings on the song grid, bed), then:
python3 .pi/skills/code-motion/scripts/hf_build.py ${P}-src/index.src.html $P
```
The lab's image files (`bedroom.png`, `bedroom_teen.png`, `cassette.png`, `hand.png`, `boombox.png`) and
`bed.wav` live in `projects/lab-collage/motion/collage/assets/` — the template names them; your
project supplies its own. Render: `npx hyperframes render $P --quality draft --fps 30 --workers 2`.
