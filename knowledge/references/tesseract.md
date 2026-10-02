---
kind: technique
tags: [tesseract, hypercube, 4d, projection, cross-section, flatland, svg-transform, structure, unity-under-variety]
audience: general — recognised via Interstellar, Marvel, A Wrinkle in Time, Dalí; the geometry itself is known to few
half_life: 1825
rights: safe
seen: 2026-09-26
---
# The tesseract — what it is, how it is shown, and what it gives a director

**Plain words.** A square is a line swept sideways; a cube is a square swept up; a **tesseract** is a
cube swept into a fourth direction. It has **16 corners, 32 edges, 24 square faces and 8 cubes** as its
"sides" (cells); every corner meets 4 edges — the name is Hinton's (1888, *A New Era of Thought*):
Greek *téssara* "four" + *aktís* "ray". We can never see it whole; we only ever see a **shadow**
(projection) or a **slice** (cross-section) of it. That fact — one object, only ever seen as changing
views — is the useful part for film.

## How it is shown (and the math each view needs)
- **Rotation happens in planes, not around axes.** 4D has six coordinate planes (XY XZ YZ + XW YW ZW).
  A *simple* rotation turns one plane and leaves the other fixed; a *double* rotation turns two
  perpendicular planes at once; with equal angles it is *isoclinic* (Clifford) — a motion no 3D
  object can make. Code: rotate the (i, j) pair of each vertex like a 2D rotation.
- **Perspective 4D → 3D → 2D.** Divide x, y, z by the distance along W (like dividing by depth), then
  project to the screen as usual. With the eye on the W axis you get the familiar **cube inside a
  cube**, joined by 8 edges — a Schlegel-style view (Schlegel 1886: project through a point just
  outside one cell, so that cell frames all the others). The 6 "frusta" between the cubes are the
  other 6 cells, squashed.
- **Turning inside out.** A 180° turn in XW, YW or ZW carries the inner cube out through a side to
  become the outer cube (the whole object passes through itself). A 90° turn in any plane maps the
  tesseract exactly onto itself — the end pose is identical to the start.
- **Parallel "shadows".** Cell-first = a cube; face-first = a box; edge-first = a hexagonal prism;
  vertex-first = a rhombic dodecahedron. Same object, four silhouettes.
- **Cross-sections (the Flatland method).** In *Flatland* (Abbott, 1884) a Square meets a Sphere and
  sees only a circle that grows and shrinks. A tesseract crossing our space corner-first appears as
  **point → tetrahedron → truncated tetrahedron → octahedron → (mirror) → point** (verified in
  `nd4.js`); a cube crossing a plane corner-first shows **triangle → hexagon → triangle**.
- **The net.** Unfolded into 3D it is 8 cubes; there are 261 distinct nets. One is the "Dalí cross":
  Dalí's *Crucifixion (Corpus Hypercubus)* (1954, the Met) hangs Christ on it — the unfolded form of
  something the mind cannot hold, as a readable body.

