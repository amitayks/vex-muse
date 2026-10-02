# Asset prompts — collage-motion

Verified on Nano Banana Pro (`fal-ai/nano-banana-pro`, 2K, png) on 2026-09-26: 4/4 usable first take
(`projects/lab-collage/gen/in/*.json`). Swap the era, subject and props; keep the tokens.

## Tokens
- **Print** (every photo and prop): `Vintage black-and-white press photograph, coarse newspaper
  halftone print texture, visible film grain, slightly faded blacks, documentary and candid, not
  glossy, not cinematic lighting.`
- **Isolate** (props, hands, objects): `Isolated on a plain seamless pure white background, the whole
  subject in frame with a generous margin, no cast shadow, no text, no logos, no brand names.`
- **People**: `an ordinary anonymous face` + an archetype (teenage musician, office worker, family
  at a computer). Never a named or recognisable person; allude by era, costume, prop, place.
- **Labels on objects**: `blank paper label with nothing written on it` — we print our own words
  in DOM on top if the object needs one.

## Templates
| Asset | Aspect | Prompt shape |
|---|---|---|
| Hero photo (torn print) | 3:4 | `<year>. <archetype> <doing the chapter's verb> in <place>, <2–3 period props>, <background detail with no readable text>. <Print> No logos, no text.` |
| Prop cutout | 1:1 / 4:3 | `A single <object> at a slight three-quarter angle, <one identifying detail>. <Print> <Isolate>` |
| Hand + object | 3:4 | `<year>. A hand holding <object> up toward the camera, entering from the bottom edge of the frame, fingers gripping its side. <Print> <Isolate> The wrist is cut off by the bottom edge.` |
| Crowd / place (inset photo) | 4:3 | `<year>. <place> full of <archetypes> <doing X>, wide shot. <Print> No logos, no text.` |

## Observed
- The photo came back with its own aged print border → `cutout.py --inset 0.035` removes it before
  tearing.
- White-ground props matted perfectly with the $0 white key (flood fill from the edges keeps
  light labels enclosed by a darker shell).
- A full room scene through Bria returned 97 % foreground; SAM 3 with `person` gave a clean
  subject mask for the depth sandwich.
- Posters and screens in generated rooms carry pseudo-text; keep them small and behind the date,
  or ask for "posters of abstract shapes".
