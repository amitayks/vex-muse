---
kind: video
tags: [case-study, claude, seedance, lip-sync, identity, 2.5d, multi-agent, lyrics, method]
audience: SF tech X
half_life: 365
rights: reference-only
seen: 2026-09-29
summary: Full production record of anabology's 5-min Claude-made lyric video ESCAPE VELOCITY (Midjourney + Suno + Seedance + JS engine) and what it adds to our method — time-resolved lip-sync divergence with cover clips, colour kept in generation, identity without omni-ref, a 2.5D depth tier, and a judged multi-agent workflow with its token bill.
---
# Case: "ESCAPE VELOCITY" (anabology, Sep 2026): the full production record

Source: a public Drive folder named "Slopcore" (owner anabology), sent by the principal 2026-09-29:
drive.google.com/drive/folders/1OKYaR5Kv5lOeIROUtigpPZtCWauUJ01y.
Mirrored in [media/escape-velocity](media/escape-velocity/README.md.pdf): the write-up PDF,
the director's log, orchestration (the agent workflow code), every Midjourney, Seedance and Suno
prompt, the final-frames sheet, the casting sheet and the lip-sync check plot. Not mirrored: the
1.61 GB master and the `audio/` and `midjourney/` subfolders, because of the disk law.
Access note: Drive returned "quota exceeded" for every direct download. The viewer route worked:
`/file/d/<id>/view` → `itemJson[9]` → JSON `pdf` URL. Images come through `/thumbnail?id=<id>&sz=w2000`.

## What it is
A 5:06 lyric video. It is a techwear fashion show where each "Look N" is an SF-tech meme, walked
by a Claude-coded model. A split-flap countdown ("18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS") flips
to "THERE IS NO UNDERCLASS" and the catwalk lifts off. It was made in about 19 h by Claude Code
(Opus 5.5, 1M context), with one human director who sent about 50 messages. Midjourney v8.2 made the
plates, Suno v6 the song, Seedance 2.5 the moving shots (through OpenRouter), and a JS canvas + WebGL
engine drew every word, HUD, graphic and 2.5D move on the beat. Same lineage as [[claude-pop-case]]:
it started from the donald "one prompt", which is reproduced verbatim in orchestration.

Numbers: 141 shots in 9 chapters · 188 MJ prompts, 636 images, 130 plates used · 47 Seedance clips
+ 30 cover clips, 91 submissions, 421 s at 720p, ≈ $93 · 7,354 frames at 1080p, ~63 min on 4 cores,
CRF 16 · tokens ≈ $626 at API price (not paid: Max plan).

Look ([frames sheet](media/escape-velocity/frames-final.jpg)): photoreal MJ plates under
a dense CV/HUD layer (tracking boxes, model cards, garment tags, split-flap chrome). Type modes are
subtitle, coverline beside her, masthead giant word, and a mass of micro text in the drop. The
colour arc goes night blue-black with one red lamp → dawn → high-key white paper.

## What it adds that we did not have

### 1. Lip-sync QA over time, not one global lag (supersedes our platecheck method)
- **Mechanism.** Seedance copies @Audio1 into its own soundtrack, and the mouth follows *that*
  soundtrack. When the copy drifts from the reference partway through, the mouth drifts with it.
  Before the drift the clip is in sync. The director spotted this from the spectrogram.
- **Check** ([plot](media/escape-velocity/lipsync-check.png)). Compare the clip's own
  soundtrack against the vocal we sent, over time:
  - a sliding spectral match curve;
  - a waveform NCC (a verbatim copy scores high);
  - a cross-similarity matrix (the in-sync part shows as a diagonal);
  - a local timing-offset curve.
  The pass threshold was 0.68, set above the null p90 of 0.54 rather than picked by hand. The
  output is a divergence time, not a single lag.
- **Repair.** Cut on the last eighth note before the divergence. A **cover clip** takes over from
  that frame: same prompt, window re-cut to start at the cover point. Plan every sung passage as a
  chain of such windows with alternating framings (CU / MCU / MS / profile), so each cover cut
  looks designed. LatentSync was the fallback only.
- **Result.** ≈ 86 % of sung seconds verified in sync. Covers are not free: 30 covers for 47 clips,
  and some windows took 3–4 covers at the same start (SD09, SD20, SD23), usually on held notes.
- **On our own plates** the waveform NCC stays low (r ≤ 0.36) because Seedance re-synthesises
  the copy rather than pasting it; the log-mel match curve is the signal that works. Measurements
  in [[generation-field-notes]].
