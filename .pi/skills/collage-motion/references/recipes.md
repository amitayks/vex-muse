# Recipes — collage-motion (math and layouts that worked in `projects/lab-collage`)

## Page layout, 9:16 (1080×1920)
| Zone | Box (px) | Content |
|---|---|---|
| free top | y 0–150 | paper only (platform UI) |
| page card | x 26–1054, y 150–1712 | torn `sheet`, amp 11 |
| header | y ~192, x 66–1014 | mono 24 px, tracking .14em · rule · `NN / NN` |
| headline | x 58, y 224 and 372 | display 150–160 px, 2 lines, `.ink` mask |
| hero + date | y 540–1420 | torn print ~650 px wide right; date 400 px left, under the subject layer |
| stickers / clippings | y 1100–1550 | cutouts overlap the hero's lower corners; labels 48 px mono |
| caption band | y 1560–1644 | torn label band, serif 40 px, one line (≤ 55 chars) |
| progress + corner notes | y 1668–1740 | dots 24 px (current = marker colour), mono 15 px lists |
| free bottom | y 1740–1920 | paper only |
16:9: header across the top, headline top-left, hero right half, stickers bottom-left, caption band
bottom; keep 5 % margins.

## Zoom-through with a carried object (cut on a downbeat)
Screen scale of the object at the cut = k (object width → ~900 px). With a camera push s about C and
the object centre P:
```
Pc = C + s·(P − C)                                  // object centre on screen after the push
#zoom1: transformOrigin Pc; x = T.x − Pc.x; y = T.y − Pc.y; scale = k / s   (power3.in, 2 beats)
at the downbeat: hide ch1, show ch2 and a top-level #carry clone whose CSS home is its ch2 place H,
  fromTo {x: T.x − H.x, y: T.y − H.y, scale: 900 / homeWidth, rotation: old} → {0, 0, 1, new}
  (0.4 s back.out, smooth); ch2 zoom 1.12 → 1 (expo.out, 1 beat)
one beat later: hide #carry, show the in-scene copy at H (it must be inside ch2 to be peeled later)
```
Zooming into a flat region to hide the cut only works if that region fills the frame on both sides;
carrying the object is more robust.

## Page peel (collage.js `peel`)
Fold line ⟂ `dir`, travelling from the corner opposite `dir` for 2.05 × the frame's extent along
`dir` (the flap must clear the frame). Outgoing layer clipped to the kept half-plane (CSS polygon, px),
flap = the lifted region reflected across the fold, filled with a `userSpaceOnUse` gradient from dark
at the fold to paper, plus a CSS drop-shadow on the SVG. `dir: [-1, -0.85]`, 2 beats, `power2.in`.
The next page (or an accent sheet) sits underneath and is visible from the peel's start.

## Stop-motion sampling
`build.seek(floor(t·step + 1e-4) / step)` from one proxy tween. step 15 at 30 fps, 12 at 24 fps;
a non-divisor (12 at 30 fps) gives uneven 2-3-2-3 cadence.

## Entrance defaults (collage.js)
drop 0.33 s back.out(2) from −140 px +9° · slap 0.2 s power4.out from 1.35× −6° · slide 0.4 s
back.out(1.3) from an edge · stretch 0.14 s (tape, rays, rules) · stamp 16 letters/s · type 30–75
chars/s (captions fastest) · draw 0.2–0.35 s.
