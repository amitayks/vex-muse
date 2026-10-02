---
kind: technique
tags: [generation, seedance, image-models, sync]
audience: studio-internal
half_life: 90
rights: safe
seen: 2026-09-29
summary: Observed behavior of Seedance 2.5 (incl. what its returned soundtrack is and how to verify lip-sync from it), Nano Banana Pro vs GPT Image 2 (style-dependent), matting models (Bria, SAM 3) and ElevenLabs Music on real Muse projects, plus timing-QA, render and fal-CDN delivery gotchas, with the fixes that worked.
---
# Generation field notes — Seedance 2.5, image models, music, timing

Model behavior drifts with versions: re-verify anything here older than its
half-life. Evidence: `pdoom-test` (Seedance quality test, P(doom) chorus,
13.1 s, 4 shots, "Cel Idol" style; source repo in [[claude-pop-case]]) and
`vex-021` (86 s Vex 0.21 release film, pure Canvas2D motion graphics on a
generated score) and [[lab-collage]] (archival collage assets and mattes).

## Image models for style tests and cast
- **Nano Banana Pro holds a flat cel/anime look and a character's identity
  better than GPT Image 2.** GPT Image 2 composed a nicer frame (calm text
  zone + backdrop) but rendered the face too small for identity lock. Choice:
  Nano Banana Pro for cast sheets and sets; do set variants as Nano *edits* of
  one plate rather than mixing models. A Nano sheet + stage as @Image1/@Image2
  held identity across all four Seedance plates.
- **The better image model depends on the style.** On a 13th-century
  tinted pen-drawing chronicle look (antioch-1098, 6 test frames on each
  model), **GPT Image 2 won**:
  - It returns **pure white grounds**, which act as identity under a
    multiply blend onto procedural vellum. Nano returns cream, aged paper
    that needs flat-field correction.
  - Its flat tinted washes read as authentically medieval, while Nano drifted
    to modern storybook faces with realistic shading.
  - `openai/gpt-image-2/edit` with character refs held identity, and
    `background: transparent` gives character sprites alpha. Put a vellum
    fill masked to the alpha under a multiply-blended sprite, so lines behind
    the figure don't show through.
  - So Nano wins cel and anime work, and GPT Image 2 wins period line art.
    Test both in the style grid.
- **GPT Image 2's content filter blocks mild bathing scenes.** A
  medieval-joke frame of a noblewoman "who took too long in the bath" was
  refused. It passed once she was fully clothed beside a steaming tub, with
  a curtain or veil hiding the scene. Keep the joke in the caption and the
  picture chaste.
