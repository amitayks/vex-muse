---
kind: project
seen: 2026-09-26
---
# lab-motion-tools — reference study + engine tests (Sep 2026)
Brief: the principal sent four viral X videos (ajith_io, kenn, urieli17, shfred0 — all Claude Opus 5.5, all code, no video model) and asked me to break them into frames, learn how they are made and what the prompt must say, add SVG transformation, Remotion and HyperFrames to the studio, decide which tool wins when, test, and rewrite my resources to that level.

Worked: `framestudy.py` (timecoded sheets, transition strips, motion/beat curve, palettes) turned each video into numbers — 128 BPM bar grid, 22–29 % holds, half-beat accelerando, motif-as-transition; the GPT contrast measured as fixed-clock slides. HyperFrames renders 8.1 s of 1080p30 in 31 s here (draft); Remotion 38 s for 4.2 s incl. bundle; VP9-alpha Remotion layers composite correctly in HyperFrames; GSAP MorphSVG and flubber beat naive / `@remotion/paths` on hard morph pairs. The combo (Seedance plate seen through a morphing spark mask + Remotion alpha lyrics + HyperFrames comp) works end to end.

Didn't / lessons: text rendered invisible until fonts were registered from bytes (URL font loads fail on this box); `clip-path:url()` blanked the plate (CSS `path()` per frame works); GSAP `fromTo` pre-roll ghosts; Studio writes ids into HTML. Cream lyrics over the tan plate lost contrast (needs a designed text zone). All folded into `code-motion`, `svg-transform`, `kinetic-lyrics` LEARNINGS.

## Follow-up 1 — originality (the principal, same day)
- **His question:** would new videos just echo these recent references instead of having their own taste?
- **Answer:** partly yes, at that point. The lab reel and the `code-motion` reel template had copied the trend's look (red dot motif, vermilion/cobalt/cream palette, grotesk + italic-serif + mono HUD, dot-as-full-stop).
- **Fix:**
  - The method now splits portable craft (beat grid, holds, one read at a time, motif as transition, ending rhymes) from the trend fingerprint (never a default, at most one item per piece, only with a reason from the song). See [[code-motion-showreels]] and [[anti-slop]] (trend echo).
  - `style-bible` gained a Diverge-first gate: 3 song-derived directions + 1 wild card before opening the reference library.
  - The reel template counts as mechanics only; every visual in it is the study replica and gets replaced.
  - The half-beat accelerando is now an option, not a rule.
- **Implication:** the lab reel is a *replica for study*, not a Muse style sample.

## Follow-up 2 — whatships.com + the tesseract (the principal, same day)
- **His asks:** (1) use whatships.com ("good for quick review on new video creations") as a reference source; (2) study the tesseract — he didn't know where it belonged in the skills but thought understanding it would give better results.
- **Outcome:**
  - whatships became a standing source, read from its public GitHub repo because the site 403s this box — `whatships.py`, wired into research (`reference-mesh` 1.3.0), the divergence gate's "what's shipping now" wall (`style-bible` 1.3.0) and a quick comparison in every review (`render-review` 1.4.0). See [[whatships]].
  - The tesseract entered as technique and as a planning rule, not as a look. Inside-out turns and slices went into `svg-transform` 1.1.0 (module `assets/nd4.js`). "One invariant, many projections" and the Flatland reveal went into `storyboard` 1.3.0. "A video is a 4D object" was judged too thin to add. See [[tesseract]].
- **Worked:** `nd4.js` unit-tested (16/32/24/8, 90° self-maps, slice shapes). Two 8.1 s HyperFrames tests rendered in 32–33 s each (draft): `renders/tesseract_turn_v2.mp4` and `renders/tesseract_slice_v2.mp4`.
- **Didn't / lessons:**
  - Beat snapshots passed, but the mid-turn swing crossed the caption; only the frame study caught it. `code-motion` 1.2.0 now measures a moving object's screen envelope over every frame before placing text.
  - The octahedron beat showed only 2 faces. A numeric search picked a camera angle that shows the 4-face checker.
  - v1 used cobalt/orange on cream, the very fingerprint written down an hour earlier. Test pieces now get an off-fingerprint palette too (v2: sage/ink/riso pink).
  - A later stranger watch found both films fail phone legibility: captions too small, and the object sits small in an empty frame.
