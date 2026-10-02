# Brand DNA — where every token comes from

Three sources, measured rather than eyeballed. Re-measure when a source changes.

## 1. The Agent Work Index decks → the language (light mode, type roles, shapes)

Reference: the Agent Work Index companion deck (sensor patterns, 16 slides, made in Typst,
960 × 540 pt). Measured with PyMuPDF from the PDF's text spans and vector drawings:

| Role | Measured | Kit |
|---|---|---|
| Page | fill #fbfaf8 | `--s-bg` |
| Figure well | #efece6, radius 8 pt | `--s-well`, `.s-well` |
| Raised card | #fdfcfa, radius 5 / 3.6 pt, stroke #b9bcc2 0.8 pt | `--s-card` |
| Hairline | #e7e5e0, 0.5 pt (above How we counted) | `--s-line` |
| Diagram strokes, ticks, running footer | #b9bcc2, 0.9 pt | `--s-rule` |
| Non-key bars | #7f8186 | `--s-bar` |
| Titles, bold, code well | #15171c | `--s-ink` |
| Reading text | #6b6f78 | deepened to #63666f (see below) |
| Signal | #ff5a1f (eyebrows, stats, fired marks, key bars) | `--s-signal` |
| Small orange text | #e6511c / #d94d1a / #cc4819 / #bf4417 | `--s-signal-label`, `--s-signal-ink` |
| Fired box | fill #ffe1d7 + 1 pt #ff5a1f | `--s-signal-tint` |
| Normal range | #e9efe9 | `--s-calm-tint` |
| Code | bg #15171c, text #e9e7e2, ids #f4f2ee, keywords white bold, punctuation #a7abb3, strings #ff8a5c, numbers #ffc4a8, comments #7d818b italic | `--s-code-*` |

Geometry (pt): margins 68 · eyebrow top 51.5 · title 73.9–109.7 · lede 114.3 · body from 149.3 ·
card gutter 12.8 · rule bar 2.5 wide · hairline 458.8 · How we counted 475.2 · running footer 506.3.
Type (pt): cover 52 · title 30 · lede 13 (cover 15) · eyebrow 9 bold caps, tracked ≈0.18 em · card
title 11.5 · body 9.8 · card body 9 · counted 8.5 · footer 8 · stat 22 · rule 12 bold · labels 6.8 bold caps ·
code 6.6.

Slide grammar: eyebrow (where we are) → title (names the pattern) → lede (defines it) → a well with the
shape → the rule (imperative, orange bar) → one orange stat with its denominator → examples (bold lead-in)
→ a code sketch → How we counted → running footer. Every numeric slide discloses its method.

## 2. The Vex dashboard → dark mode, radii, motion

Source: `@vex/ui-theme/styles.css` (`:root` is dark, `.light` is light; the dashboard defaults to light).

| Dashboard token | Value | Kit dark token |
|---|---|---|
| `--bg` | #181818 | `--s-bg` |
| `--panel` | #212121 | `--s-well` |
| `--panel-2` | #2b2b2b | `--s-card` |
| `--sidebar` | #101010 | `--s-code-bg`, `--s-desk` |
| `--border` | rgb(255 255 255 / .09) | `--s-line`, code edge |
| `--text` / `--muted` | #dfdfdf / #aaaaaa | `--s-ink` / `--s-muted` |
| radii | chip 6 · control 8 · card 10 px | well 8u (10.7 px on a slide) · card 5–6u |
| `--ease-out-strong` | cubic-bezier(.23, 1, .32, 1) | `--s-ease` |

The signal orange is kept in dark (5.7:1 on #181818). Tints are 16% signal / 14% jade over the panel.
The dashboard's gemstone intents and plum accent are product UI; documents do not use them.

## 3. The logo → no background, framed at its own border

Source: `shift-labs-ai/assets` — `avatars/svg/original.svg`, `avatars/png/original.png` and 15 colourways
(`generate.sh`). Kept untouched in `assets/brand/official/`.

**Visual analysis of the official file** (rendered at 2048 px, measured by colour):
- The file is a 512×512 white square; the logo fills 45.4% of its width (20.4% of its area) and sits off-centre:
  white margins 162.9 left, 117.1 right, 130.7 top, 148.5 bottom.
- The logo's own frame is 232.0 × 232.75 (canvas units), nearly square (0.997). Its border is the **lip**
  (#CB8E97): 22 units deep along the bottom (the keycap's side), 2 on the right, a hairline on the left, and it
  rises into the top-right corner. Face #F4B7BC is 79.8% of the logo, lip 10.8%, arrow #1A2038 9.0%.

**Rule history (the principal, 2026-09-29).**
1. 1.0.0 cropped the keycap to a guessed viewBox, made it recolourable, and rebuilt a lockup and wordmark.
2. 03:31, "dont cut the original logo. it is as it is." 1.1.0 used the whole official square byte for byte.
3. 20:41, "keep only the logo without its white background… we do not use any white background." In 1.2.0 the
   white `<rect>` is removed and the frame is the logo's exact border, computed from the vector geometry (cubic
   extrema, stroke allowance, rounded outward), never guessed. The paths, colours and proportions stay byte-identical.
   The same trim is applied to all 16 colourways. Verified: the trimmed render touches all four edges, has
   transparent corners and no white pixels, and matches the official artwork (0.17% of pixels differ, all at
   antialiased edges).

Where it goes: page header (28 px high) and footer (22 px), deck cover (40 pt, top right), closing slide (64 pt).
Evidence kept, not used as a mark: the official lockup's "shift" wordmark is Inter Bold at −0.025 em (IoU 0.87),
which is why Inter sets the documents' type.

## Deliberate deviations (and why)

- **Inter instead of Helvetica Neue.** The decks are set in Helvetica Neue (Apple system font, not
  embeddable). Inter is the wordmark's own face, open (OFL), and renders the same on every machine and in
  headless verification. It runs ≈5% wider: slide ledes get 700 pt instead of 600 pt.
- **Muted #6b6f78 → #63666f.** The measured grey is 4.27:1 on the stone well; the deepened one passes AA
  (4.86:1) with no visible change.
- **Three orange text tiers.** #ff5a1f is 2.99:1 on paper, so text uses `--s-signal-label` (#e6511c, 3.6:1,
  bold caps labels and large numbers) or `--s-signal-ink` (#b33c10, ≥4.5:1 on paper and on the tint).
  Fills and marks keep #ff5a1f.
- **Bold caps labels may sit at 3:1.** Eyebrows and diagram labels are labels, not reading text (the decks do
  the same). shoot fails anything under 3:1 and warns on small reading text under 4.5:1.
- **DejaVu Sans Mono** for code: the open base of Menlo, which the decks use.
- **The logo appears in documents** (header, footer, cover, close). The source deck has none. The keycap
  alone, on no background, ties a publication to the brand without decorating it.