- **Why this matters to us.** Our `platecheck` measured one onset-envelope lag, and our own
  LEARNINGS already recorded that it aliases on the beat period. Adopted 2026-09-29 as
  `seedance-plates/scripts/syncdiverge.py` (skill 1.1.0). It added a `glitch` verdict (dips that
  recover) and a `no_copy` verdict (the plate's SFX drowned the copy). Results on our plates are in
  [[generation-field-notes]].

### 2. Seedance prompts and windows that worked
- Sung clip, verbatim pattern (the exact words sung in the window, quoted):
  `@Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in time: "<words>".`
  Then framing, one physical action, camera. Always end with `Locked camera, no cuts, no head turns.`
- Windows are 4–8 s, **start inside a word gap** (never mid-word) and quote only the words inside them.
- Motion clips (not sung) get the full mix as @Audio1 so the moves land on the beat. They end with
  `Her mouth stays closed, face expressionless.`
- **No two clips start from the same frame.** Continue from the previous clip's last frame or
  use another plate. Otherwise the cut is jarring (director's note).
- She sings **most** lines, not all ("like Grimes vids").
- Plates were 720p, and `generate_audio: true` was kept on because the soundtrack is the sync evidence.

### 3. Colour goes into generation; the look is applied in post
- Seedance clips started from monochrome, print-graded frames came back grey.
- v1 was rejected: "way too gray … loses the Midjourney magic." The global low-saturation
  xerox/dither pass had flattened the whole video.
- Fix: a colour halftone instead of the desaturating print pass, and exemplar video colourisation
  (Deep Exemplar, CVPR 2019) using each shot's own colour plate as the exemplar.
- **Rule:** start frames and plates stay in full colour. Halftone, dither or print looks are
  compositor layers that must not flatten saturation across the whole video.

### 4. Keeping the lead on-model when there is no omni-ref
Tried in order:
- **GPT-image identity pass:** drifted out of the plate's look (it left MJ's latent space).
- **Face sheet as an image prompt:** over-conditioned. It put a close-up-sized head on a distant
  figure, and a whole sheet imported its multi-head layout, so crop to a single face.
- **Distance ladder:** the character on a plain studio floor at CU / MS / FS / WS / EWS. Image
  weight fell with distance (iw 1.0 / 0.6 / 0.4 / none / none), because far away the face matters
  less.
- **What held:** the full written canon in every prompt, the framing word first, where she stands
  in the frame, and an explicit ethnicity and skin descriptor. Without that descriptor MJ turned her
  Asian in 12 of about 25 plates.

For us: `cast-and-sets` feeds a turnaround sheet as @Image1. Expect the same big-head failure at
wide framings, and give wide shots a distance reference or text only.

### 5. The 2.5D tier (between a still and a paid clip)
- 130 plates against 77 clips. Most stills became **2.5D shots**: a depth map drives parallax and
  layer separation, 2–4 stills of the same shot are swapped on the beat, and CV boxes (Grounding
  DINO) track her as part of the HUD layer.
- Failure mode: repetition. The same still ran across 6–8 shots near the end (white-cu ×8,
  gantries ×7, takeoff ×6).
- Rules that came out of it:
  - never the same treatment on two consecutive 2.5D shots;
  - at least 5 treatments per chapter;
  - replace repetitive panels with pure motion design.
- We have no depth-parallax tier. It is the cheap way to put a performance-free plate in motion.

### 6. The multi-agent production pattern (with its bill)
- **Research:** 5 parallel sweeps (recent events, longevity, deep SF memes, exact timeline quotes,
  fact-check of the old draft). Then an **adversarial verifier** tries to refute each item and
  defaults to "unverifiable". Items with recognisability ≥ 3 are checked. Only *confirmed* or
  *wording-fix* facts may enter a lyric. The output is a ranked bank with a one-glance visual per item.
- **Lyrics:** 4 writers with different angles (density, tension, hook, fashion) → 3 judge lenses (a
  timeline user, a topliner, a ruthless editor) → a merger → a critic that counts syllables per bar
  (spoken deadpan at 128 BPM holds about 6–10 syllables per bar).
- **Storyboard:** 3 directors (fashion film, meme density, narrative) → 3 lenses (viewer/director,
  taste, producer) → a head director who writes `shots.json`. That file must tile 0–306.4 s with no
  gaps, snap to the beat map, cover every lyric line and keep the lead on screen ≥ 70 % of the time.
  Mid-run UPDATE blocks told the agents about late discoveries (the lip-sync method, the identity rule).
- **Animation:** one animator per chapter, restricted to its own file → an art director that
  renders and *reads contact sheets* (≤ 14 fixes, pass flag) → a fixer. Hard gates: `render lyrics`
  N/N tokens on screen, ≤ 1500 ms/frame, pure functions of t, `hash()` not `Math.random`.
- **Cost:** 48 % animation ($301, 40 agent runs, 3,145 tool calls), 30 % main session, 15 %
  storyboard, 7 % research. **96 % of tokens were cache re-reads**, and the main context sat at
  about 565k tokens. The cost driver is context size × number of calls, not images (under 4 %).

### 7. Song
- Suno v6 custom mode. The style prompt, the exclude list and the lyrics field are all in
  `prompts-suno`.
- Deadpan spoken verses carry the references, so nothing is stretched over a melody. The sung
  euphoric chorus carries the turn. Acronyms are spelled out for the singer ("A G I").
- The chosen take drifts in tempo, **131.5 → 133.9 BPM**, so every cut uses the beat map and never
  a fixed tempo.
- Word timings come from **wav2vec2 CTC forced alignment of the known lyrics** (character
  posteriors plus Viterbi). When we wrote the lyrics ourselves this should beat chunked Whisper.
  Not yet tested here.

### 8. Director notes worth keeping (from the log, paraphrased except where quoted)
- The bar: motion design that *explains the words*, "not just animated lyrics."
- Transitions: "Edgar Wright level … but also not overdone and amateurish". Mostly hard cuts on
  the beat, with a motivated device every few shots and never the same device twice in a row.
- "Do the Seedance prompts only when sure they will work."
- Show a short clip with audio before running the expensive repair.

## What does not transfer
- Midjourney (they drove it through the director's logged-in browser) and Suno: we have neither.
- The Higgsfield/OpenRouter route for Seedance: we use fal.
- The MJ prompt *family* is still a good template:
  concrete scene + framing + where she stands + a declared empty field for type + a fixed
  palette/grain/finish suffix + `no text, no letters, no logos`.

## Unread lead
Nick Khami (@skeptrune), "How I made Palmer Luckey and Paul Graham perform Hotel Lobby": the Seedance
2.5 audio-reference lip-sync trend that convinced the director it could be done. Not fetched yet.
