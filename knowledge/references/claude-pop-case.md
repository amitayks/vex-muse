---
kind: video
tags: [case-study, claude, p5-brush, seedance, rotoscope, lyrics, method]
audience: SF tech X
half_life: 365
rights: safe
seen: 2026-09-26
---
# Case: "Claude Pop" (donald, Sep 2026) + JohnHeibel's PDoom / ClaudeAnimationBase

Sources: x.com/donaldjewkes/status/2102801274173587569 (1.7M views; "one
prompt, Claude worked 12 hours"), github.com/JohnHeibel/PDoomVideo (the
"I'm Upping My P(doom)" video, all code model-written),
github.com/JohnHeibel/ClaudeAnimationBase (the distilled kit). Both repos
are vendored pinned in `vendor/` (see `vendor/PINS.md`). A local copy of the
original video (mp4, audio, frame sheets) with a quoting post is in
[[references/media/claude-pop-original/post|media/claude-pop-original]].

## What the donald prompt actually specified (the method, not the style)
1. Feel the lyrics deeply; free to abandon the reference's style.
2. Know your capabilities; plan within them.
3. Use the reference compendium + a zeitgeist audit (timeline events, memes,
   the words around them) + internet-brutalism raw inserts, anchored to
   references the audience understands.
4. A style bible designed to work with the available image models; anti-
   Pixar, anti-"GPT slop"; K-pop as an anchor, not a cage; Twitter-native.
5. A protagonist personifying the brand/voice (Claude's sunflower-esque
   mark → a pop idol matching the feminine vocal), backup dancers, supporting
   cast, designed sets.
6. Seedance 2.5 generations with the images inserted, **the song cut up and
   passed as audio reference per shot** so timing and lip-sync are exact,
   with verification loops, re-running as needed.
7. Then reconstruct everything as a JS painted overlay (rotoscope: shoot,
   then draw over) so only the drawing is seen; the plates are scaffolding.
8. Lyrics as motion graphics composed into the shots, varying hero vs
   subtitle; heavy text at the hook.
9. Rigor in composition and timing planning so it coheres; revisit and
   re-iterate; watch the full video repeatedly with screenshots.
10. Spend aggressively but economically.
→ All ten are now standing method in skills (`mv-director` routes them).

## What the PDoom repo teaches (good)
- Frames as pure functions of time → parallel, out-of-order, resumable
  rendering; `hash()` for stable randomness, 12 fps reseeded boil.
- A storyboard with a reads table; chapters as files; subagents briefed by
  a written guide (`ANIMATION_GUIDE.md`) and restricted to their own file.
- Review loop by contact sheets, frame strips and crops — the model
  checks its own motion.
- Medium discipline: p5.brush wash + ink + watercolor fills, paper and
  grain, `glow()` for light instead of muddy pigment.

## Where it falls short (what we beat)
- Timing: many shots 1.4–2 s with 2–3 reads each — the guide itself admits
  models pile reads. Our storyboard gates on read time.
- A literal gag per lyric line (an illustrated glossary) instead of a world
  with an arc; generic "stage show" frame.
- Karaoke bar as the only text — no hero typography, no composition for
  text.
- Characters are simple primitives (Clawd block); no real performance, no
  lip-sync, no dance quality — this is exactly what plates + rotoscope add.
- Tempo claimed 88 BPM in the guide; our detector hears ~130 (3:2). Verify,
  don't inherit.

## ClaudeAnimationBase kit (our `studio/` fork base)
The better engine: `paint()/inkLine()`, `boilSeed()`, 31 acted emotions with
`emotions()` transitions, drawn key-view turns, `jump/take/stroll/spring`,
camera, `brushWipe/iris/flash`, render modes `--sheet/--strip/--crop/--crop-at/--stills/--clip/--frames`.
Fork changes so far: offline fonts (no network wait), `--page=` to render any
studio page, no GPU rasterization under `--soft-gl`, longer ready timeout.
