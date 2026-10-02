---
kind: video
tags: [case-study, collage, mixed-media, paper, scrapbook, explainer, history, editorial, stop-motion, vertical, pexo, generation-pipeline]
audience: history / explainer / documentary feeds (Reels, TikTok, X video); tech-history audience on X
half_life: 150
rights: safe
seen: 2026-09-26
summary: The "archive scrapbook" explainer (Pexo's 30 s Rise of Microsoft, via @omarsar0) measured frame by frame - page grammar, build-hold-transition rhythm, paper transitions, how it was generated and where it breaks - plus Muse's code-first recreation, proved in projects/lab-collage.
---
# Case: the paper-collage explainer (Pexo, "The Rise of Microsoft", Sep 2026)

Source: @omarsar0 2103575986772070862 (25 Sep 2026, 9.5 k views, 321 k followers): "Hours researching…
5 min feeding that research into Pexo… 10–15 min later, a finished 30 s video… cutouts, stickers,
supporting images… nothing felt randomly added… first take." Pexo is an agentic AI video maker.
Evidence: `research/x/omarsar0-2103575986772070862/` (post, video, `study/` from `framestudy.py`,
`crops/`). Method to make it ourselves: skill `collage-motion`.

## Measured
- 1440×2560, 24 fps, 30.0 s, music bed only ("Inspired", Kevin MacLeod, CC BY 4.0, credited on the
  last frame), Pexo watermark bottom-right.
- **7 chapters, one page each** (`01 / 07` … `07 / 07`), 3.3–5.7 s per chapter. Only 6 hard cuts
  detected: most seams are **in-camera paper transitions**, not cuts.
- Rhythm per chapter: **build 1.5–2 s → hold 1–1.5 s → paper transition 0.3–0.6 s**. Holds are 17.5 %
  of frames (code showreels: 22–29 %). During builds motion energy alternates frame to frame
  (3.2–4.5 s): elements are placed with few in-betweens = a stop-motion feel.
- Music: ~160 BPM detected; 2 of 6 cuts within a frame of a beat, the rest 40–124 ms off. Chapter-paced,
  not bar-authored.
- Palette (per-shot k-means): aged cream paper `#D8C8B6` (45–50 %), warm ink `#1C1A18`, halftone greys,
  **one accent: cobalt `#17477B`–`#2B568D`** (torn construction paper, the big years, the IBM stripes),
  red marker underlines, khaki/kraft tape. Period colour only on period artifacts (Windows flag,
  Win95 box, Office tab colours).

## The page grammar (what every chapter repeats)
1. Full-bleed aged paper; a **torn-edge page card** from ~9 % to ~88 % of the height — top and bottom
   stay free (platform UI safe zones).
2. **Header chrome**: series title in small condensed caps + hairline rule + chapter counter
   (`THE RISE OF MICROSOFT ———— 03 / 07`).
3. **Headline**: 2 lines of heavy condensed grotesk caps, ink-distressed, top-left
   ("IT STARTED WITH CODE", "THE IBM DEAL", "ONE DISK. MANY PCs.", "EVERY HOME. EVERY DESK.").
4. **The date**: either huge cobalt numerals (1975) **sandwiched between the photo's background and
   its people** (Allen's head in front of the "5") or a paper date sticker (1981) with a red underline.
5. **Hero image**: B&W halftone archival-style photo in a torn frame, or a die-cut cutout with a white
   border (hand holding the floppy).
6. **Keyword stickers**: kraft/paper labels in slab/typewriter type + red marker underline — each is a
   noun from the narration: BASIC, Micro-Soft, PARTNERSHIP, LICENSE, INSTALL → REPEAT, OPEN, CLICK.
   Plus clippings (Popular Electronics, WSJ "MSFT", BusinessWeek) and masking tape.
7. **Bottom**: one serif caption sentence; a progress row of 7 dots (current one red); tiny mono
   keyword lists in the bottom corners.
The page is a visual summary you can pause on; the counter promises a finite story (completion).

## Build order inside a chapter
backdrop/paper → hero photo → header types on → headline types (letter- or word-wise) → date slams →
stickers/clippings one every 0.15–0.3 s → caption → progress dot. Camera: slow push or pull on the
whole page during the hold — the headline moves with it (it is printed on the page, not a HUD).
Photos are "alive": a handshake closes, people lean, paper flutters.

## Transitions (all paper or objects; no crossfade anywhere)
| t | move | read |
|---|---|---|
| 0.0 | torn blue sheet unrolls in from the right | "the scrapbook opens" |
| 3.3 | page rolls up like a scroll, next photo under it | turning to the next document |
| 7.5 | **zoom-through**: into the floppy label/hub, cut, pull out to a hand holding the floppy | the object carries the story |
| 14.2 | **page peel** from the bottom-right, white paper back, full cobalt sheet under it | chapter break |
| 19.3 | whip through graph paper into the office | speed |
| 25.0 | **paper plane** flies out of the PowerPoint page into the Windows 95 page | motif carry |

## How it was made (inference, with evidence)
Every page is **one image-model render** and the build is **a video model interpolating toward it**:
- small text is garbled in the pixels: "ALBUQVERQVE / CORE / CONDUTERS / FOOPLE", "possibiiity",
  "New Moxico", "Tonerrow", "A LAEGER TONGOROW";
- the header and counter crop and scale with the camera (they are not an overlay);
- type resolves out of blur mid-build ("Ilicro-Sufi" → "Micro-Soft" at 2.3 s), "DEAL" rises at a
  different size and baseline than its final (5.6 s), a contract lands blank and gains text (5.2–5.5 s).
Pipeline, probably: research → script → per-chapter page keyframe (image model, full layout + type) →
first/last-frame video generation for each build and each transition → concat + CC-BY bed + watermark.
**Strengths**: fast, physically rich transitions (the roll, the peel, the flutter), a coherent
document system. **Costs**: typos in every small text, no beat authoring, readability at the model's
mercy, photoreal likenesses of real people generated (Gates, Allen, an IBM executive) — a rights risk
we don't take (reference-mesh rule: archetypes, never likenesses).

## Where it breaks (what to beat)
- The first second is blank paper + a blue strip: no hook until the headline at 1.3 s.
- Every chapter has the same rhythm (build/hold/transition): no escalation, no accelerando.
- The ending is the last page holding ~5 s — no payoff, no rhyme with the open.
- Readable-at-a-glance text sits beside unreadable model text; a designer screenshot dunks on it.

## Principles vs. the look
**Portable craft**: the page as a document (series title + counter + progress = a finite story) ·
stickers = the narration's keywords, so the page summarises itself · the depth sandwich (date between
a photo's background and its people) · build → hold → paper transition · transitions made of the
medium (peel, roll, tear, zoom-through, a paper object carried across) · one accent on neutral
paper · archival B&W = "the past", colour only on the artifacts that were coloured.
**Fingerprint — never a default**: cobalt + cream + red-marker palette · "THE RISE OF X" header ·
Anton-like headline + typewriter labels · blue construction-paper strips and rays · the blue-sheet
peel · `01 / 07` dots. Any of these needs a reason from the piece; change the accent, the paper, the
type pairing and the transition set per project (`style-bible` → Divergence).

## Muse's recreation (code-first, proved 2026-09-26)
`projects/lab-collage/` ([[lab-collage]]): "THE HOME STUDIO", 2 chapters + end card, 1080×1920,
128 BPM, 18.3 s. Assets generated separately (Nano Banana Pro: one B&W halftone archetype photo +
3 props on white, $0.60), matted ($0 white-key; SAM 3 `person` $0.005 for the subject inside the
photo — Bria returned 97 % foreground on a busy room), paper/tape/ink procedural ($0). Everything
typographic is DOM: spelled right, crisp, timed on the beat grid. Builds stepped at 15 fps (on twos)
while the camera stays smooth; depth sandwich ("1979" between the room and the teen); transitions:
zoom-through with the cassette carried across the cut, and a code page peel into the end card.
Total spend $0.62.
**Better than the reference by construction**: correct text, beat-authored, no likeness risk,
editable per element (a re-cut is a re-render, not a re-generation).
**Where the generation route still wins**: organic paper physics (a scroll roll, cloth-like flutter)
and living photos. Use a Seedance 2.5 image-to-video plate *inside* a torn frame for those
(untested here; see [[generation-field-notes]]), never for type.

Related: [[internet-brutalism]] (inserts), [[kinetic-typography]], [[code-motion-showreels]],
[[tool-selection]], [[anti-slop]].
