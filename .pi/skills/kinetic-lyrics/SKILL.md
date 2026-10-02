---
name: kinetic-lyrics
description: Design and animate lyric typography as motion graphics inside a music video - choose hero / integrated / subtitle / none per line, set words on their sung onsets from song.json, compose text into the zones the storyboard reserved, evolve one type system across sections, and build it in HyperFrames DOM type (default), a Remotion alpha layer or painted p5 type, with legibility checks at phone size. Use whenever lyrics, titles, captions, on-screen words or text-driven hooks appear in a video.
license: MIT
compatibility: HyperFrames (code-motion) or studio/ (p5-paper-engine), song.json (song-map), shots.json (storyboard).
metadata:
  author: muse
  version: "1.2.0"
---

# kinetic-lyrics — words that hold the scroll

Principles and vocabulary: `knowledge/references/kinetic-typography.md`.
Timing source: `song.json.words[]` via `shots.json text.words` — never retype
times or words.

## Build
1. **Type system** from the bible: display face + text face, sizes for each
   mode, colors (fill, stroke/shadow that survives any plate), treatment per
   section. Fonts go into `studio/assets/fonts/` (woff2, inlined like the
   fork does — no network at render).
2. **Engine** — pick per piece ([[tool-selection]]): **HyperFrames DOM type** (default: real
   kerning, masks, per-letter GSAP, over any footage/graphics; recipes in
   `code-motion/references/recipes.md`), a **Remotion alpha layer** when the lyric layer must be
   regenerated from data for several aspect ratios, or **painted p5 type** when the words must
   belong to a hand-made medium. Vocabulary from the showreels: mask rise, arc-in with rotation,
   motion-blur drop, bracket/selection frame, echo stack, word wallpaper, text → dots, typewriter
   with block cursor; faces and treatments come from the bible's type system (not the showreel trio).
   Fonts are registered from bytes (`FontFace(ArrayBuffer)`) — URL font loads fail on this box.
   For painted type: one shared `lyrics.js` per project in the studio exposing
   `lyricLayer(t)` called after each shot paints (and before grain), driven
   entirely by shots.json + song.json:
   - hero: word groups laid out in the zone, each word enters on its t0 with
     the section's entrance (slam / type-on / split / smear), emphasis words
     scale-hit on the nearest beat, exit on the shot's cut or line end +
     hold;
   - integrated: drawn by the shot itself in world space (wall, screen,
     sign) using the same faces;
   - subtitle: one consistent strip, karaoke-lit per word by onset.
   Text is painted like everything else (letter shadow, slight boil via
   `boilSeed`, paper grain over it) so it belongs to the medium.
3. **Hook**: the first line is hero, large, on screen by frame 1 or on the
   first sung onset, whichever comes first.

## Checks (per shot, in the review sheets)
- Onset: the word is visible ≤1 frame before its t0 (strip around 3 onsets).
- Legibility: downscale the frame to 360 px wide — every word readable; over
  footage the zone behind the words is calm and contrasting (scrim if not).
- A phrase never outgrows its zone: a new phrase clears the last one.
- Zone: no overlap with the protagonist's face or the shot's event.
- Consistency: same mode looks the same everywhere; treatments change only
  at section boundaries.
- Spelling: text rendered = lyrics.txt (diff the list of drawn words).

## Acceptance
Every lyric word in the song appears in its planned mode or is deliberately
`none` per shots.json; onset, legibility, zone and spelling checks pass on
the review sheets; the hook line is hero within the first 2 s.
