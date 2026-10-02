---
name: p5-paper-engine
description: Paint and animate hand-made-looking 2D frames in JavaScript with Muse's studio (fork of ClaudeAnimationBase - p5.js + p5.brush watercolor, ink, boil, paper, glow, acted characters, camera, wipes/irises) - project page setup, chapter files, pure-function-of-time shots, the look-at-it review loop (sheets, strips, crops) and headless rendering. Use in phase 7 of a video project, for any painted/animated shot, overlay, title card, loop or GIF, and when extending the engine.
license: MIT
compatibility: tools/env.sh (Chrome headless shell + libs, ffmpeg); studio/ with node_modules (bootstrap installs).
metadata:
  author: muse
  version: "1.1.0"
---

# p5-paper-engine — the brush is mine

When to paint (vs `code-motion`): the read is a hand-made world, an acted character or a story
told in drawings (reference: shfred0's "Claude animates its own life" — two-tone ink, 8 fps boil,
the mark as protagonist, tiny handwritten captions; [[code-motion-showreels]]). Graphic type, UI,
HUD and shape morphs are faster and crisper in HyperFrames; painted frames can be layered into a
HyperFrames composite as PNG sequence / alpha video.

Engine API and animation law: read `studio/ANIMATION_GUIDE.md` in full before
painting (upstream, authoritative: medium, reads, principles, API). Fork
changes: `studio/FORK.md`. This skill adds the project layout, the lyric/
music-video exceptions, and how to render on this box.

## Project layout (inside studio/)
- `projects/<slug>.html` — copy of `studio.html` loading core/clawd/timeline
  + the project's files; point `--page=` at it.
- `projects/<slug>/config.js` — `PROJECT = {duration, bpm, offset, audio}`
  from song.json (bpm verified, offset = first downbeat).
- `projects/<slug>/cast.js` — the project's characters (shared, director
  edits only). `projects/<slug>/ch/NN_<section>.js` — one file per chapter,
  `chapter(name, start, end, [[t0, shotFn], …])` as in vendor/PDoomVideo.
- `projects/<slug>/timing.js` — generated from song.json + shots.json
  (words, beats, shots) so code never retypes times.

## Laws (on top of the guide)
- Frames are pure functions of t. `hash()` for stable randomness,
  `boilSeed(key)` per element, no Math.random, no state.
- **Text is allowed and designed** in music videos — through `kinetic-lyrics`,
  never ad-hoc `letter()` calls in shots. The guide's "no text" rule still
  applies to signs/captions that repeat the picture.
- Characters on model: the painted cast is traced from the approved sheets
  (proportions, palette, silhouette) — not the kit's Clawd unless the brief
  wants Clawd.
- Build shot by shot: block key poses as stills, check, then motion.

## Review loop (every shot, every change)
Run from `studio/` after `source ../tools/env.sh`; always `--soft-gl` here.
- `node render.mjs --page=projects/<slug>.html --soft-gl --sheet=<t,...> --cols=4 --w=480 --out=out/check/<id>.jpg`
- motion: `--strip=a:b --cols=6 --w=320`; details: `--crop=x,y,w,h`; follow a
  world point: `--crop-at=x,y,w,h`.
Read every image. Check read, timing (count frames per read), motion
(anticipation/follow-through/no twinning), boil stability, contacts,
transitions, text legibility at 360 px width, color.
- After a crashed/killed render: `../tools/killchrome.sh` (no pkill on this
  box; orphaned Chrome eats the 2 CPUs). It kills EVERY headless Chrome —
  never run it while another render is in flight.

## Performance budget (measured on this box: 2 CPU, SwiftShader)
Software WebGL is slow. Keep per-frame cost low: fewer watercolor `fill`
shapes (cache static backgrounds by drawing them once into a
`createGraphics` keyed by boil frame), `onTwos(t)` for hand-drawn 12 fps
animation, and review at `--w=480`. Final full-length renders go through
`render-review` (Modal GPU, ~0.3 s/frame), not this box.

## Acceptance
Each shot: a reviewed sheet + strip for its key motion and every
transition, no page errors in the log, ms/frame within the render budget,
text legible at phone size.
