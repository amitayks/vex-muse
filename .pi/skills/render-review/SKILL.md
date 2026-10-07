---
name: render-review
description: Render a video from the studio (local previews or the render farm), encode it with the final audio mix, and review it like a stranger - full watches, per-lyric screenshots, contact sheets, a scored rubric against the brief's requirements - producing a versioned review with the fix list that sends work back to the right phase. Use in phase 9 of a video project, after any change to a rendered cut, and before anything is called done or delivered.
license: MIT
compatibility: tools/env.sh (Chrome, ffmpeg, $PY with modal); MODAL_TOKEN_ID/SECRET for GPU renders; GitHub Actions `render.yml` as CPU fallback.
metadata:
  author: muse
  version: "1.6.1"
---

# render-review — done means watched

## Render
- **Code-motion cuts** (HyperFrames master, `code-motion`): render locally —
  `npx hyperframes render <comp> --quality draft --fps 30` to review (~31 s per
  8 s of 1080p), `--quality delivery --fps 60` for the final. Painted layers
  still come from the farm below.
- **WebGPU code-motion cuts** (shader layers, skill `webgpu-shaders`): HyperFrames
  cannot render them here. Render on Modal: `HF_COMP=<comp> $PY -m modal run
  .pi/skills/render-review/scripts/modal_hf.py --comp <comp> --timeline main --duration <s>
  --out <mp4> --audio <wav> --fps 30 --chunks 32 --webgpu --cpu 8` (~2 min for 32 s of 1080p30).
- **Where (painted p5 frames)**: this box (2 CPU, software WebGL, ~75 s/frame) is for sheets,
  strips and stills only. Full renders go to **Modal GPUs** (default, pay per
  second, nothing idle; measured 0.23–0.3 s per 1080p watercolor frame on an
  L4 with `--gpu-angle=vulkan`):
  `$PY -m modal run .pi/skills/render-review/scripts/modal_render.py::render --page <studio page> --t0 A --t1 B --chunks N --out projects/<slug>/renders/frames`
  (env: `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET`; ships the local `studio/`
  tree, so no git sync needed; `::probe` = GPU sanity check + timing sheet).
  N ≈ duration/10 s (≤20). Then `farm.py encode <frames> audio/mix.wav <out.mp4> --start A`.
  Fallback: GitHub Actions CPU farm (`farm.py submit/collect`, ~70 s/frame
  per runner — only if Modal is down).
- **Versions**: `renders/v<N>.mp4` never overwritten; `renders/v<N>.json`
  records git sha, shots changed, farm run id, duration, ms/frame.
- **Platform fit**: check the destination's current length/size limits
  before the final encode (e.g. X non-Premium 2:20 max); an over-length song
  gets a radio edit cut on bar lines in `song.json`, never a fade-out.
- **Encode**: H.264 High, CRF 17, yuv420p, faststart, 24 fps (or the
  project fps), AAC 256k from the mix. Cutdowns (9:16, 1:1) are separate
  layouts, not crops.
- Delete frames after a verified encode (disk law).

## Review (every version)
0. **Frame study**: `$PY .pi/skills/reference-mesh/scripts/framestudy.py renders/v<N>.mp4
   --fps 8 --out review/v<N>/study` → tempo, cut grid vs beats, hold share, palette per shot,
   `motion.png`, timecoded sheets, a strip for every transition. Read all of it; compare with
   the reference's numbers when the brief names one ([[code-motion-showreels]]).
0b. **Shipping-now check** (quick, every version): `python3 .pi/skills/reference-mesh/scripts/whatships.py
   wall --cat motion,design --days 14 --out review/v<N>/wall.jpg` and read it beside our contact sheet.
   Could our cut sit in that wall unnoticed? Which saturating traits from [[whatships]] does it use? Two
   or more, or "yes" → originality ≤3 and the fix goes to `style-bible`. For a craft question ("how did
   they time that?"), `whatships.py fetch <slug> --study` and compare the numbers.
1. **Stranger watch**: the whole file at full speed, no pausing — note the
   first moment attention drops, anything confusing, anything that feels
   off-beat. (Watching = reading a 4 fps contact strip of the full video in
   order plus the audio-onset table; say which.)
2. **Lyric screenshots**: one frame per lyric line at its mid-point +
   one at each hero word's onset → `review/v<N>/lyrics_*.jpg`; read all.
3. **Seams**: a strip ±0.5 s around every cut. Performer→performer cuts: the eyes' midpoint lands at
   the same screen height and near the same x in the last/first frame (final crop, same tile size);
   a jump is fixed by reframing the shot, a punch-in may change face size but not eye height.
4. **Sync**: `platecheck`-style lag for the full mix vs master (must be 0),
   word-onset strips for 5 random lines.
5. **Thumbnail test**: frames at 0.0, 0.5, 1.0, 2.0 s at 360 px wide — is
   the hook legible and arresting?
6. **Requirements**: re-read `brief.md → Requirements`; map each to a
   timestamp/frame or mark MISSING.

## Rubric (score 1–5, bar = all ≥4, hook and sync = 5)
hook (0–2 s) · sync (mouths, words, cuts on beat) · readability (one read at
a time, text legible at phone size) · coherence (one world, on-model, palette
arc) · craft (medium consistent, no slop tells, motion principles) ·
retention (cadence varies with energy, escalation per chorus, no dead
stretch > 2 bars, holds 20–40 % of frames, ≥60 % of cuts on a beat) · payoff (motif pays off, ending rhymes) ·
requirements (every brief line satisfied) · originality (a stranger would not
mistake it for the reference, a recent viral piece, this fortnight's launch wall or my last
project; it could not belong to another song).

Write `review/v<N>.md`: scores, evidence (frame paths), and the fix list —
each fix routed to its phase/skill (e.g. "shot 14 read collision →
storyboard", "chorus 2 mouth off → seedance-plates"). Fix at the source,
re-render the affected range, re-review. Repeat until the bar holds.

## Acceptance
The delivered version has a review file with all rubric lines at/above the
bar, every requirement mapped to evidence, render metadata recorded, and
frames cleaned up.
