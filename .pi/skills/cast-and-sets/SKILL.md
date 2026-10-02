---
name: cast-and-sets
description: Design a video's cast and locations with image models so they stay on-model through every generation - protagonist design (often a brand, artist or AI personified), character turnaround and expression sheets, backup dancers and supporting cast as variations of one design system, set/environment plates composed with room for lyrics, and the assets.json registry of uploaded references. Use in phase 4 of a video project, or whenever a character, mascot, dancer troupe or location must be designed or re-generated consistently.
license: MIT
compatibility: fal-media skill (FAL_KEY); style-bible tokens.
metadata:
  author: muse
  version: "1.0.0"
---

# cast-and-sets — on model, every time

## Protagonist
1. **Who**: write a one-paragraph character bible — what they embody
   (e.g. the brand's mark and voice made human/idol), age read, vibe,
   signature silhouette element, signature color, signature prop/gesture
   (the "killing part" move from the storyboard), what they must never look
   like. Derive distinctive features from the source identity (a logo's
   shape language → hair/costume/accessory), not from generic "cute girl".
2. **Key design** (1–4 candidates on the chosen model with bible tokens).
   Pick one; iterate by *edit*, not re-roll, to keep what works.
3. **Sheet**: from the chosen key, generate via edit/multi-ref:
   turnaround (front, 3/4, side, back), 6 expressions (neutral, joy, awe,
   fear, determination, singing-open-vowel), 3 action poses, hands.
   Layout one sheet image on a flat paper background, labels off.
4. **Consistency check**: put the sheet next to 3 fresh generations using
   it as reference; if face shape, hair mass, costume or palette drift, add
   the drifting feature to the character tokens and re-run.

## Troupe & supporting cast
- Backup dancers = a *system*: same base proportions and costume grammar,
  varied by one axis (color accent, accessory, hair) so formations read
  as a unit and the protagonist stays the center.
- Supporting characters get a mini-sheet (front, 3/4, 2 expressions).
- Keep the cast small: every extra character costs consistency and money.

## Sets
- One set per world/section + the recurring chorus stage (it escalates per
  chorus: same geometry, new dressing/lighting/scale).
- Generate each set EMPTY at 16:9 with the storyboard's text zones calm
  (describe the zone: "left third open sky / plain wall").
- Make 2–3 camera angles per set by edit, same props and light.

## Registry
Upload every approved sheet/set once (`fal.py upload`) and record in
`projects/<slug>/assets.json`: `{id, kind, file, url, tokens, notes}`.
Plates reference assets by these URLs as @Image1..n, in a stable order
(protagonist sheet first, then set, then extra cast).

## Acceptance
Protagonist sheet + ≥1 dancer sheet + every storyboard set exist, pass the
consistency check (3 fresh generations on model), sit inside the bible, and
are registered in assets.json with URLs; one contact image of the cast is
ready for the checkpoint with the principal.
