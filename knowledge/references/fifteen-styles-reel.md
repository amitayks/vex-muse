---
kind: video
tags: [case-study, code-animation, showreel, opus-5.5, style-catalogue, brand-spots, transitions, packaging]
audience: AI Twitter (Chinese-language AI creators and their followers)
half_life: 180
rights: safe
seen: 2026-10-01
summary: Vincent Wei's 3-min "15 commercial-grade styles, all Opus 5.5 code" reel (Sep 29 2026), frame-studied — measured timing, its structure (each style is a 10 s spot for a made-up brand, joined by token bridges), the style/tool table, its weak spots, the one engine gap it exposes for Muse (Blender Cycles), and the chip-war lyric-video skill lead from its replies.
---
# Case: Vincent Wei's "15 styles in code" reel (Sep 29 2026)

Source: @VincentWei93, x.com/VincentWei93/status/2104957548797604116 (112k views on day 2). The author
is an AWS AI applied scientist who made the video-shotcraft, talkcraft and anything2explainer repos
(10k+ GitHub stars). The post says the picture, music and SFX were all written as code by Opus 5.5,
and he promises to publish each style's prompt later. That prompt set is a lead worth fetching when
it lands. Sent by the principal 2026-09-30. Muse studied it on 2026-10-01 with `xfetch` + `framestudy`, but
the frames and panel crops were **not** kept in the library because bash was denied mid-task. Refetch
with `xfetch.py` if the evidence is needed.

It belongs to the same wave as [[code-motion-showreels]]: no video model, every frame is code. This one
is a style **catalogue**, not a 15 s showreel.

## Measured
- 179 s, 1920×1080, 30 fps, 71.6 MB.
- **Grid:** 120 BPM; the Bauhaus chapter prints the BPM. One bar is 2 s.
- **Structure:**
  - a ~4.6 s cold open;
  - fifteen 10 s spots (5 bars each), joined by ~1.3 s bridges, for a ~11.3 s cycle per chapter;
  - an ~8 s recap and end card.
- **Holds:** 38 % of frames are held still, against our bar of 20–40 %.
- **Cuts:** `framestudy` found 120 "shots" averaging 1.49 s. Many of those are events inside a card,
  not real cuts. Only 40 of 119 cuts land on a beat (34 %).
- **Sound:** each chapter has its own cue in its style (a marimba under the isometric city). The mix
  is mostly quiet and ambient; the synthwave chapter is densest.

## Why it reads as "commercial-grade": the packaging, not the styles
- **Every style is a 10 s ad for a made-up brand that ends on its wordmark**: popwise, soft.,
  morphe., drop., NEON DRIVE, PIXEL QUEST and others.
  - Each spot has exactly **one event**: a match lights, a city grows, a drop splashes into the
    wordmark.
  - Ending on a product makes a technique demo read as a finished ad.
- **Token bridges between chapters.** The outgoing card collapses into a small token made of its own
  material (e.g. a gold arch logo shrinks to a ring, then a bead). The token turns into the next
  style's material and pops open into the next card. This is "transitions made of objects" (see
  [[code-motion-showreels]]) used as a catalogue's connective tissue.
- **Gallery frame.** A persistent inset 16:9 stage floats on an ambient blur sampled from the card
  itself. Beside it sits a side panel, alternating left and right per chapter, with:
  - the index number, a CJK hero title and an English subtitle in tracked caps;
  - a one-line description;
  - **tool chips** (how it was made) and the brand name;
  - progress ticks.

  The tool chips are an honest meta layer that sells the "all in code" claim.
- **Ending that rhymes.** All 15 tiles assemble into a 3×5 recap wall, then the end card: "Opus 5.5 —
  one model, fifteen styles, all rendered in code."

## The 15 chapters (style → technique named on the panel)
| # | Style | Technique / tool |
|---|---|---|
| 01 | hand-drawn frame-by-frame, on twos | Canvas brushwork |
| 02 | isometric 2.5D city build | Three.js, orthographic camera |
| 03 | flat vector brand story | SVG + GSAP |
| 04 | line-art stroke logo reveal | path-stroke draw |
| 05 | 3D balloon letters / capsule tiling | **Blender Cycles + Python physics** |
| 06 | shape morph (ink drop → coffee cup) | shape interpolation |
| 07 | sticker explainer, phone taken apart | exploded-view / wireframe |
| 08 | cyberpunk HUD target lock | Three.js + bloom |
| 09 | collage cut-out, stuttered frame rate, halftone | stop-motion cut-out frames |
| 10 | frosted / aurora glass, an AI-assistant launch | WebGL glass shader |
| 11 | Bauhaus grid poster on the beat | BPM-locked grid |
| 12 | synthwave | VHS post-process |
| 13 | pixel art, a day's light | palette-cycled pixel canvas |
| 14 | liquid soda "drop" launch | SDF metaballs |
| 15 | vertical variety-show caption diary | spring DOM/SVG, 9:16 frame |

The chip-to-chapter pairing for 07 and 08 comes from cropped side panels, and 07 is the least certain.

## Weak spots (what to beat)
- **Too small on a phone.** The stage fills only ~60 % of the frame and the panel text is tiny. The
  CJK copy also carries meaning that non-Chinese viewers lose.
- **Loose on the beat.** Only 34 % of cuts land on a beat.
- **Uneven quality.** The aurora-glass and synthwave spots are trend-generic (see the fingerprint list
  in [[code-motion-showreels]]). Pixel art and the 3D chapter are the strongest.
- **A catalogue, not a music video.** No through-line beyond the frame device; each spot is
  self-contained.

## Against Muse's studio
- **14 of 15 styles are browser code** (Canvas, SVG + GSAP, Three.js, WebGL shaders), which
  [[tool-selection]] already covers.
  - SDF metaballs and heavy glass shaders are slow under SwiftShader, so render those chapters on a
    GPU.
  - Palette cycling is trivial on a canvas.
  - The vertical caption chapter is `kinetic-lyrics` territory.
- **The gap is chapter 05: Blender Cycles driven by Python** (physics-simulated 3D). It is not in the
  stack; it could run as a Modal GPU job. Not adopted. Flagged as the one engine this reel has that we
  don't.
- **Portable craft to take:**
  - a one-event, ends-on-a-mark structure per style;
  - token bridges that carry material across a cut;
  - a visible "how it's made" layer when the claim is "made in code".

## Lead from the replies
@superalesha (Alexey Fateev), x.com/superalesha/status/2104953991620710703 (2.4k views):
- A happy, pink, loud pop song about the US–China chip war, made "opposite to the p(doom) videos". No
  video model; Claude built every scene in code.
- Packaged as a skill: `github.com/alesha-pro/tools/tree/main/skills/lyric-music-video`. It builds on
  **mexicat/pdoom-video**, not JohnHeibel's PDoomVideo (see [[claude-pop-case]]).
- Possibly worth a look for a variable-tempo beat tracker for generated songs.
- Not read in depth yet.