- Nano Banana Pro outputs 2752×1536 at 16:9.
- **"Calm zone for text" is read literally as an empty void.** Asking for a
  calm left third produced a flat blank cream panel. Phrase it as the
  backdrop *continuing* into a calm flat area of a named colour ("the sunburst
  backdrop continues into a calm flat terracotta area on the left").
- Avoid asking any model for legible non-Latin text (e.g. a "Chinese room");
  dress the set with unreadable paper slips instead. See [[anti-slop]].

## Archival collage assets and matting
Tested on [[lab-collage]] (tokens in `collage-motion/references/prompts.md`).
- **Nano Banana Pro does archival B&W halftone well.** The "vintage
  black-and-white press photograph, coarse newspaper halftone" tokens gave
  4/4 usable assets on the first take.
  - Props came back "isolated on pure white, no text, no logos". The hero
    photo used an anonymous archetype.
  - At 2K, 3:4 is 1792×2400 and 1:1 is 2048×2048.
  - `fal.py` rates it at $0.15 per image at any resolution. That rate was not
    checked against fal's pricing API.
- **Photos come back with their own aged print border.** Crop ~3.5 % per
  side (`cutout.py --inset`) before tearing or framing.
- **Pseudo-text in generated rooms.** Posters and screens in generated rooms
  carry fake text, so keep them small or behind other layers.
- **Full generated pages garble their small text** (the Pexo route), so
  typography stays in DOM. See [[paper-collage-explainer]].
- **White-ground props: use the $0 white key.** A flood fill of near-white
  from the image edges mattes them cleanly. A light label enclosed by a
  darker shell survives, because the fill can't reach it.
- **`fal-ai/bria/background/remove` ($0.018) is for isolated objects
  only.** On a busy full-frame room photo it kept 97 % of the frame as
  foreground.
- **`fal-ai/sam-3/image` handles a subject inside a scene.**
  - Price: $0.005 per call (fal pricing API), about 4 s.
  - Inputs: a text `prompt` and `apply_mask: false`.
  - Output: a binary L-mode mask PNG at the source resolution. `person` gave
    a clean mask that left out the guitar on his lap.
  - It returns the same URL as both `image` and `masks[0]`. That made
    `fal.py` log $0.01 until its img-unit estimate switched to counting
    unique URLs (fal-media 1.2.0).
- `bria/extract-object` ($0.02) exists and is untested.

## Seedance 2.5 image-to-video (product shots)
- A photoreal keycap still made with Nano Banana Pro from the rasterized
  brand icon, then turned into an 8 s Seedance image-to-video push-in, passed
  its first 480p draft and held the object's identity. Seedance picks where
  the scripted "press" lands (7.375 s here, not the requested time). Find
  that frame by frame, then time-remap to the beat.
- Finished image-to-video plates come out 1926×1076; scale to 1920×1080.

## Seedance 2.5 reference-to-video with @Audio1 lip-sync
- Prices confirmed: 480p draft **$0.2205/s** (4 s = $0.882, audio on);
  1080p finish via `draft/complete` ≈ **$4.76 per 4 s plate** (output runs
  4.087 s). `draft/complete` returns no duration, so cost must be derived
  from the output file — check the ledger after every finish.
- First-round hit rate: **2 of 4 drafts passed**. Masked or non-lip-sync
  shots (face hidden, prop action) pass easily; the failures were timing.
- **Events tied to a sung word arrive 0.5–1 s late.** Pyro on "FOOM", a mask
  reveal on "lies" and irises igniting on "eyes" all landed late. Stating the
  cue as an absolute time inside the slice ("pyro exactly at 3.1 s on FOOM,
  no pyro before") fixed the pyro on re-draft; naming the word alone does not.
- **Mouth stays closed on the first words of a slice.** On a slice starting
  mid-phrase ("with your shinigami eyes") the singer only opened her mouth on
  the second word. Prompt "she starts singing immediately at 0.0 s, mouth open
  on the first word"; if it still misses, let hero text carry the pickup.
- Framing requests are weakly obeyed: asking for waist-up still returned a
  medium-wide, face too small to judge lip-sync at 480p.
- Re-drafts can drift off-bible (one S4 re-draft swapped the navy/red palette
  for a psychedelic swirl); compare against the earlier draft before choosing.
- **Finishing preserves timing.** 1080p finishes re-checked within 10–50 ms of
  their drafts, so a draft that passes sync is safe to finish. Plates that
  passed can finish while failed shots re-draft in parallel.

### Free fix: time-remap late events in the conform
Instead of paying for a re-draft, remap plate time → song time with
piecewise-linear knots (`scenes/remap.json`), speeding up only where lip-sync
cannot be broken:
- during a **held vowel / melisma** (mouth shape is static) — pulled the S4
  red-eye flare onto "eyes" at ~1.35× speed;
- during stretches where the **mouth is hidden** (behind a mask) — ramped S3
  so the mask drop lands on "lies".
Then end on a hard 2-frame punch rather than a slow fade that hides the payoff.

### Verifying lip-sync from the plate's own soundtrack
- **Mechanism.** Seedance copies @Audio1 into the soundtrack it returns, and
  the mouth follows that copy; where the copy drifts, the mouth drifts too
  (found at scale in [[escape-velocity-case]] §1). The copy is
  **re-synthesised, not verbatim**: waveform NCC against the slice was only
  r = 0.05–0.36 on all 10 pdoom-test plates, so compare spectra, not
  waveforms.
- **Current check (since 2026-09-29):** `seedance-plates/scripts/syncdiverge.py`
  (skill 1.1.0), wired into `platecheck`. It tracks a log-mel match over time
  (per-band mean removed, 10 ms hop, 400 ms windows, threshold set above a
  mismatched-lag null) and returns one verdict:
  - `in_sync`: the copy holds all clip; pass if |lag| ≤ 40 ms.
  - `diverges`: fails from `t_div`; the report gives the song-time cut point
    and the words the cover clip must re-sing.
  - `glitch`: short dips that recover (e.g. inside a held vowel); look at the
    mouth in the `check_by_eye` spans, keep if hidden or static.
  - `no_copy` / `ambiguous`: the audio cannot vouch; the mouth sheet decides.
- **Validation, $0:** a synthetic suite on real plates (clean, wrong slice,
  mid-clip replace, 100 and 250 ms slip, dropout) passes 12/12 with the two
  plates swapped, locating each planted break within ~0.1 s
  (`scripts/test_syncdiverge.py`, must exit 0).
- **Results on the 10 pdoom-test plates** agree with the earlier eye review
  (null p90 0.06–0.13):

  | plate | verdict | lag | match | read |
  |---|---|---|---|---|
  | S2 d1 / final | in_sync | 0 ms | 0.62 / 0.65 | copy holds 100 % |
  | S4 d1 / final | in_sync | −20 ms | 0.62 / 0.65 | copy holds 100 % |
  | S4 d2 (rejected on palette) | in_sync | +50 ms | 0.40 | would fail the 40 ms lag gate |
  | S3 d1 / final | glitch | −50 ms | 0.40 / 0.42 | 0.3 s dip inside the held "lies", recovers; the mask hides the mouth → harmless |
  | S1 d2 / final | no_copy | — | 0.14–0.17 | the plate's own pyro/confetti SFX drown the copy; eye call (0 ms) stands |
  | S1 d1 (rejected) | diverges | +340 ms | 0.42 | late all clip, breaks at 3.0 s where its own boom takes over |

- **Pitfalls it handles:**
  - Model-generated SFX (pyro booms) replace the copy, so an SFX-heavy sung
    plate cannot be verified from audio. Keep SFX out of sung plates or
    judge them by eye.
  - A mid-clip slip gives two competing global lags, just like beat
    aliasing. The tell is time: in a slip each lag wins a different stretch;
    with aliasing both fit the same stretches.
- **Superseded: the single onset-envelope lag** (the original `platecheck`
  audio check, still reported as `onset_lag_ms`, never a gate). It aliases on
  the beat period: S1 read a confident −450 ms ≈ one beat at 132 BPM, with
  near-equal peaks at −240 ms and 0, which was simply wrong. Sign convention
  kept: negative lag = plate audio early → delay the picture.
- **Mouth-from-picture does not work on stylised plates.** A YuNet face
  detector (mouth darkness vs vocal loudness) found the face in 0 of 97
  frames on the S2/S3/S4 finals (cel style, mask, eye close-up). The one
  clean read, S1 d1, had the mouth ~+210 ms late against a +340 ms
  soundtrack: the same direction, but a hint, not proof. Not adopted.

## Music and SFX generation
- ElevenLabs **Music via the direct API returns 402 on the free plan**; the
  same model works through fal (`fal-ai/elevenlabs/music`, `prompt` +
  `music_length_ms` + `force_instrumental`). ElevenLabs SFX work directly.
  fal now also serves `elevenlabs/music/v2.5`, whose `composition_plan`
  (timed chunks) gives exact section boundaries. The full generator landscape
  is in [[music-tools]].
- Both 90 s instrumental scores prompted at 120 BPM came back with an **~8 s
  near-silent intro** before the drop. Trim so the drop lands at ~2 s for the
  hook; a ticking intro (key clicks on the beat) is worth keeping as tension.
- Whisper on an instrumental's silent tail **hallucinates text** (a Romanian
  "subscribe to our channel" outro). Ignore `words` on instrumentals.
  A lone "You" on ElevenLabs and Lyria 3 instrumental beats was the same
  hallucination. Treat one or two stray words as no vocals when checking a
  take for phantom vocals.
- **ElevenLabs v2.5 composition-plan cues are not clean beds** (five cues
  for antioch-1098):
  - Takes carried unrequested **near-silent dropouts** of 1.5–3.5 s
    mid-cue. The fix was to offset the cue start so the dropouts land on
    comic pauses in the narration.
  - Tempo came in 6–7 % off the brief (93.35 vs 100 BPM).
  - "Instrumental" medieval cues carried chant: 12–13 phantom words
    against the usual 1–2. Find the dropouts with an RMS envelope and the
    chant with a transcript before placing a cue under speech.
- The `gpt-audio` listening proxy sometimes refuses outright ("I'm unable to
  listen"). Retry, and never treat a refusal as a verdict.
- Measure each SFX file's onset/peak offset before spotting (e.g. a clack
  with 58 ms of lead silence) and cue by peak, not file start.

## Timing QA
- **The song-map beat grid sits a constant offset early of the real hits.**
  P(doom): drum onsets 46 ms after the 132 BPM grid (MAD 0.4 ms). vex-021
  score: the drop landed 60 ms after the grid downbeat. Measure grid vs real
  onsets on every song, record the offset (`beat_offset_vs_drums_ms`) and
  shift beats/downbeats so cuts land on the hits. Lyric timing is unaffected
  (it uses vocal word onsets). **Root cause found 2026-09-26** (song-map
  1.1.0): onset frames were stamped at their start, 46 ms before the window
  centre. That offset is now corrected in the tracker, and beat_this on Modal is
  the default grid (+15 ms vs kicks). Still measure the offset; it is now
  ~−20…+15 ms, not ~50 ms. Details in [[music-tools]].
- Word boundaries on melisma and fricatives ("shoggoth's lies", held "eyes")
  need hand-checking on the vocal-stem RMS envelope; aligner times overlap
  there. Slice bounds should end in an energy dip, not mid-sustain.
- Frame count: use `round(dur × fps)` consistently in timing and conform;
  mixing `ceil` and `round` drops the last frame.

## Rendering
- **Pure Canvas2D pages render ~19 fps locally** on the 2-CPU box (86 s at
  30 fps ≈ 2.5 min) — no Modal needed for motion-graphics or plate+lyrics
  compositing; Modal is for p5.brush painting. The page contract is
  `window.ready`, async `window.renderAt(t)`, `window.renderSheet`, `DUR`.
- Brand display fonts lack symbol glyphs (✓ ⎇ ⌘ ◉) and the render boxes have
  no system fallback fonts: draw icons as shapes, never rely on glyph fallback.
- **three.js pages:** headless Chrome blocks ES-module imports over
  `file://` and the page just hangs with no error. Ship three as a classic
  script instead (`studio/assets/lib/three.classic.js`, the module build with
  its export rewritten to `window.THREE`). Locally it needs `--soft-gl`
  (SwiftShader), which runs at about 2–4 s per frame with motion-blur
  subframes: fine for sheets, far too slow for a full cut. On Modal L4, 1980
  frames at 1080p30 took ~25–30 s wall in 12 chunks.
- Modal can reuse a warm container with a stale studio tree; after any farm
  render, diff a changed frame against the prior version.

## Delivery and fal CDN privacy
- **fal CDN URLs are public by default**: anything sent through `fal.py
  upload` or produced by a model is readable by anyone with the URL.
  Uploads are for model inputs only, never a delivery channel for finished
  work; the principal's rule is the full-res master as a file, to him only (web
  chat when WhatsApp's 16 MB cap blocks it).
- A normal `FAL_KEY` **cannot DELETE** a CDN file (403/404 on every
  endpoint tried). To withdraw one: `PUT
  https://rest.fal.ai/storage/files/acl?url=<url-encoded file url>` with body
  `{"default":"hide","rules":[]}`; the public GET then returns 404.
  This works on uploads and image outputs, but **returned 403 on Seedance
  video outputs**. Those stay public-by-URL, so never share their URLs.
- **Messaging caps.** `send_file` to WhatsApp refuses anything over 16 MiB
  (16,777,216 bytes). To deliver a bigger master without losing quality,
  split it losslessly with an ffmpeg stream copy (`-c copy`) at keyframes.
  List keyframes with `ffprobe -show_entries packet=pts_time,flags`. The
  parts are bit-exact slices of the master. Default x264 GOPs of ~8 s limit
  the split points, and grainy photoreal shots are heavy per second. Encode
  finals with a shorter GOP if splitting is likely.
  - **Web chat takes bigger files.** the principal's Vex web chat accepts ~64 MB
    per file, WhatsApp 16 MiB. A 415 MB master still needs parts.
  - **Cut by size, not time.** A time-even first part came out 78.6 MiB
    because the cold open is the densest stretch. Choose keyframes so each
    part stays under ~58 MiB.
  - **The segmenter snaps to the *next* keyframe,** so put each cut a hair
    before its keyframe.
  - **Verify the parts:** joined back together, the video and audio
    streams must be MD5-identical to the master. That proves the parts are
    the master and not a copy (`antioch-1098`, 8 parts).
- **The workspace auto-syncs to git** (`your workspace's git remote`,
  private: unauthenticated API and web return 404). Any new media path must
  be in `.gitignore` before its first file lands. The music lab committed
  263 MB (54 audio files, including stems of commercial songs) before rules
  existed ([[lab-music]]).
  - `git check-ignore` says nothing about files that are already tracked,
    so also check `git ls-files`.
  - Untrack with `git rm --cached`. History keeps the files until a rewrite
    and force push, which needs the principal's yes.
- ElevenLabs Music via fal bills **$0.60 per started output minute** (a 30 s
  clip bills as a full minute), per fal's pricing API on 2026-09-26. `fal.py`
  has carried this rate and every other music/audio rate since that date,
  so the ledger now logs music cost automatically. This supersedes the
  earlier hand estimate of ~$0.8 per minute used on `vex-021`.

Related: [[music-video-grammar]] (lip-sync framing), [[kinetic-typography]].
