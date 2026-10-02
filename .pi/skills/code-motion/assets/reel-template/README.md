# reel-template — mechanics scaffold (HyperFrames 0.8.78)

**Its look is a study replica of the Sep 2026 Opus showreel trend. Reuse the code (beat helper, proxy
tween, iris, masks, morph, landing, font build) — replace every colour, face, motif and line of copy.**

128 BPM, 4 bars + tail (8.1 s): A dot mitosis → B iris + EVERY [FRAME] on purpose. → C MorphSVG gizmo
chain → D dot drops in as the full stop of the wordmark. HUD (bar pips, TC, chapter), grain, fonts.

Start a composition:
```bash
P=projects/<slug>/motion/<comp>; mkdir -p $P/assets/fonts ${P}-src
cp -r .pi/skills/code-motion/assets/reel-template/{hyperframes.json,assets} $P/
cp studio/assets/fonts/{ArchivoBlack-Regular.ttf,InstrumentSerif-Italic.ttf,IBMPlexMono-Medium.ttf} $P/assets/fonts/
cp .pi/skills/code-motion/assets/reel-template/index.src.html ${P}-src/
# edit ${P}-src/index.src.html, add assets/<song>.wav, then:
python3 .pi/skills/code-motion/scripts/hf_build.py ${P}-src/index.src.html $P
```
Audio in the template points at `assets/beat128.wav` (a synthetic test beat) — replace with the song slice.
