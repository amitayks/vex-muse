# Craft vocabulary — the decisions behind "every frame on purpose"

Distilled from the frame study of the Opus 5.5 showreels ([[code-motion-showreels]]) and the
HyperFrames motion rules (vendored knowledge, heygen-com/hyperframes skills, Apache-2.0).

## Easing is the adverb
- Enter with `.out` (expo.out confident, back.out playful overshoot), leave with `.in`, move between
  positions with `.inOut`. Backwards eases are the commonest amateur tell.
- No more than two tweens in a scene share an ease; the slowest scene is ≥3× slower than the fastest.
- Named curves are content too: `cubic-bezier(0.83,0,0.17,1)` shown in a graph editor is a joke designers get.

## Speed is weight
0.15–0.3 s energy · 0.3–0.5 s default · 0.5–0.8 s gravity · 0.8–2 s atmosphere. Exits are faster than
entrances (0.4 in / 0.25 out). Don't start at t=0: first move at 0.1–0.3 s.

## Snap, then hold
Reference showreels spend 22–29 % of frames perfectly still. Motion arrives as a snap on a beat, then
the read sits. A scene = build (0–30 %) · breathe with ONE ambient motion (30–70 %) · resolve (70–100 %).

## Rhythm across the piece
Bar-length chapters → beat cuts → half-beat supercut (6–8 micro-scenes) → hard stop → end card ≥1.5 s.
Name the pattern before building ("bar,bar,bar,bar,beat,beat,½×8,HOLD").

## Transitions are sentences
Hard cut = wake up; motif iris / zoom-match = "this becomes that"; velocity-matched push/whip =
continuous camera; shader (domain-warp, whip-pan, light-leak…) = centrepiece only, 1–2 per piece;
crossfade = "this continues" — rare. Every seam gets a named transition in the storyboard.

## Choreography is hierarchy
What moves first matters most. Stagger by importance, total stagger < 0.5 s, overlap entries.
Vary entry directions per scene (rise, arc, scale, letter-spacing, mask wipe).

## Type
- Contrast of voice by role (statement / human word / label), faces chosen for the song. The
  showreel pairing (Archivo Black + Instrument Serif Italic + IBM Plex Mono) is now a trend fingerprint:
  don't default to it. Fonts live in `studio/assets/fonts/` — add new open-licensed faces per project.
- Hero words 60–80 % of frame width; anchor to edges or a grid, not centred-and-floating (except
  wordmarks). Two focal points per frame.
- Moves: mask rise, arc-in with rotation, vertical motion-blur drop, echo/outline stack, word wallpaper,
  text → dots, text on rotating rings, typewriter subtitle with block cursor, bracket/selection frame.

## Frame design
Three layers minimum (field / content / chrome). Flat fields are fine *with* grain and chrome; empty
pure black reads "not loaded". Structural lines must connect two real things. Hard colour-field
switches per chapter; one accent colour does all emphasis.

## Unity under variety
Many techniques, one author: same palette, same texture, same type system, same motif.
If a chapter needs a different palette to work, the chapter is wrong.

## Slop tells in motion (reject on sight)
Looking like last month's viral trend (see the fingerprint in [[code-motion-showreels]]) ·
website-hero layout per slide · one layout repeated · slides on a fixed clock off the beat · glossy
chrome blob that only rotates · generic slogans · every element `y:30 → 0, opacity 0 → 1` ·
same ease everywhere · crossfade soup · centred everything · ambient zoom on every scene.