- **Delivery:** the plain-language report `outbox/tesseract-whatships-study.md` and both MP4s went to the principal's web chat. A completion summary went to the WhatsApp session "Muse // the principal". The work is filed as a spine decision on `muse-studio` (ref `file:1756`).
- **Spend:** $0.

## Follow-up 3: Mirage's Tesseract engine (the principal, same evening)
- **His asks:**
  - First, *without editing anything*: does Mirage's "Opus 5.5 + Tesseract" post, site or skill
    add tools or understanding?
  - Then: run the test and send it. Points go into the skills only after he decides, and only if
    genuinely helpful.
- **Answer:**
  - No new understanding of the tesseract; the name is branding.
  - It is a real new tool: a local After-Effects-like engine for agents.
- **Test:** the 8 s "turn" piece was ported exactly, in an isolated `/tmp` install with telemetry
  off. The picture matched (0.79 % of pixels differ), but it was 2.2× slower (74 s vs 33 s).
  v0.2.0 gotchas included a silent export failure from one throwing script and opacity units that
  contradict the docs. **Not adopted.** Details are in [[mirage-tesseract]].
- **Method points:** of the three in Mirage's docs, only eye-line continuity across performance
  cuts was proposed, as one line in the render-review cut check. The principal approved that point only
  ("Great report, add the eye line only"). It is now in `render-review` 1.5.0 (seams step), and the
  other two stay out. The approval is filed as a spine decision on `muse-studio`.
- **Files and filing:**
  - `renders/tesseract_turn_tsrct_v3.mp4` and `renders/engine_compare_hf_vs_tsrct.mp4`
  - `tsrct-test/`
  - report `outbox/tesseract-engine-test.md`
  - a spine status encounter on `muse-studio`
- **Spend:** $0.

## How the principal works with this
- **Plain words.** He is not a video person and doesn't follow editing terminology. He wants findings in plain words: the first study reached him as a 6-page PDF with a glossary, the second as a plain-language markdown report.
- **Originality over imitation.** He holds the studio to its own taste rather than copying references.
- **Ideas as hunches.** He brings ideas as hunches ("I don't know where it belongs, but it's important"). The job is to test each one and keep only what holds, not to force it in.
- **Skills stay lean.** He does not want the skills "dirtied with too much info that eventually becomes garbage". When he asks "does this help?", answer and test first, recommend the few points that earn a place (with the reason the rest are duplicates), and change skills only after his explicit go.
- **Routing.** Research asks arrive in the WhatsApp session, which opens a fresh autonomous web session with a full brief. That session delivers files to his web chat and reports completion back to WhatsApp with `vex.sessions.messages.prompt`.

## Outputs
Spend across the whole lab: $0. There was no paid generation; the combo reused the pdoom S1 plate.
- **Renders:**
  - `renders/hf_test_v3.mp4` (lab reel)
  - `renders/combo_v1.mp4`
  - `renders/rm_test_v1.mp4`
  - `renders/tesseract_turn_v2.mp4`
  - `renders/tesseract_slice_v2.mp4`
- **Other files:**
  - `morphlab/morph_compare.png`
  - sources in `tesseract-src/` (`build.sh turn|slice`)
- **References:** [[code-motion-showreels]], [[tool-selection]], [[svg-transformation]], [[whatships]], [[tesseract]].
- **Skills changed in the first pass:**
  - `code-motion` and `svg-transform` (both new)
  - mv-director 1.1, storyboard 1.1, style-bible 1.1, kinetic-lyrics 1.1
  - render-review 1.2, reference-mesh 1.2, p5-paper-engine 1.1, rotoscope-paint 1.1
- **Skill versions after follow-up 2:** reference-mesh 1.3.0, style-bible 1.3.0, render-review 1.4.0, svg-transform 1.1.0, storyboard 1.3.0, code-motion 1.2.0.
- **After follow-up 3:** render-review 1.5.0 (eye-line check).
