---
name: scene-writing
description: Write a short film scene (15-120 s of screen time) that plays as real life, not theatre - a premise with stakes, characters who talk TO EACH OTHER (interruptions, half-lines, reactions, off-screen answers, intercom/radio), two-speed pace (fast action or slow held events, never a purposeless middle), and a coverage plan (shot sizes, eye-lines, who is on screen while someone else speaks, sound perspective) that current AI video can actually produce. Use for every film, teaser or trailer script, for the writers' room station of a crew line, or when dialogue in a cut feels recited.
license: MIT
metadata:
  author: muse
  version: "1.1.0"
---

# scene-writing — people talking, things happening

## Shape (write in this order)
1. **Premise in two lines:** who wants what, what is at risk now, what stops them.
2. **Beat sheet:** 5–12 beats, each one read (cause → reaction), each marked **FAST** (action, cut
   0.3–1 s) or **SLOW** (held event, talk, dread, 2–5 s). No beat is "medium".
3. **Scene:** screenplay format. Time it: talk at ~2.5 words/s, action beats at their shot length. The total
   must fit the runtime within 10 %.
4. **Design list:** every machine, building, place, product, kit and procedure the viewer sees or hears,
   each with the specialist who must design it for real (crew skill, 'Everything on screen is real').
5. **Coverage table:** `beat · shot size · camera (mounted/locked/handheld; speed) · who is on screen ·
   who is heard (on/off/intercom/radio) · eye-line direction · sound perspective`.

## Dialogue that sounds real
- People answer each other, not the audience. Nobody explains the plot or their feelings in full sentences.
- Under pressure people speak in fragments, repeat a word, overlap, get cut off, go quiet. Write overlaps as
  `(over)` and cut-offs with `—`.
- Give every line a listener and a reaction. Show the listener at least as often as the speaker.
- Put some lines off-screen, on intercom or on radio, so the picture can stay on a face or on the action.
- Use procedure and jargon of the world for texture: callouts, numbers, names, checklists.
- One person never speaks more than ~8 s without a cut to someone else or to the thing they see.

## Writing for the models we have
- Prefer shots AI video does well in 1–4 s: faces reacting, mounted cameras with vibration, subjects
  crossing frame fast, weather, smoke, motion blur, silhouettes. Avoid long takes of acting, fine hand
  work, readable text, close crowds.
- Every on-camera line ≤ ~3 s; longer speech carries over cutaways.
- Keep the cast small (2–4 speaking roles) and give each one a silhouette or costume tag that reads at
  phone size.

## Acceptance
`scripts/<name>.md` has the premise, the FAST/SLOW beat sheet, the scene with timings summing to the
runtime ±10 %, the design list and the coverage table; no speaker runs > 8 s uncut; every line has a listener; it is
original (no named film or series copied). The crew critic rubric (`crew/references/rubrics/script.md`) is
the external check.
