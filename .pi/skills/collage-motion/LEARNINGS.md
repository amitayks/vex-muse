# LEARNINGS — collage-motion

- 2026-09-26 Bria background removal treats a busy full-frame photo as all foreground (97 % kept): for a subject inside a scene use SAM 3 with a text prompt (`--matte sam:person`), Bria only for isolated objects.
- 2026-09-26 A subject layer must share the print's geometry exactly: same source, same --inset/--max, `--notrim` on the cut, same box and same entrance in the comp — then the date sits between room and person.
- 2026-09-26 Text split into inline-block spans loses `\n` in `white-space:pre` blocks: emit a `<br>` for newlines.
- 2026-09-26 A pen stroke with round caps hidden by dashoffset still paints its cap as a dot: keep it `visibility:hidden` until its draw starts.
- 2026-09-26 Page chrome (progress row, header) placed outside the page wrapper showed on frame 0 before its page arrived: enter chrome with the page.
- 2026-09-26 A shadow wrapper of size 0 collapses any `inset`/`right` child to nothing: give wrappers the element's real box.
- 2026-09-26 HyperFrames lint: initial hides via `tl.set(..., 0)` do not render at t=0 — hide with `gsap.set` outside the timeline, then `tl.set` later states.
- 2026-09-26 Tape laid on a hero's top corner crossed the headline above it: check every tape/arrow envelope against the headline and caption glyph boxes.
- 2026-09-26 Torn polygons with a fixed % step turned a 60 px strip end into a sawtooth and left spikes at corners: sample each edge per ~9 px of its measured size and make corners shared points at both edges' depth.
- 2026-09-26 Rays and cassette clones placed after the headline in DOM order cut through its glyphs: headline and caption go last in the chapter stack.
- 2026-09-26 A chapter's last stickers and caption built right up to the peel, so the caption finished typing 0.1 s before the page left: schedule the caption's end (start + chars/cps), not its start, at least 1 beat and 0.9 s before the transition.
