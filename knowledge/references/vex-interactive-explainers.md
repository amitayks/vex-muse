---
kind: technique
tags: [interactive-html, explainer, svg, generators, vex, onboarding]
audience: non-technical readers learning a system one idea at a time
half_life: 180
rights: Vex's own pages. Study the mechanics; do not copy the look.
seen: 2026-09-27
---
# Vex "meet them" explainers: the interactive single-file HTML pattern


## Why / Context

## Details
**Files.** They sit in `inbox/2026-09-27/`. There are nine tours: actions, artifacts, channels + sessions, data, factory, knowledge, schedules, sensors and team. Each is 480–700 lines (27–40 KB). They share a rig, `vexel-rig.js`, which arrived as `vexel-rig-9e6db8.js`. The pages load `<script src="vexel-rig.js">`, so copy it under that name next to them before running.

**Page anatomy**
1. A dimmed fake dashboard (sidebar and skeleton bars) sits behind a blurred scrim.
2. An 800 px modal is centred and scaled to fit: `--fit = min(1, (innerWidth-24)/800, (innerHeight-24)/560)`.
3. The head has an eyebrow ("Introduction to sensors", 11.5 px uppercase, .08em tracking, muted) and an h2 that is the whole thesis in one or two sentences. For example: "A sensor monitors a system. It sends a task to your agent only when the system changes."
4. The stage is a 760×340 SVG scene.
5. The lesson card pops in with opacity plus a translateY on an overshoot ease, `cubic-bezier(.2,1.3,.4,1)`. It has a step kicker, a bold title and a 13.5 px body.
6. The ending is a centred, closable card with the SUMMARY and every lesson ticked ✓.
7. The footer has "End the tour", a copy-paste prompt ("Send this message to your agent: *'Create a sensor for refund emails in Gmail.'*") and Close.

**Content model.** Each lesson is `const LESSONS = [[title, body], …]`, 5–6 per page, and each page ends with `const SUMMARY = '…'`.
- **Title:** one short declarative rule ("After 5 errors, the sensor stops.").
- **Body:** 2–3 short present-tense sentences in simplified technical English, one idea per sentence, addressed to "your agent".
- **Summary:** a single memorable line ("A sensor watches, so your agent does not have to.").

**The rig.**
- **Loading.** `vexel-rig.js` is a classic script that works from `file://`. It exposes `window.VexelRig` = `{createWorld, C, el, rand, pick, clamp, lerp, ease, wait, waitUntil, arrow, …}`.
- **Coordinates.** SVG user units equal CSS px (no viewBox), so `getCTM()` on a hand anchor gives world positions directly.
- **Layers:** `back`, `floor`, `props`, `chars`, `front`, `fx`.
- **Boil.** Hand-drawn wobble comes from `feTurbulence` (fractalNoise, baseFrequency .045, 2 octaves) into `feDisplacementMap` (scale 2.2). The seed cycles 1→3 about every 110 ms, and ground lines re-jitter on each tick.
- **Characters ("vexels").** Each has moods (neutral, sly, happy, surprised) built from eyelid, tilt and mouth paths, plus the moves `walkTo`, `hopTo` and `hold`. The reader can drag and poke them (grab cursor).

**Director as generators.** Every behaviour is a generator where `yield` returns dt:
- `yield* wait(s)` pauses for s seconds.
- `yield* waitUntil(fn)` pauses until a condition is true.
- `on(name)` waits for an event counter to change.
- `setBrain(v, task(v, script(v)))` assigns a script to a character, and a default idle brain takes over when the script ends.

The scene *performs* each lesson: a ticket flies to the bin, the sentry switches off after 5 failures. The director is one generator stepped from the frame loop, so a lesson reads top to bottom like a screenplay. "End the tour" calls `gen.return()` and then `finish()`. After the summary card the scene stays a free-play sandbox.

**Guided attention.**
- A spotlight `focus()`es a target: fog from an SVG mask with a blurred hole, plus a dashed, rotating, pulsing ring. When it asks for a click, the tour waits for the reader to click the lit item. A click elsewhere gets a gentle "not yet" pulse.
- Pointer arrows are hand-drawn: a quadratic curve that bows up to 16 px, with the head built from the curve's real tangent at the tip so it lands on the ring edge aimed at its centre.

**Look (Vex's, not to copy).**
- **Palette:** INK `#241b2b`, BODY `#31263b`, ROSE `#f5c0c0`, RED `#d6453d`, ORANGE `#e98a2e`, BLUE `#3d6fc4`, MUTED `#8f8796`, lines `#ece8ef`.
- **Type:** Inter 400/500/600 for the UI. Patrick Hand for scene labels, with a white halo (`paint-order: stroke; stroke:#fff; stroke-width:4px`).
- **Font loading:** the fonts come from Google Fonts. Rendered on this box they need `FontFace(ArrayBuffer)` registration ([[tool-selection]]).

**Language.** The body copy follows ASD-STE100 Simplified Technical English: short sentences, one idea each, the same term every time, active voice. The Hebrew equivalent is short, present tense, with one term per concept.

**As built in a brand kit:**
- Authors mark up to 6 elements with `data-tour="n" data-tour-title data-tour-body`.
- An optional `data-tour-ask` makes the reader click the lit target to continue.
- The look: a petrol spotlight, butter step cards, a closing summary card with ticks, and a floating pink launch circle.
- Everything stays readable with zero clicks.

**What transfers to a branded doc:**
- one thesis
- 5–6 rule-shaped lessons, each acted out on stage
- a closing summary card
- the fit-to-viewport modal or stage
- a generator director
- boiled hand-drawn marks
- spotlight-plus-arrow attention
- plain short sentences
