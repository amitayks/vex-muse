---
kind: technique
tags: [generation, seedance, image-models, sync]
audience: studio-internal
half_life: 90
rights: safe
seen: 2026-10-11
summary: "Observed behaviour of Seedance 2.5 (soundtrack, lip-sync checks, end-frame cuts), Nano Banana Pro vs GPT Image 2 vs FLUX 3, matting models, performance transfer (Kling motion-control), plates from architecture renders, ElevenLabs Music and Stable Audio 3 quirks, timing QA, render and fal-CDN delivery gotchas, with the fixes that worked."
---
# Generation field notes — Seedance 2.5, image models, music, timing

Model behavior drifts with versions: re-verify anything here older than its
half-life. Evidence: `pdoom-test`, `vex-021`, [[lab-collage]],
a client brand film and the project notes linked in each section.

## Image models for style tests and cast
- **Nano Banana Pro holds a flat cel/anime look and a character's identity
  better than GPT Image 2,** which rendered the face too small for identity
  lock. Do set variants as Nano *edits* of one plate. A Nano sheet + stage as
  @Image1/@Image2 held identity across all four Seedance plates.
- **Frames made from text alone rebuild the set every time.** A cockpit's
  glazing changed between two frames, and a reverse shot "on the glareshield
  facing aft" still drew the windscreen behind the pilot, with her window on
  the wrong side. Make one approved empty-set master view, build every angle
  and start frame as an edit of it, and name each side of the frame in the
  prompt ("her side window on the RIGHT of the frame; windscreen behind the
  camera").
- **An approved frame passed as image 2 gets copied.** With the set master
  as the second image, Nano rebuilt the whole scene from it (lost smoke and
  jolt, a mic on the wrong ear). Composite small missing details in the
  finish instead.
- **The better image model depends on the style.** On a 13th-century
  tinted pen-drawing look (`antioch-1098`) **GPT Image 2 won**: its pure
  white grounds multiply cleanly onto vellum (Nano returns cream paper), its
  flat washes read as medieval (Nano drifted to storybook faces), and
  `openai/gpt-image-2/edit` with refs held identity (`background:
  transparent` gives alpha). Nano wins cel, anime and photoreal faces
  ([[lab-cinematic]]); test both in the style grid.
- **GPT Image 2's filter refused a mild bathing joke**; the same woman fully
  clothed beside a steaming tub passed. Keep the joke in the caption.
- Nano Banana Pro outputs 2752×1536 at 16:9.
- **"Calm zone for text" is read literally as an empty void.** Asking for a
  calm left third produced a flat blank cream panel. Phrase it as the
  backdrop *continuing* into a calm flat area of a named colour ("the sunburst
  backdrop continues into a calm flat terracotta area on the left").
- Avoid asking any model for legible non-Latin text (e.g. a "Chinese room");
  dress the set with unreadable paper slips instead. See [[anti-slop]].

## FLUX 3 Image
Use it only for plates whose placement and scale must be exact; evidence and prices in [[lab-flux3]].
- **Layout by box works.** Inside `prompt`, write a caption with `<id_n>` tags, then a JSON row table (`id`,
  `bbox` [top, left, bottom, right] on 0–1000, `desc`); fal has no bbox field. It placed the singer in her box
  at the asked crop; Nano, given the same layout as prose, drifted her to the centre.
- **Its edits are not pixel-locked through fal.** Edits follow the boxes but come back
  re-tinted (aqua backdrop → mint) and resampled to another size. Colour-match a FLUX edit to its source
  before pairing them as Seedance start/end frames.
- **It overrides style tokens toward clean modern photography:** no halftone, a grey sweep instead of pure
  white, an added cast shadow. A "pure white background" medieval drawing came back on parchment.
- **Its filter refuses named anime and film titles** ("Sailor Moon", "Perfect Blue") with a 422
  `content_policy_violation`; the same prompts pass without them. Describe the look instead.
- Cel-style identity from a sheet plus set plate held as well as Nano's.

## Archival collage assets and matting
Tested on [[lab-collage]] (tokens in `collage-motion/references/prompts.md`).
- **Nano Banana Pro does archival B&W halftone well:** the "vintage
  black-and-white press photograph, coarse newspaper halftone" tokens gave
  4/4 usable assets on the first take. At 2K, 3:4 is 1792×2400.
- **Photos come back with their own aged print border.** Crop ~3.5 % per
  side (`cutout.py --inset`) before tearing or framing.
- **Generated text is fake.** Keep generated posters and screens small or
  behind layers; typography stays in DOM ([[paper-collage-explainer]]).
- **White-ground props: use the $0 white key.** A flood fill of near-white
  from the image edges mattes them cleanly. A light label enclosed by a
  darker shell survives, because the fill can't reach it.
- **`fal-ai/bria/background/remove` ($0.018) is for isolated objects
  only.** On a busy full-frame room photo it kept 97 % of the frame as
  foreground.
- **`fal-ai/sam-3/image` handles a subject inside a scene** ($0.005, ~4 s):
  a text `prompt` plus `apply_mask: false` returns a binary mask PNG at
  source size. `person` gave a clean mask that left out the guitar on his lap.

## Video matting: Bria VRMBG v3 vs LTX-2.5 Alpha-Gen
Tested on [[lab-alphagen]] (access, limits, licence and numbers there) with a 4 s cel-anime idol plate
and a generated soft-edge clip (wind-blown hair, sheer sleeves, stage haze).
- **Bria v3 is the default for cutting out a subject.** `bria/video/background-removal/v3` ($0.03/s,
  about 22 s for 4 s). On the cel idol it agreed with Alpha-Gen (IoU 0.84), kept the ink line crisper
  and flickered about half as much. On the soft clip it kept flyaway hair strands cleanly and stayed
  stable, but dropped the haze and turned a sheer sleeve opaque.
- **Alpha-Gen picks its own foreground**: the semantic main subject, with no prompt or mask. When the
  idol plate cut to flames and confetti, it matted them as soft foreground while Bria kept only the
  idol. That makes it the candidate for semi-transparent elements around a performer (smoke, haze,
  fire, glass); that case is untested.

## Seedance 2.5 image-to-video
- Seedance picks where a scripted action lands (a keycap "press" came at
  7.375 s, not the requested time). Find that frame, then time-remap to the beat.
- **Real faces are refused up close.** Seedance image-to-video rejected every
  close shot of the real chef from a photo shoot (`partner_validation_failed`,
  real-person likeness). A wide team shot with small faces passed once, then
  a re-draft was refused too. Refused jobs are not billed. Kling v3 Pro
  image-to-video held the same faces (a client store film).
- Finished image-to-video plates come out 1926×1076; scale to 1920×1080.
  480p drafts come out 856×478 at 24 fps (97 frames for 4 s).
- **An end frame turns a fast action into a hidden cut.** For a cleaver
  chop, a start still (cleaver raised) and an end still (cleaver embedded)
  were both pinned (`image_url` + `end_image_url`). Seedance lifted the cleaver out of frame
  at ~0.8 s, showed the empty block, then cut to it embedded at ~1.4 s: no
  fall at all. The same start frame **without** an end frame, prompted as
  physics ("falls straight down under gravity, very fast … The cleaver
  never leaves the frame. After the impact everything is still."), gave a
  continuous fall with the impact inside ~3 frames, then a hold.
  - Rule: for fast physical actions pin only the start frame, describe the
    physics and forbid leaving the frame. Keep end frames for slow
    transformations (Kling behaves the same way, below).
- **Find hidden cuts with a frame-diff list** (mean luma diff of consecutive
  frames at 240×135): a lone spike after near-zero motion is a cut; a real
  fast action shows a short run of raised values.
- **Generated "flat brand-colour" backdrops miss the hex.** A seamless
  backdrop prompted as aqua `#BFEDEF` came back an even RGB ≈ (175, 230, 226). Sample the plate and use that colour for any
  adjacent flat field, or let the photo be the band (a client brand dossier).

## Performance transfer: an AI actor as the driver
Test of the actor-driven route from [[gossip-goblin-trailer-case]]: `projects/lab-cinematic/test-driver/`. One 8 s line, a photoreal still (Nano Banana Pro) and a Veo 3.1 Fast text-to-video driver (a plain actor in the same framing, audio on, $1.20).
- **Kling v3 Pro motion-control won** ($0.168/s, `character_orientation: video`, ~7 min wall). It kept the still's face, coat and room and followed the driver's head, eyes and mouth (1920×1088, 30 fps).
- **Veo 3.1 Fast image-to-video straight from the still** ($0.15/s with audio) held identity best. The acting is the model's own, so use it when the acting can be simple.
- **H3 Max Recast** ($0.45/s at 1080P; the pricing API's "0.05 units" is wrong) is the sharpest and copies the acting exactly. It keeps the driver's room and drifts the face toward the driver. Use it only when the driver is already shot in the final set.
- **Wan Motion failed:** it drew a ghost second head on an 8 s chest-up close-up.
- **The ElevenLabs voice changer** (fal, library voice ID `1BfrkuYXmEwp8AWqSLWk` "Declan") kept the driver's word timing to +10 ms (envelope r 0.89). So a transferred mouth stays in sync with the changed voice.
- Cost per 8 s directed shot on the winning route: about $2.70 (driver $1.20, Kling $1.34, voice changer $0.30 per started minute, assumed).
- **Shoot the driver in a plain version of the final set and costume.** Both dialogue shots of [[lab-cinematic]] passed on the first take this way.
- **Motion-control plates trim the driver's start** by a varying amount (40, 70 and 210 ms measured; 5.83 s out for a 6.0 s driver). Measure the lag on the plate's own audio copy and place the re-voiced line by it.
- **A gesture lands on the driver's side of the face.** Mirror the driver (hflip) when the story needs the other side, and keep the still's facing with `character_orientation: image`.

### Kling v3 Pro image-to-video
- At 4 s (`generate_audio: false`, $0.112/s) it gave 1–2 s of usable life on 9 of 10 world shots on the first take: a face lifted from water, a wave over shards, steam from a driftwood horse, a porcelain hand grabbing a wrist.
- **It ignores a state change described only in the prompt.** "The lanterns go out one by one" left every flame lit. A Nano Banana Pro edit of the frame with the lights out, as `end_image_url`, worked; retime the change in the conform.
- **"Blast" makes an explosion.** "As the aircraft passes, its blast hits the camera" gave a fireball under a water bomber, and a negative clause did not stop it. Write "a gust of wind shakes the camera", or add the shake in the conform.
- **Fast vehicle passes start with a ~1.2 s slow float,** even with "full speed from the first frame": use the fast span or speed it up.
- **"Locked camera" is not enough: Kling pans to follow a fast subject** (the background slid 116 px in 2.4 s). Name what stays fixed ("the canyon wall, the ridge and the brush stay exactly where they are in the frame; only the aircraft and the smoke move"), put pan/track/follow in the negative and use cfg 0.7: the background then held within 0.7 px. Measure the background shift (phase correlation on a static area) before calling a take locked.
- **A shorter duration makes a faster event** (`duration: 3`: out of frame by 2.8 s). Kling adds unasked parts late in a take (fireball, landing gear), so cut before them.

## Architecture plates from renders
Five image-to-video models on two renders of a residential tower, a night exterior and an interior (a real-estate film):
- **MiniMax H3 Max camera-controls** (`minimax/h3-max/camera-controls`) kept facades and furniture
  rigid and sharpest; the camera follows azimuth, elevation and distance keyframes over a frozen
  scene, though the sky can still change. `duration: 6` returns about 6.6 s.
- **Kling v3 Pro** moves naturally but invents (snowy peaks behind the city; a push-in through a
  glass railing). **Veo 3.1 Fast** oversharpened and invented rooms; Veo and Wan 3.0 Prime added a
  crown to the tower. Veo bills audio by default (+50–100 %): send `generate_audio: false`.
  **Seedance 2.5** drafts were soft and drifted on facades.
- The rule that worked: H3 camera-controls for buildings and rooms, Kling for people, wind or water.

## Repainting Blender renders
The LTX render-to-real paint pass, the video repaint test (Flux 3 edit-video leads) and the seam findings live in [[render-repaint]].

## Seedance 2.5 reference-to-video with @Audio1 lip-sync
- Prices: 480p draft **$0.2205/s** (audio on); 1080p finish via
  `draft/complete` ≈ **$4.76 per 4 s plate**. `draft/complete` returns no
  duration, so derive its cost from the output file.
- Masked or non-lip-sync shots pass easily; first-round failures were timing.
- **Events tied to a sung word arrive 0.5–1 s late.** Pyro on "FOOM", a mask
  reveal on "lies" and irises igniting on "eyes" all landed late. Stating the
  cue as an absolute time inside the slice ("pyro exactly at 3.1 s on FOOM,
  no pyro before") fixed the pyro on re-draft; naming the word alone does not.
- **Mouth stays closed on the first words of a slice.** On a slice starting
  mid-phrase ("with your shinigami eyes") the singer only opened her mouth on
  the second word. Prompt "she starts singing immediately at 0.0 s, mouth open
  on the first word"; if it still misses, let hero text carry the pickup.
- Framing requests are weakly obeyed (waist-up came back medium-wide), and
  re-drafts can drift off-bible; compare against the earlier draft.
- **Finishing preserves timing.** 1080p finishes re-checked within 10–50 ms of
  their drafts, so a draft that passes sync is safe to finish. Plates that
  passed can finish while failed shots re-draft in parallel.

### Free fix: time-remap late events in the conform
Instead of a paid re-draft, remap plate time → song time with piecewise-linear
knots (`scenes/remap.json`), speeding up only where lip-sync cannot break: in a
held vowel (static mouth) or while the mouth is hidden. End on a hard 2-frame
punch, not a slow fade that hides the payoff.

### Verifying lip-sync from the plate's own soundtrack
- **Mechanism.** Seedance copies @Audio1 into the soundtrack it returns, and
  the mouth follows that copy; where the copy drifts, the mouth drifts too
  (found at scale in [[escape-velocity-case]] §1). The copy is
  **re-synthesised, not verbatim**: waveform NCC against the slice was only
  r = 0.05–0.36 on all 10 pdoom-test plates, so compare spectra, not
  waveforms.
- **The check** is `seedance-plates/scripts/syncdiverge.py`, wired into
  `platecheck`. It tracks a log-mel match over time and returns one verdict:
  - `in_sync`: the copy holds all clip; pass if |lag| ≤ 40 ms.
  - `diverges`: fails from `t_div`; the report gives the song-time cut point
    and the words the cover clip must re-sing.
  - `glitch`: short dips that recover (e.g. inside a held vowel); look at the
    mouth by eye, keep if hidden or static.
  - `no_copy` / `ambiguous`: the audio cannot vouch; the mouth sheet decides.

  It finds planted breaks within ~0.1 s on a synthetic suite, and it agrees
  with the eye review on all 10 `pdoom-test` plates.
- **Model-generated SFX (pyro booms) replace the copy,** so an SFX-heavy sung
  plate cannot be verified from audio. Keep SFX out of sung plates or judge
  them by eye.
- **A mid-clip slip gives two competing lags,** like beat aliasing; in a
  slip each lag wins a different stretch.
- **A single onset-envelope lag is never a gate.** It aliases on the beat
  period: one plate read a confident −450 ms (one beat at 132 BPM) when the
  truth was 0. Sign convention: negative lag = plate audio early → delay the
  picture.
- **Mouth-from-picture fails on stylised plates** (YuNet found no face in
  97 cel, masked or eye close-up frames).

## Music and SFX generation
- ElevenLabs Music returns 402 on the free direct API but works through fal.
  SFX worked directly until the direct key used its 10,000-credit quota
  (HTTP 401 `quota_exceeded`); `fal-ai/elevenlabs/sound-effects/v2` works
  (at most 22 s per call, `loop` supported). Prices: [[music-tools]].
- Both 90 s scores prompted at 120 BPM had an **~8 s near-silent intro**.
  Trim so the drop lands at ~2 s for the hook.
- Whisper **hallucinates text** on instrumentals (a "subscribe to our
  channel" outro, a lone "You"). Treat one or two stray words as no vocals.
- **ElevenLabs v2.5 composition-plan cues are not clean beds** (five cues
  for antioch-1098):
  - Takes carried unrequested **near-silent dropouts** of 1.5–3.5 s
    mid-cue; an offset cue start put them on comic pauses.
  - Tempo came in 6–7 % off the brief (93.35 vs 100 BPM).
  - "Instrumental" medieval cues carried chant: 12–13 phantom words
    against the usual 1–2. Find the dropouts with an RMS envelope and the
    chant with a transcript before placing a cue under speech.
- **Plan-chunk descriptions don't control dynamics** (ElevenLabs v2.5,
  140 BPM, 4 takes on a client brand film). A first chunk described
  as "sparse, only short sub hits" came back with the kick at full level from
  bar 0, and "starts instantly at full energy, no intro" was obeyed by one
  take of two. Design intros, breakdowns and stops yourself (filter, stems,
  SFX, an edit on bars) and take only the groove from the generator.
  - Tempo was exact (grid drift ≤ 4 ms), unlike the 6–7 % miss on
    antioch-1098's cues.
  - Every take ran exactly **1.33 s longer** than the plan. Measure length
    per take; a plan near a minute boundary may bill the next minute.
  - A plan asking for E minor came back in C major (a client branch film).
- Stable Audio 3 on the same 140 BPM brief kept the exact length (27.43 s)
  but had no sections at all (flat energy to the end), ignored the key
  (F minor for A minor), and one of two takes measured 70 BPM (half time).
- **The audio-model ear is good for vibe words, not structure.**
  `gpt-audio` refused to judge a take (3 of 3) but answers accent questions
  ([[voice-casting]]); `gpt-4o-audio-preview` returns `model_not_found`;
  `gpt-audio-mini` gave usable genre words and an invented timeline.
  - Read structure from numbers: per-bar RMS of the mix, the band below
    150 Hz (kick) and the band above 4 kHz (hats). A section change is a
    step in one band.
  - As a blind SFX check, `gpt-audio` names each sound and lists the events
    in a mix window. It caught an opening that sounded like a forest, a
    glass door that creaked like wood, and an unreadable sit. Its prior is
    strong: it called every door wooden, answered "no audio" on two quiet
    beds, and rated almost everything 8–9 of 10.
- Measure each SFX file's onset/peak offset before spotting (e.g. a clack
  with 58 ms of lead silence) and cue by peak, not file start.
- **ElevenLabs SFX misfire on machines and come back quiet on room tone**
  (36 cues for TOWER 42). Footsteps on a steel lift floor came back as
  clanging tools, a turnstile as metal hits, one lift chime as a whistle.
  Room-tone beds measured −36 to −50 LUFS integrated: gain them in the mix.
  The turnstile beep and the lift motor were synthesized instead.

## Video critics
Gemini 3.1 Pro (watches and listens) and Jev (judges): routes, costs and failure modes are in [[critic-models]].

## Video upscaling
- FlashVSR ×3 on fal (`fal-ai/flashvsr/upscale/video`) lifted a 360×640 phone
  reel to 1080×1920 that holds at phone size and at 1:1 on faces and sign
  lettering, far better than Lanczos; detail the source lacked stays soft.
  Price and use were measured on a client branch film.

## Timing QA
- **Measure the beat grid against the real hits on every song.** With
  beat_this on Modal (the default grid) the offset is about −20…+15 ms.
  Record it (`beat_offset_vs_drums_ms`) and shift the grid so cuts land on
  hits ([[music-tools]]).
- **A mix-only grid can sit on the off-beat while its tempo is exact.** On
  a generated 140 BPM groove the local tracker put every beat between the
  real beats. Take the grid from beat_this and check its phase for $0 by
  folding the 30–120 Hz kick-onset envelope modulo the beat period; per-bar
  RMS is too coarse ([[music-tools]]).
- **Re-cut generated takes need per-section alignment.** An ElevenLabs
  groove drifted late against its own grid (kick phase 26 → 41 ms over 8
  bars), so after a bar re-cut the later sections sat 18–35 ms late and
  flammed against SFX placed by peak. Give each placed section its own
  offset, measured with the kick-band fold, until all match within ~6 ms.
- Word boundaries on melisma and fricatives need hand-checking on the vocal-stem RMS envelope; aligner times overlap
  there. Slice bounds should end in an energy dip, not mid-sustain.
- Frame count: use `round(dur × fps)` in both timing and conform;
  mixing `ceil` and `round` drops the last frame.

## Rendering
- **AAC encoding raises true peak by about 0.1 dB,** so master to −1.5 dBTP.
  Swap audio with `-map 0:v -c:v copy`; the video MD5 must not change.
- **Pure Canvas2D pages render ~19 fps locally** on the 2-CPU box, so
  motion graphics need no Modal; Modal is for p5.brush painting. Page
  contract: `window.ready`, async `window.renderAt(t)`, `window.renderSheet`, `DUR`.
- Brand display fonts lack symbol glyphs (✓ ⎇ ⌘ ◉) and the render boxes have
  no system fallback fonts: draw icons as shapes, never rely on glyph fallback.
- **three.js pages:** headless Chrome blocks ES-module imports over
  `file://` and the page hangs with no error. Ship three as a classic
  script (`studio/assets/lib/three.classic.js`, export rewritten to
  `window.THREE`). Locally it needs `--soft-gl` at 2–4 s per frame (sheets
  only); Modal L4 rendered 1980 frames of 1080p30 in ~25–30 s.
- Modal can reuse a warm container with a stale studio tree; after any farm
  render, diff a changed frame against the prior version.

## Delivery and fal CDN privacy
- **fal CDN URLs are public by default**: anything sent through `fal.py
  upload` or produced by a model is readable by anyone with the URL.
  Uploads are for model inputs only, never for delivery (caps below).
- **An exhausted fal balance locks the account:** every model call returns
  403 ("Exhausted balance") until a top-up, which unlocked in about a minute.
- A normal `FAL_KEY` **cannot DELETE** a CDN file (403/404 on every
  endpoint tried). To withdraw one: `PUT
  https://rest.fal.ai/storage/files/acl?url=<url-encoded file url>` with body
  `{"default":"hide","rules":[]}`; the public GET then returns 404.
  This works on uploads and image outputs, but **returned 403 on Seedance
  video outputs**. Those stay public-by-URL, so never share their URLs.
- **Messaging caps.** `send_file` checks the size against the destination before it reads a byte.
  WhatsApp takes 16 MiB and the principal's Vex web chat 64 MB; both refused a 94 MB master.
  - **Over both caps:** the principal chose one full-res `send_file` in the WhatsApp chat, over a CRF 18
    re-render and a lossless split ([[lab-cursor-motion]]). WhatsApp refuses the upload, but the
    web view links the call's path to the workspace Files download, where he gets the file.
  - **Size it before the master render.** 1080p60 at CRF 15 with full-frame camera motion runs
    about 36 Mbps (22 s = 94 MB); dense food photos at HyperFrames delivery quality ran 11 Mbps
    (50 s = 69 MB).
  - **Lossless parts:** stream-copy at keyframes (short GOP), cut by size (under ~58 MiB each);
    joined back, the streams must be MD5-identical (`antioch-1098`).
- **The workspace auto-syncs to git** (`github.com/OWNER/REPO`,
  private: unauthenticated API and web return 404). Any new media path must
  be in `.gitignore` before its first file lands. The music lab committed
  263 MB of audio before rules existed ([[lab-music]]).
  - `git check-ignore` says nothing about files that are already tracked,
    so also check `git ls-files`.
  - Untrack with `git rm --cached`. History keeps the files until a rewrite
    and force push, which needs the principal's yes.

Related: [[music-video-grammar]] (lip-sync framing), [[kinetic-typography]].
