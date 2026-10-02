---
name: shift-labs-design
description: Make every Shift Labs (makers of Vex) deck, report, research note, dashboard or figure on-brand, honest and decision-ready - the Agent Work Index editorial look (warm paper, Inter, one signal orange, stone wells, "How we counted") in light paper and Vex-dashboard dark charcoal, the Shift keycap logo on no background, and Dio's decision-ready method (decision first, metric contracts, matched comparisons, variance decomposition, evidence ladder, chart by job, action gates, visible trust). One self-contained HTML file (a 16:9 deck printing to 960x540 pt PDF, or a responsive page) from a kit of tokens, components and fifteen JSON shapes, enforced by build, lint and shoot. Use whenever an agent makes anything a person will read for or about Shift Labs, Vex or the Agent Work Index - research decks, findings, weekly or metric reviews, briefs, diagrams, figures for posts - or is asked to make something "look like Shift Labs", support dark and light mode like the Vex dashboard, or make a report decision-ready.
license: MIT
metadata:
  author: muse
  version: "1.4.0"
---

# shift-labs-design

Three jobs, one file: it must look like the Agent Work Index decks (warm paper, ink type, simple shapes,
**one orange that marks the thing that happened**), every number in it must say how it was counted, and a
document that supports a decision must be a governed argument, not a decorated dataset (Dio's method).
It works in light (paper) and dark (the Vex dashboard's charcoal) from one set of tokens.
Human-facing version: `assets/book/shift-labs-brand-book.html`. Depth: `references/`.

## The law

1. **Form.** One self-contained `.html` built with `scripts/build.py`: a **deck** (`<body class="s-deck">`,
   prints to one 960×540 pt PDF page per slide) or a **page** (`<body class="s-page">`: report, note,
   one-pager). A single figure ships as PNG via `shoot.mjs --figures`. PDF = the printed deck.
2. **Two modes.** `<html data-theme="light|dark">`; the reader toggles, `?theme=dark` renders dark.
   Both modes must pass shoot. Never hard-code a mode-specific colour.
3. **Tokens only.** Colours `var(--s-*)`, fonts `var(--s-f-*)`. Any raw colour or font outside the kit fails lint.
4. **Orange is a signal.** It marks what fired, the key bar, the eyebrow, and one number per slide
   (`.s-stat.is-signal`). Everything else is grey or ink. No rainbow palettes, no gradients, no shadows inside a doc.
5. **The logo: no background, its own border.** `assets/brand/logo.svg` is the official keycap artwork with only
   its white 512×512 background removed, framed at its own border (the lip's outer edge) by `scripts/trim_logo.py`
   from the untouched `official/original.svg` (paths byte-identical). Place it with
   `<img data-brand="logo" class="s-logo" alt="Shift Labs">` in the page header and footer and on the deck cover and
   close; size by height only (≥ 16 px), a quarter of its width clear. Never put it on a white tile; never recolour,
   redraw, crop, round, mask, rotate or stretch it, or build a lockup. build pins the bytes, lint checks the hash,
   shoot checks it renders whole and not on white. Colourways (`data-brand="avatar-<way>"`) are for avatars only.
6. **Numbers say how they were counted.** Every slide with a number carries `.s-counted`; a page carries
   `.s-counted`, `.s-method` or `.s-trust`. `<html data-mode="published|snapshot|live|sample|synthetic">` on any doc
   with numbers. Too few cases prints n/a, never a guess.
7. **Claims carry their evidence.** Every doc starts from `<!-- job: reader, decision -->`. Causal, attribution,
   profitability and record claims carry an evidence level (`.s-claim` / `data-evidence`). A doc whose job is a
   decision is a **report** (`<html data-doc="report">`) and carries the full contract below.
8. **Done** = `lint.py` 0 errors + `shoot.mjs` pass in light, dark and reduced motion + you looked at every slide
   or slice + (reports) the five final questions answer yes.

## Tokens

| Token | Light (paper) | Dark (dashboard) | Role |
|---|---|---|---|
| `--s-bg` | #fbfaf8 | #181818 | page |
| `--s-well` | #efece6 | #212121 | figure wells, cards |
| `--s-card` | #fdfcfa | #2b2b2b | boxes inside a well |
| `--s-line` / `--s-rule` | #e7e5e0 / #b9bcc2 | 9% white / #5d6066 | hairlines / ticks, strokes, outlines |
| `--s-bar` | #7f8186 | #9a9da4 | non-key bars |
| `--s-muted` / `--s-ink` | #63666f / #15171c | #aaaaaa / #dfdfdf | reading text / titles, bold |
| `--s-signal` | #ff5a1f | #ff5a1f | marks, key bars, rules, large numbers |
| `--s-signal-label` / `--s-signal-ink` | #e6511c / #b33c10 | #ff6a33 / #ff8a5c | caps labels (≥3:1) / small orange text (≥4.5:1) |
| `--s-signal-tint` / `--s-calm-tint` | #ffe1d7 / #e9efe9 | #442a21 / #293532 | the box that fired / a normal range |
| `--s-code-*` | ink well, white keywords, orange strings | #101010 well | code sketches |

Radii follow the dashboard: well 8u (10 px), card 5–6u, marks 3.5u. The logo carries its own colours and no background; no token touches it.

## Type

Inter (the wordmark's face) as `--s-f-display` (titles) and `--s-f-sans`; DejaVu Sans Mono as `--s-f-mono`.
All embedded by build. Sizes are deck points (1u = 1pt on a slide; a page scales u and floors text at 12 px):

cover title 52 · title 30 (−0.022em) · eyebrow 9 caps +0.18em signal · lede 13 muted (bold = ink) ·
card title 11.5 · body 9.8 · small 9 · counted 8.5 · note 8 · stat 22 · rule 12 bold · label 6.8 caps ·
code 6.6. Sentence case in source; the kit sets caps. No emoji; glyphs outside the fonts fail lint (no Δ: write "Change").

## Deck anatomy (copy `assets/templates/deck.src.html`)

```
body.s-deck[data-runfoot="Publication · Month Year"]      running footer + page number on every slide
section.s-slide.is-cover   logo · .s-eyebrow · h1.s-title.is-cover · .s-lede.is-cover · .s-slide__foot (ticks + caption)
section.s-slide            header.s-slide__head (eyebrow · h2.s-title · lede)
                           .s-slide__body[.is-split | .is-split-even | .is-3 | .is-4]
                             left .s-slide__col: .s-well (shape) · .s-rule · .s-stat.is-signal
                             right .s-slide__col: .s-kicker · ol.s-examples · pre.s-code
                           p.s-counted          ("How we counted." is added by the kit)
section.s-slide.is-close   logo · one-sentence takeaway · eyebrow
```
Margins 68 pt; eyebrow at 51.5 pt; body from ~149 pt; the counted rule at 458.8 pt; footer at 506 pt.
Content that crosses the counted rule fails shoot: cut words, not type size. A report deck puts the data mode in
the running footer (automatic with `data-doc="report"`).

## Page anatomy (copy `assets/templates/page.src.html`; a report: `report.src.html`)

`header.s-head` (logo · `.s-head__brand` · doc name · `.s-mode` · `[data-theme-toggle]`) → `section.s-hero` (eyebrow, one `h1`,
lede, `.s-stats`) → `section.s-sec` blocks (`.s-sec__head`, then wells, `.s-split`, `.s-cards`) → a Method section
(`.s-method` dl + `.s-counted`) → `footer.s-foot` (logo, publication, source). `.s-embed > .s-slide`
shows a real slide inside a page. A report runs: hero (h1 = the material movement, KPI band, `dl.s-brief`) →
`section[data-part]` movement → drivers → exposure → claims → decisions → evidence (`.s-trust` + contracts).

## Components

`.s-well` (`.is-card` for the raised tone) · `.s-card` (`__head`, `__title`, `__meta`, `__body`, `__art`) · `.s-cards`
(`--cols`) · `.s-rule` · `.s-stat` / `.s-stats` · `ol.s-examples` (bold lead-in, grey numerals, `start` works) ·
`pre.s-code` (JS highlighted; `data-lang="text"` to skip; `data-spec-of="id"` prints a shape's JSON) · `.s-log`
(`.is-sig`, `.is-faint`) · `.s-label` · `.s-tag` · `.s-kicker` · `.s-note` · `.s-caption` · `.s-counted`
(`data-lead` renames the lead) · `.s-mode` · `.s-method` · `.s-fig-head` (h3 metric title + `.s-small` reading).
Decision-ready: `.s-vs` · `dl.s-brief` · `span.s-claim[data-evidence]` (the kit fills pips and level) ·
`.s-decisions > article.s-decision[data-kind]` (`.is-signal` = the one asked for now) · `.s-trust` · `.s-table`
(scroll box) `> table.s-tab` · `table.s-ledger` · `table.s-contract` · `details.s-more`. Markup: `report.src.html`.

## Shapes (full specs: `references/shapes.md`)

`<figure class="s-shape" data-shape="NAME" data-figure="id"><script type="application/json">{…}</script></figure>`

| Shape | Job | Key fields |
|---|---|---|
| `ticks` | runs over time; fired runs ringed; `style:"check"` = ✓/✗ probes | `runs` ("..1.."), `notes[{at,text,mark,row}]` |
| `axis` | reminders, a deadline window, a day | `points[{label,kind,size,above}]`, `scale`, `domain`, `spans`, `lines`, `ticks`, `dotted` |
| `line` | a value over time (`band`: out-of-range turns orange); trend of related series | `values`, `band`, `x`, `axis`, `points`, `series[{name,tone,values}]` |
| `shares` | ranked categories (horizontal), one key bar, null = n/a | `rows[[label,value]]`, `key`, `total`, `unit` |
| `columns` | a few periods, zero-based, beside the matched prior | `x`, `series[{name,values,role:"prior"}]`, `key` |
| `variance` | contribution to a change; parts reconcile to the total | `rows[[label,from,to]]`, `total` |
| `tablegraph` | exact breakdown with movement (never a pie) | `rows[[label,value,prior]]`, `labelHead`, `valueLabel` |
| `bullet` | actual against target | `rows[{label,value,target,band,max,better}]` |
| `heatmap` | two ordered dimensions (day × hour); orange at the threshold | `rows`, `cols`, `values`, `threshold` |
| `flow` | sources → code → store → event → agent → outcome | `steps[{kind,label,items,code,text,tag,else,note}]` |
| `queue` | a list with a cursor; items after it fire | `seen`, `fresh`, `cursor`, `note`, `result` |
| `diff` | last look vs this look; changes orange | `before{label,rows}`, `after{…}` |
| `match` | two systems that should agree | `left{label,rows}`, `right{…}` (null = missing) |
| `stairs` | stages that take on more | `steps[[title,sub]]`, `active`, `rise` |
| `fanout` | one thing split or copied | `from`, `to[]`, `cols`, `tone:"signal"` |

Data shapes take `"reconcile":"key"`: their values must sum to the element with `data-total="key" data-v="N"`.
Operational exceptions are a table or the decision queue, not a chart.
Connected parts share one centre line: labels above and notes below never shift the body (shapes are built on
label · body · note grid rows). No shape fits → draw inline SVG with the `k-*` classes (`k-line`, `k-sig`, `k-fill-tint`, `k-t-cap is-sig`…) so both
modes still work. Never add a chart library, pie, donut, stacked bars or areas, smoothed lines or 3D.

## Voice

Simplified technical English: short present-tense sentences, one idea each, the same term every time
(define it once). **Titles name the thing** ("New items"); a chart title names the metric ("Agent turns by day")
and the reading goes in its subtitle; a report h1 may state a finding only when the number beside it proves it.
The rule is an instruction ("Keep a cursor and fire only for items after it."). A stat is a
number plus its denominator in words ("of sensors fire on new items"). Examples are real, paraphrased, anonymous.
No hype words, no exclamation marks, no emoji.

## Honest numbers (depth: `references/method.md`)

Every number: a unit and a denominator in words · How we counted (unit, source, weighting, exclusions, coding
check) · suppression shown as n/a · visible rounding (whole % in decks; say when shares miss 100; "about" when
rounded in prose) · derived values carry `data-calc="(a-b)/b*100"` (lint recomputes at the shown precision) ·
`data-mode` states what the data is, and sample or synthetic data is labelled in every header and deck footer by the kit.

## Decision-ready (Dio's method; depth: `references/decision-method.md`)

decision → metric contract → data QA → metric validation → matched comparison → decomposition → evidence
ladder → chart by job → action gate → visible trust → artifact QA.

1. **Decision first.** The job names reader, decision and what changes it. The first screen (`dl.s-brief`)
   answers: changed · material · drivers · risk · decision · missing. Evidence sits one level below, never gone.
2. **Metric contract** per KPI (`tr[data-metric]` in `table.s-contract`): meaning · source · grain · calculation ·
   exclusions · comparison · owner · action. Two reasonable people could compute it differently = not defined.
3. **Data QA ≠ metric validation.** QA: fresh, complete, no duplicates or unknowns, lower grain reconciles to
   higher. Validation: definition, denominator, grain, window, no proxy taken for an outcome.
4. **Matched comparison.** Every KPI has `.s-vs` (matched prior, plan, target, SLA). A complete period is never
   compared with an incomplete one silently; an uncaptured cutoff says "Not captured".
5. **Decompose the change** by contribution, not size (`variance`, `tablegraph`), reconciled exactly. "A made two
   thirds of the rise" is arithmetic; "X caused it" needs its own evidence. Keep them apart.
6. **Evidence ladder**: confirmed · likely · suspected · correlated, not causal · unknown. Claims the source cannot
   settle move to `table.s-ledger` with what would settle them: data requests, not deletions.
7. **Chart by job**: per visual, its job, the fit, what it can and cannot prove, which required chart is missing.
8. **Action gates** (`article.s-decision`): kind (approve · investigate · defer · reject · act), evidence, missing,
   owner, review, status, source. Costly or irreversible with evidence missing → investigate: learning before
   intervention.
9. **Visible trust** (`.s-trust`): mode · source · generated · period · cutoff · qa · definitions · scope · caveats;
   a gap says "Not captured". Never look more authoritative than the source.

Seniority changes depth, never metric truth. Examples here are placeholders or synthetic; never copy a client's
figures, names or partners into this skill.

## Workflow

1. Write the job as `<!-- job: reader, decision, what changes it -->` under `<title>`. If it names a decision,
   the doc is a report: reconstruct the decision, the metric contracts and the comparisons before any chart.
2. Pick the form: deck (presented, paged), page (read, scrolled, phone) or report (`report.src.html`). Copy the
   template to a work dir as `<slug>.src.html`; rewrite every text and number; delete what you do not need.
3. One idea per slide or section: choose the shape by job (table above); keep one orange number.
4. `python3 scripts/build.py <slug>.src.html` → `<slug>.html` (fonts, kit, the original logo and favicon inlined).
5. `python3 scripts/lint.py <slug>.html` — fix every error, justify every warning.
6. `node scripts/shoot.mjs <slug>.html [--pdf] [--pdf-dark] [--figures]` — light and dark; decks: every slide at
   1920×1080 + contact sheets + PDF; pages: phone and desktop slices; every doc: a reduced-motion pass; reports:
   the brief inside the first desktop screen. Needs puppeteer-core and `$CHROME_PATH`.
7. Look at every sheet and slice in both modes. Deliver the built `.html` (and the PDF for decks) with one line:
   what it is for (a report: the decision it supports). A check you could not run is reported as not run.
8. Changed `lint.py`, the kit or `report.src.html`? Run `python3 scripts/lint_selftest.py`: the clean report must
   pass and every planted fault must be caught.

## Acceptance — the gate (all yes)

- Next to an Agent Work Index deck, do the same hands seem to have made it — in light and in dark?
- Can the reader say what each slide is about from its title and rule alone?
- Is orange on the one thing that happened, and nowhere decorative?
- Is the logo the untouched artwork, with no background behind it, wherever it appears?
- Does every number have a denominator in words and a How we counted?
- Is anything clipped, crossing the counted rule, overlapping, or under 12 px on a phone? (shoot says no)
- Does every connected part sit on one centre line: arrows meet boxes at their middles, ≠ and links on their rows? (shoot checks ±1 px, and you look)
- Reports: can the reader state the headline in 10 seconds? See what moved it without another analysis? Trace every
  material claim to visible evidence? Tell action from investigation? Would it stay honest if its most attractive
  story turned out false?
- Lint 0 errors; shoot `pass: true` in both modes and reduced motion; you looked.

## Files

```
assets/kit/shift.css · shift.js       tokens (light/dark), frames, components, shapes (window.SL)
assets/fonts/                          Inter (OFL) + DejaVu Sans Mono, subset woff2 · coverage.json for lint
assets/brand/                          logo.svg + logo.png (no background, own border) · avatars/ (16, trimmed) ·
                                       official/ (untouched sources) · PINS.json (hashes)
assets/templates/deck.src.html         the reference deck (15 slides, the explanatory shapes) — copy it
assets/templates/page.src.html         the reference research note — copy it
assets/templates/report.src.html       the reference decision-ready report (synthetic data, every data shape) — copy it
assets/book/                           brand book (source + built)
scripts/build.py · lint.py · shoot.mjs build → lint → look (stdlib Python; node + puppeteer-core)
scripts/lint_selftest.py               plants method faults into the report; lint must catch every one
scripts/trim_logo.py                   official avatar → background removed, framed at its border
references/brand-dna.md · shapes.md · method.md · decision-method.md
```

Corrections go to `LEARNINGS.md` the same day, as one line of intent.
