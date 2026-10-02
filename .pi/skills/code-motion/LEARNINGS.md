# LEARNINGS — code-motion

- 2026-09-26 Chrome on this box fails URL font loads (NetworkError, even data: URIs) and has no system fonts: register every face from bytes (FontFace(ArrayBuffer)) or text renders blank.
- 2026-09-26 HyperFrames workers seek frames in parallel: a timeline built inside fonts.ready leaves early frames at CSS initial state — register synchronously.
- 2026-09-26 GSAP fromTo pre-renders its from-state before its start time when seeked (flash at full opacity from frame 0, shockwave blob): drive custom effects as pure functions of t from one proxy tween.
- 2026-09-26 clip-path:url(#svgClipPath) on a wrapper around a <video> blanked the plate in capture; a CSS path() rebuilt per frame works.
- 2026-09-26 HyperFrames preview writes data-hf-id into project HTML and lint errors on two root compositions in one dir: keep sources in <comp>-src/, build in.
- 2026-09-26 A dot that floats for a bar before landing reads floaty: bring the motif back for ONE beat and land it on the downbeat.
- 2026-09-26 mix-blend-mode:difference on HUD text turns it cyan on red fields: set the HUD colour per field instead.
- 2026-09-26 Tweening fill between flat inks passes through mud (red→blue = purple): switch fill hard at the morph midpoint.
- 2026-09-26 The template/brief had hard-coded the studied trend's look as defaults: principles are portable, looks are not — keep templates as mechanics only.
- 2026-09-26 Beat snapshots passed but the turn's mid-motion swing crossed the caption at 6.5 s (found only in the frame study): measure a moving object's envelope over every frame before placing text.
- 2026-09-27 HyperFrames' runtime executes external `<script src>` files before the body exists (validate: "Cannot read properties of null (reading 'appendChild')"), while direct Chrome runs them fine: keep DOM-building code inline at the end of body (inline it at build time) and register the timeline in that same script (lint wants create + register together).
- 2026-09-27 `mix-blend-mode:multiply` on images inside a transformed camera div blends only inside the camera's stacking context (white paper showed as a light box): put the blend on the camera group itself so it multiplies onto the page.
- 2026-09-27 When a snapshot is blank but the page renders in plain Chrome, run `hyperframes validate/check` first — it reports runtime JS errors the snapshot hides.
- 2026-09-27 Word-by-word caption spans with `white-space:pre` and the space inside the span leave no break opportunity: the line never wraps and runs off-frame. Keep words `nowrap` and put the space as a text node between spans.
- 2026-09-27 A dark scene whose camera group multiplies onto a dark page turns every drawing black: multiply the camera only onto light pages.
- 2026-09-27 `hyperframes snapshot` took ~40 s/frame on a 5-min comp; a puppeteer seek of the built index.html (tl.seek + screenshot) took ~0.6 s/frame and matched — use it for review sweeps, snapshot/check for the gate.
- 2026-09-27 Old-style display fonts (IM Fell) have no Greek: any non-Latin line needs a face that covers it (EB Garamond) or it renders tofu.
