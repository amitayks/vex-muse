---
name: collage-motion
description: Build mixed-media paper-collage motion - the archive-scrapbook / editorial explainer look (torn paper pages, B&W halftone cutout photos, die-cut stickers, keyword labels with marker underlines, masking tape, clippings, big dates, header + chapter counter + progress dots) animated as stop-motion builds, holds and paper transitions (page peel, zoom-through with an object carried across the cut, tear, strip wipes) in HyperFrames, with image-model assets, $0 procedural paper and matting (white key / SAM 3 / Bria). Use for history, origin-story, documentary or explainer pieces, "make it like that Pexo / collage / scrapbook video", nostalgia or memory sections of a music or lyric video, or any shot whose read is a page of evidence being assembled.
license: MIT
compatibility: tools/env.sh ($PY with numpy/scipy/pillow, ffmpeg, CHROME_PATH); HyperFrames 0.8.78 + GSAP 3.15 (projects/lab-motion-tools/node_modules); FAL_KEY for assets and paid mattes.
metadata:
  author: muse
  version: "1.1.0"
---

# collage-motion — a page of evidence, assembled on the beat

Reference and its measurements: [[paper-collage-explainer]] (take the principles, not its
cobalt/cream/"RISE OF" fingerprint). Engine rules (fonts from bytes, sources outside the project,
pure functions of t): skill `code-motion`. Proof and working example: `projects/lab-collage/`.

## 1. Write the page system first (`projects/<slug>/collage-brief.md`)
- **Series chrome**: title for the header, chapter count (the counter and the dots), 9:16 or 16:9.
- **Per chapter**: headline ≤ 3 words per line × 2 lines · the date (big numerals or a sticker) ·
  hero image idea (photo in a torn frame or a die-cut cutout) · 2–5 **keyword stickers = nouns of
  the narration or lyric** · ≤ 1 clipping · one caption sentence · the transition out (§5).
- **Look** (from `style-bible`, never from the reference): paper tone, ink, ONE accent, marker
  colour, display face (heavy condensed) + mono (labels, notes, header) + serif (caption, clippings).
  Past = archival B&W halftone; colour only on artifacts that were coloured.
- **Rhythm** on the song grid: per chapter build ≤ 2 bars → hold ≥ 1 beat and ≥ 0.9 s → transition
  ≤ 2 beats. Escalate across chapters (faster builds, shorter holds) and land the last on a payoff that
  rhymes with the open — the reference's flat rhythm and 5 s dead end are what we beat.
- A chapter with no event (nothing changes but more stickers) is not designed yet: give it one
  (a count that multiplies, a stamp, a date that flips, a hand that takes the object).

## 2. Generate assets, not pages
- Image model = Nano Banana Pro (`fal-media`), one model per piece. Prompt tokens and per-asset
  templates: `references/prompts.md`. Photos: **archetypes, never real people's likeness**; brands as
  generic objects. Props and hands **isolated on pure white**. 2K, 3:4 / 1:1 / 4:3 by shape.
- Never ask the model for the page, the headline or any label: all type is DOM (spelled right,
  crisp, on the beat). Model text is the #1 tell of the generated route.
- Ledger every call (`--ledger projects/<slug>/ledger.jsonl --tag <asset>`); ~$0.15 per asset.

## 3. Cut them out — `scripts/cutout.py` (run `$PY … --help`)
| Source | Command | Cost |
|---|---|---|
| prop / hand on white | `--matte white --shape die --grade bw --border 12` | $0 |
| photo → torn print with fibre rim | `--shape torn --inset 0.035 --grade bw --tear 22 --rim 12` | $0 |
| subject inside a full photo (depth sandwich) | `--matte sam:person --shape cut --notrim --savemask m.png` with the **same** `--inset/--max` as its torn print | $0.005 |
| isolated object with hair/fur/soft edges | `--matte fal` (Bria) — busy scenes come back ~all foreground | $0.018 |
Reuse saved masks with `--mask`. LOOK at every cutout on a dark and a light ground.

## 4. Paper, tape, ink — `scripts/paper.py` ($0, seeded)
`--kind bg` backdrop · `sheet` page stock · `stock --tone <accent>` construction paper for strips,
rays and sheets (give torn elements an explicit CSS box: `torn` measures it for edge density) · `kraft` tape PNG · `ink` letterpress mask (CSS `mask-image` on display type).

## 5. Build in HyperFrames
- Start from `assets/collage-template/` (README there: copy, fonts, build with
  `code-motion/scripts/hf_build.py`, symlink `node_modules` from `projects/lab-motion-tools`). Its
  content is the lab replica: replace every image, word, colour and position.
- `assets/js/collage.js` (API in its header): `torn`, `enter(el, drop|slap|slide|stretch|pop|rise,
  t)`, `stamp` (headline letters), `type` (mono/serif), `draw` (marker, arrows), `peel`, `boil`,
  `finish(tl, DUR)`. Time in beats: `at(bar, beat)`.
- **Stop-motion rule**: builds sample at `step: 15` (on twos at 30 fps; 12 at 24 fps); cameras,
  zooms and peels stay smooth. Elements appear placed in 3–5 steps, never fade.
- **Build order**: page → hero → header + progress row → headline → date → stickers/clippings (one
  per step-beat) → caption → progress dot. Chrome belongs to the page: it never shows before it.
- **Depth sandwich**: torn print < big date < `--notrim` subject layer, same box and same entrance.
- **Stacking**: headline and caption are the top reads in DOM order (above rays, clones, stickers,
  tape); only the depth-sandwich subject may cover the date. Collage clutter never crosses a word.
- **Layers** use a `.sh` wrapper for shadow and an inner element for the torn clip (a clip on the
  shadowed element cuts its shadow off). Wrappers need real size if anything inside is `inset`.
- **Transitions — one per seam, made of the medium, never a crossfade** (math in
  `references/recipes.md`): page peel into the next sheet · zoom-through into an object + the object
  carried across the cut into its next home · strip/sheet slap wipe · a paper object (plane, ticket)
  flying from one page into the next. Pick by story: carry when the object continues, peel for a
  chapter break, wipe for speed.
- Camera: push 1.00 → 1.03 over the build+hold; the page moves as one print, chrome included.
- Living photos (optional): a 480p Seedance 2.5 image-to-video draft of the hero photo, placed as a
  muted `<video>` inside the torn frame — not yet verified in the lab; verify before a project
  depends on it. The generated-page route (image page + first/last-frame video) only for a physical
  transition you cannot code; never for anything with text.

## 6. Review (the gate)
Lint 0 errors → `snapshot --at` every build beat → draft render → `framestudy.py` on the render.
Check:
- headline and date readable at 360 px wide; no sticker, tape or arrow crossing headline/caption glyphs;
- every sticker is a keyword of the narration; all copy proofread (DOM means no excuse);
- builds stepped (motion curve spiky during builds, flat in holds); each hold ≥ 0.9 s measured from
  the caption's last typed character (start + chars/cps), not from the last slap; cuts and
  slams on beats; the first 2 s show the hero and the start of the headline;
- nothing visible before its page (chrome, dots, strokes' round caps);
- top ~8 % and bottom ~11 % of a 9:16 frame free of reads (platform UI);
- the ending pays off and rhymes with the open; spend logged.

## Acceptance
`collage-brief.md` exists; every asset in the ledger and looked at; draft MP4 with the song passes
§6 (framestudy read, snapshots read, notes in `review/`); final render only after the draft passed;
any new mechanic added to `collage.js` with its lesson in LEARNINGS.md.