## Where it lives in culture (what an audience brings)
- *A Wrinkle in Time* (L'Engle, 1962): "tessering" = folding space-time to travel.
- *Interstellar* (2014; Kip Thorne consulting): Cooper inside a tesseract of endless copies of Murph's
  bedroom across moments in time — time laid out as a place you can walk; he talks through the
  second hand of her watch. The most loved screen image of the idea: **time as a room**.
- Marvel's Tesseract (*Thor*, *Captain America*, *The Avengers*, 2011–12): a glowing cube housing the
  Space Stone — the word as a magic box, no 4D content. Also Heinlein's "—And He Built a Crooked
  House" (1940), the Grande Arche in Paris (1989, designed after a tesseract projection), *Fez*.
- **Mirage "Tesseract"** (Sep 22 2026, [[whatships]]): a video suite for AI agents; its film shows a
  wireframe cube turning into nested cubes on a CRT — the hypercube as a "more dimensions" logo.
  The engine itself has no 4D content; the name is branding. See [[mirage-tesseract]] for the engine
  test.

## Verdict on the four hypotheses (tested, not forced)
- **(a) A visual technique — YES, adopted** into skill `svg-transform` (module `assets/nd4.js`). Three
  moves worth having: *inside-out turns* (a W-plane turn: the inner becomes the outer continuously;
  90° multiples land on an identical pose → bar-locked loops and hidden cut points); *the slice*
  (one hidden object yields a lawful sequence of shapes — an entrance/exit that goes point → shape →
  point, and whose size can follow the song's energy); *depth as pen weight* (the 4th-direction depth
  drives stroke width — ink logic, not glow).
- **(b) A video is a 4D object, every frame a slice — PARTLY.** Literally, a 2D video is a 3D block
  (x, y, t) and a 3D world over time is 4D; slit-scan is slicing that block at a tilt. But Coxeter's
  warning holds: "little, if anything, is gained by representing the fourth Euclidean dimension as
  time." What survives is a planning habit the storyboard already mostly has — plan the whole
  object, not the frames. Not added as new method.
- **(c) Unity under variety — YES, as a planning lens,** and it is already how the best launches work:
  Mirage's own film is one Muybridge horse in ~15 treatments; Cube Motion is one dot system in every
  state. Rule (in skill `storyboard`): name the **invariant** (the one object/idea), make each section a
  different **projection** of it (view, slice, medium, scale), and move between sections by changing
  the view continuously, not by replacing the thing.
- **(d) Better — the Flatland reveal.** Show lawful shadows or slices of the hidden whole first, let the
  viewer infer it, reveal the whole at the payoff. Suspense from rule-bound partial views. Pairs with
  (c); in `storyboard` beside it.

**Originality rule.** A rotating wireframe hypercube (neon on black, "4D = tech") is a cliché and, since
Mirage, a brand's logo. It enters only as structure (projections of one idea), transition grammar
(inside-out, slice) or a lawful morph — dressed in the piece's own medium, never as the look.

## The $0 lab tests (`projects/lab-motion-tools/`, sources `tesseract-src/`, build `tesseract-src/build.sh`)
- **turn** — `renders/tesseract_turn_v2.mp4` (8.1 s, 128 BPM, HyperFrames SVG). Bar 1 builds it on
  the beats (inner cube, outer cube, the 8 rays into the fourth direction, the fill); bar 2 turns
  XW 180° (the pink cell comes outside); bar 3 YW 180° (back in by another way); bar 4 XY + ZW at
  once (isoclinic). Each turn runs 3 beats and lands on beat 4, then holds. A plane indicator
  (X Y Z W with arcs) says which plane is turning.
- **slice** — `renders/tesseract_slice_v2.mp4` (8.1 s). Left: a cube crossing a flat world (triangle →
  hexagon → triangle). Right: a tesseract crossing ours, flat-shaded, one step per beat; bar
  downbeats land on the landmark shapes (tetrahedron, octahedron, mirrored tetrahedron, gone).
  Faces are coloured by which side of the tesseract they come from (teal side / pink side): the
  shape arrives teal, is a teal-pink checker at the octahedron, and leaves pink.
- Measured (v2): 243 frames rendered in 32–33 s (draft, 2 workers); motion energy lands on the beat
  grid with 59 % (turn) and 82 % (slice) of frames held — reviews in `review/tesseract-*/study_v2/`.
  v1 → v2 fixes: the bar-4 swing crossed the caption (envelope now measured over every frame and
  kept above it); the octahedron beat showed only 2 faces (camera angle chosen by search so it shows
  the 4-face checker); palette moved off the fingerprint.
- Limits: wireframe without hidden-line removal (fine for a line drawing, wrong for solids); the slice
  renderer assumes a convex polytope (true for all cross-sections of a tesseract); lab pieces, no
  song or story; palette chosen off the trend fingerprint (v1 used cobalt/orange on cream — the
  fingerprint — and was re-rendered).
- Review verdict (stranger watch of v2, same day): the math reads correctly and every turn lands on
  its beat, but both films fail phone legibility. The bottom captions are too small, and the object
  sits small in a mostly empty frame. Before any project reuse, scale the object to fill the frame
  and set captions at hero or subtitle size ([[kinetic-typography]]).

Sources (Wikipedia, retrieved 2026-09-26): Tesseract · Rotations in 4-dimensional Euclidean space ·
Four-dimensional space (dimensional analogy, cross-sections, shadows, Coxeter quote) · Schlegel
diagram · Crucifixion (Corpus Hypercubus) · Flatland · Charles Howard Hinton · A Wrinkle in Time ·
Interstellar (film) · Infinity Stones. Mirage post: https://x.com/trymirage/status/2102429594804429138
