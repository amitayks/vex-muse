---
kind: project
seen: 2026-10-06
tags: [lab, cursor-motion, hyperframes, beat-sync]
---
# lab-cursor-motion: Cua cursor motions, re-timed to the beat

**Brief.** the principal sent the Cua launch post (x.com/trycua/status/2107152124891246978) and asked "Worth stealing?". The post shows 6 new cursor motions for Cua Driver, picked from 82 in an open-source playground. Muse's verdict: take the motion code, but leave the cursor art, because it is the Cua brand. The principal said yes in a Hebrew voice note. He told Muse to decide what matters and to make a small, cute demo that shows his team how it works. A little spend was OK, with no set cap. He then asked for a second piece "with a cool beat": go wild, but spend nothing.

- **Vol. 1, "cursor, on the beat"** (24 s, 16:9, 92 BPM): a toy xylophone. One cursor plays a tune with one motion style per bar, and each click is a marimba note on beat 2 or 4. Bar 7 is an x-ray: it draws all six paths, and a beat lane shows each click on a beat line. In bar 8, six cursors arrive on eighth notes (an arpeggio) and strike one chord together.
- **Vol. 2, "Cursor Phonk"** (21.8 s, 16:9, 130 BPM, C# minor): cursors finger-drum a phonk beat live on a 4x4 pad controller. Each drum, 808 and cowbell hit is a click (223 clicks, 20 cursors, 12 motion styles). The parts enter one at a time: kick, then clap and 808, hats, cowbell. A 12-cursor swarm arrives in the break and slams 12 pads on the drop. A 4-3-2-1 countdown lines up all 20 cursors for the last downbeat.

**What was kept**
- Only the motion lab, vendored and pinned in `vendor/PINS.md` as `vendor/cua-motion-lab` (MIT). Its upstream is the folder `libs/cua-driver/tools/cursor-gallery/motion-lab/` in the `trycua/cua` monorepo.
- Each of the 82 motions is a pure function. It takes a seed and targets, and it returns timed points plus hover, press and click events. This is the same model as our engines, so it fits HyperFrames and p5 without a rewrite.
- The lab's 87 tests pass here, and the shipped styles give the same output on each run. The shipped styles are `signature_arc`, `comet_swoop`, `spring_settle`, `magnetic`, `adaptive` and `classic`.
- Not kept: the Rust driver, the Cua cursor art and the OS overlay.
- Added by Muse: `code-motion/scripts/cursor_track.mjs` re-times a track so each click lands on a given beat. It also supports hover waypoints. `code-motion/assets/cursor/cursor-fx.js` draws the cursor and its effects on a canvas as a function of time. The engine row is in [[tool-selection]].

**What worked**
- The re-timing keeps the move's own speed and adds a wait before the move. It does not stretch the whole path. In vol. 1 the worst speed-up was 1.25x (the first `squash pop` move). In vol. 2, with 16th and 32nd notes, no move went past 1.6x.
- `classic` needed 2.2–4x speed-ups to hit the beats. Vol. 1 shows the lab style `squash pop` in its place, which also shows the team that all 82 lab styles are available.
- Fast parts in vol. 2 are split across cursors: 2 hat cursors, 3 cowbell cursors, and 8 "divers" that roll the hat in 32nd notes.
- A sound on each click makes the sync audible. The vol. 1 x-ray lane explains the method without words.
- Sync on the final files: in vol. 1, each audio onset is 6–9 ms after its click (the attack rise), and each struck key moves on the first frame at or after its click. In vol. 2, solo stems through the same master chain put 191 of 191 timed hits within −1 to +3 ms. No pad flash is more than one frame off, and the file's audio matches the source bed at lag 0.
- Chrome's WebAudio master compressor delays the whole mix by about 8.7 ms (416 samples at 48 kHz). Vol. 2 measures this with an impulse and trims it from the bed.
- The old agent cursor from `vex-021` was a straight line plus a scale bump on click. The lab adds arc paths, spring landings, a speed glow, a click ripple and a squish.

**What didn't**
- In the vol. 1 draft, a cursor took the next style's colour about 0.65 s before the bar label changed. The fix: each leg carries a show time, and the player changes the look at that time. A ripple keeps the colour of the click that made it.
- Both drafts had dead air. Vol. 1 had 1.8 s with no cursor before the finale; hover waypoints now gather the cursors above their keys. Vol. 2 opened on 0.9 s of static pads; a "VOL. 2" title and a cursor on screen at frame 0 fixed it.
- The vol. 2 master is 94 MB, because the camera moves the whole frame on every kick. Grain that moved on every 60 fps frame first pushed the encode past 114 MB; grain now steps at 12 fps.
- The vol. 2 808 holds about 0.45 of its level into each next note, a side effect of `cancelScheduledValues` at the ramp end. It sounds like a legato phonk 808, and the timing does not change, so it stays.
- A full-mix onset check flags masked hits: 8 claps and hats under the cowbell, riser and blips. Solo stems are the proof for those parts.
- The frame-study hold fraction (0.97) has no meaning for small objects on a still set.

**Spend.** $0 for both, with no paid generation. The scores are `js-scoring` WebAudio synths. All renders ran on this 2-CPU box: vol. 1 at 60 fps took 4 m, and vol. 2 at 60 fps took 13 m 22 s.

**Final**
- Vol. 1: `projects/lab-cursor-motion/renders/cursor-on-the-beat-v1.mp4` (1920×1080, 60 fps, 24.08 s, 5.9 MB, −15.5 LUFS). Muse sent the full master to the principal on WhatsApp, because it is under the 16 MB cap.
- Vol. 2: `projects/lab-cursor-motion/v2/renders/cursor-phonk-v1.mp4` (1920×1080, 60 fps, 21.8 s, 94 MB, −11.4 LUFS). WhatsApp (16 MB) and the web chat (64 MB) both refused it. On the principal's route, Muse sent it as one full-res `send_file` in the WhatsApp chat, and he downloads it from the web view ([[generation-field-notes]], messaging caps).
- Each version folder has a `README.md` with build steps, `review/check_sync.py`, and a frame study in `review/v1`. Vol. 2 adds `review/stem_sync.py`.

## How the principal works with this
- He sends an X post with "Worth stealing?". He wants a split: what we can take (code under its licence) and what we must leave (brand art).
- When he says go, he lets Muse decide the scope. He asks for small, cute demos that he can show to his team, and "go wild, spend nothing" is a real brief.
- Muse talks to him in English, even when he writes or speaks Hebrew.
- For a master over both chat caps, he wants one full-res file, not a re-encode or a split.
