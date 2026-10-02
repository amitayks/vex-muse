---
name: style-bible
description: Design and lock a video's visual style so every generated and hand-painted frame reads as one world - choose a medium with a physical logic, a restricted palette and typographic system, write reusable prompt tokens that the available image/video models render well, and prove it with a test grid on the real models before any cast or plate is made. Use in phase 3 of a video project, whenever a look must be invented or matched, or when frames start drifting in style.
license: MIT
compatibility: fal-media skill (FAL_KEY) for test frames.
metadata:
  author: muse
  version: "1.3.0"
---

# style-bible — taste enforced on the machines

A style is a set of constraints the models can actually obey. I design it,
then I test it on the models, then I lock it.

## Diverge first (the originality gate)
Before opening the reference library, write **three directions derived from this song only** — its
world, era, lyric imagery, the artist's own visual history, the audience's culture — plus one wild
card from a medium or tradition the studio has never used. Each: medium, palette, type voice, motion
signature, transition device, motif, one sentence of why it belongs to *this* song.
Then attack them: (1) could this look belong to any other song? → not specific enough; (2) does it
share more than one trait with a recent library case (fingerprints in [[code-motion-showreels]],
[[claude-pop-case]]) or with the last project in `knowledge/projects/`? → rework; (3) **what's shipping
now**: `python3 .pi/skills/reference-mesh/scripts/whatships.py wall --cat motion,design --days 14`
— could this direction sit in that wall unnoticed, or does it use two traits from the current
fingerprint in [[whatships]]? → rework. Test pieces too. References enter
only now, as craft (timing, clarity), never as the look. Pick the most specific survivor; record the
rejected ones and why in `bible.md`.

## Decide (write `bible/bible.md`)
1. **Medium** with a physical logic (e.g. risograph-on-newsprint cel,
   gouache on toned paper, cut-paper collage, ink + watercolor, screenprint
   halftone, sticker/vinyl). The medium dictates texture, edges, mistakes and
   how light behaves. It must also be reproducible in the p5 overlay
   (paper, wash, ink, grain, boil) if the piece uses rotoscope.
2. **Palette**: 4–6 inks + paper, hex values, with a section arc (which
   color dominates which section). No pure black/white.
3. **Line & shape**: line weight range, outline or not, silhouette rules,
   level of detail (where the eye rests).
4. **Light**: flat / cel-shaded 2 tones / glow only from emissive objects.
5. **Type system**: display face + text face (licensed/open), treatments by
   section (see `knowledge/references/kinetic-typography.md`).
6. **Camera language**: lens feel, framing defaults, what moves.
7. **Must-not list** from `knowledge/references/anti-slop.md` + brief.
8. **Anchors**: 3–6 named, real craft traditions or works the style sits
   between (e.g. "90s Sailor Moon cel × Swiss poster × risograph zine").
   Named traditions steer models far better than adjectives.

## Code-drawn styles (HyperFrames / Remotion / SVG)
When the look is built in code, the bible is a design system, not prompt tokens: palette hex with
which field each chapter uses, a type system chosen for this song's voice (roles: statement / human /
label — faces picked fresh, not the showreel trio) with sizes per text mode, texture, frame chrome only
if the concept needs it, motion signature (eases, speeds, hold share,
transition rule), the motif. Test = 6 HyperFrames snapshots from a 1-bar sketch (hero type frame,
two chapter fields, a transformation midpoint, the frame chrome or its absence, the end card) read at full size and at
360 px, against [[code-motion-showreels]] and the anti-slop list. No image-model spend needed.

## Tokenize
Write `bible/tokens.md`: a fixed **style suffix** (medium, palette words,
line, light, texture, anchors) and a **negative/avoid clause**, both pasted
verbatim into every image and video prompt. Plus per-set and per-character
tokens later (`cast-and-sets`). Never paraphrase tokens between calls.

## Test on the real models (the gate)
- Generate a 6-frame grid: protagonist-less wide set, character medium,
  close-up face, crowd/dancers, an insert object, a hero-text composition
  frame (empty zone). Run on 2 image models (e.g. nano-banana-pro and
  gpt-image-2) with the same tokens; ~12 images, ≲$3.
- Read every frame against the bible and the anti-slop list. Keep the model
  that holds the medium; adjust tokens; re-run only failures.
- Animate 1 frame with Seedance image-to-video at draft (480p, 5 s) to see
  whether the medium survives motion (texture swimming, line boil, color
  shift). If it melts, simplify the medium for plates and move texture into
  the overlay.
- Save the winners as `bible/frames/*.png` — they become style references
  (@Image) for every later generation.

## Acceptance
The divergence record exists (3 + 1 directions, attacks, why the winner is specific to this song).
Code-drawn look: the design-system section is complete and the 6 snapshots pass. Generated look:
`bible.md` + `tokens.md` exist; 6 test frames on the chosen model read as
one world at thumbnail size and pass the anti-slop list; the motion test
survived or the bible records the fallback; spend logged.
