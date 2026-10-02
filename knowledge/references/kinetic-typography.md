---
kind: typography
tags: [lyrics, motion-graphics, retention, layout]
audience: all
half_life: 3650
rights: safe
seen: 2026-09-26
---
# Kinetic lyric typography — text as a retention engine

Text on screen is the cheapest attention hold there is: people read before
they decide to scroll. It must be designed, not captioned.

**Three modes** (chosen per line in the storyboard)
1. **Hero** — the line IS the shot. Huge (30–60% of frame height per word
   group), set word-by-word on the vocal onsets from `song.json`, composed
   into negative space the plate left for it. Use for the hook, the
   title/chorus line, and punchlines. Always in the first 2 s.
2. **Integrated** — text lives in the world: painted on a wall, on a phone
   screen, a banner behind the dancers, a chart label. Readable but
   secondary.
3. **Subtitle** — small, consistent, lower third or top band, karaoke-lit
   by word. For verses where the picture carries the meaning.
Plus **none** for moments where text would compete with a visual payoff.

**Rules**
- Word on onset: a word appears ≤1 frame before its sung onset (from
  `song.json words[].t0`), never after. Emphasis words get scale/weight hits
  on the beat.
- One typographic system per piece: 1 display face + 1 text face max;
  treatment evolves by section (e.g. clean → glitched → fractured as the
  song accelerates), never random.
- Composition first: storyboard marks the text zone (left third, top band,
  center stack); the plate is generated with that zone calm.
- Contrast is non-negotiable: readable at phone size over the plate (test
  by downscaling the frame to 360 px wide).
- Motion vocabulary: slam-in (scale 1.3→1 with 2-frame overshoot), type-on
  per syllable, split-and-drift on held notes, smear/whip exit on the cut,
  kinetic reflow when the camera moves (text sticks to world or to screen —
  decide per shot).
- Don't repeat the picture: if the frame shows the thing, the text can be
  the feeling, or absent.
- 9:16 cutdowns: hero text re-laid, not cropped.

**Voice contrast and moves (from [[code-motion-showreels]])**
- Principle: give type roles (statement / human word / label) and contrast them in voice, not
  decoration. The showreels' grotesk + italic serif + mono pairing is their fingerprint — pick faces
  for each song instead.
- Moves that read as designed: per-letter rise from a baseline mask; letters riding in on an arc with
  rotation and overshoot; vertical motion-blur drop; selection brackets snapping around the key word;
  whip-reflow with blur when a line grows; echo/outline stacks; word wallpaper; a word collapsing into
  a row of dots (type → motif); text on rotating rings; typewriter subtitle with a block cursor.
- Engine: HyperFrames DOM type is the default (real kerning, masks, blend); painted type only when the
  medium demands it. Fonts registered from bytes on this box ([[tool-selection]]).
