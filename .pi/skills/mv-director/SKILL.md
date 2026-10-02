---
name: mv-director
description: The master workflow for making a music video, lyric video, animated short or any audio-driven visual piece end to end - expand a one-line ask into a full Director's Brief, then run the gated pipeline (song map, research, style bible, cast and sets, storyboard, base plates, painted overlay, kinetic lyrics, sound design, render, review) with budgets, checkpoints and a watch-it-like-a-stranger final gate. Use whenever the principal asks for a video, a remake/remix of an existing video, a visual for a song, or sends a track, a reference video or a repo and says "make something like this / better than this".
license: MIT
metadata:
  author: muse
  version: "1.3.1"
---

# mv-director — from a one-line ask to a finished cut

A request is never too short. I expand it into the Director's Brief below,
fill every field I can decide myself, and ask only the **blockers**. Then I
run the phases in order; each phase has an artifact and a gate. I never skip
a gate because I'm excited (that's M7/M8).

## 1. The Director's Brief (`projects/<slug>/brief.md`)
Template: [references/brief-template.md](references/brief-template.md). Fields:
- **Source**: audio file (exact master used for the final encode), lyrics,
  any reference work (video, repo, post) and what specifically is admired in it.
  No audio is not a blocker: the song can be **fetched** (a named track, a
  link, a type beat or OST — `music-source`), **picked from the library**
  (`musiclib.py ls`), or **generated** (`music-gen`: a beat, a score with
  cue points, or a sung song with lyrics I write) — and cut to the video's
  length on its bars (`track-edit`). I choose, and say which in the brief.
  A reference video is frame-studied before the brief is written
  (`reference-mesh/scripts/framestudy.py`: tempo, cut grid, holds, palette,
  transitions) — admire it in numbers, then push past it.
- **Destination**: platform + audience (e.g. X / SF tech timeline; YouTube;
  IG vertical), aspect(s), max length, loudness target.
- **The one feeling** the piece must leave, in one sentence.
- **Hook**: what happens in the first 2 s that stops the scroll.
- **Concept**: the world, the protagonist (who they are — often the brand or
  the artist personified), the arc across the song, the motif that pays off,
  and how the ending rhymes with the opening.
- **Look**: the style direction (decided in `style-bible`), what it must NOT
  look like, anchor references the audience will recognize.
- **Technique mix** — engine per layer, chosen by each shot's read
  ([[tool-selection]]): code motion graphics in HyperFrames (type, graphics,
  UI, HUD, SVG transformations — the default and the compositor), Remotion
  layers (data-driven / spring / audio-reactive, transparent WebM), painted
  p5 (hand-made worlds, acted characters), generated plates (performance,
  lip-sync) shown raw, through SVG masks or painted over, internet-collage
  inserts. Any mix is legal; the brief states it and names the combo move
  (e.g. plate seen only through the motif mask).
- **Motion brief** (for every code-motion part): tempo grid, the motif's three
  jobs (open / transition / end), palette as hex, type system, chapter list,
  rhythm plan, transition rule, texture, frame chrome, end card —
  `code-motion/references/motion-brief.md`. The craft bar to beat:
  [[code-motion-showreels]] — its principles, never its look.
- **Originality**: the look is invented from this song (`style-bible` →
  Divergence: 3 song-derived directions + a wild card, attacked against
  recent references and my last project). References inform craft only.
- **Text plan**: lyric typography modes (hero / subtitle / none) and where the
  hero moments are.
- **Budget**: spend cap (default $150), render budget (hours), deadline.
- **Rights flags**: song, likenesses, marks, memes — one line each.
- **Blockers** (the only questions I ask): audio only when a specific master
  or version is required (otherwise fetch/generate it), platform, cap,
  deadline, anything with rights risk that changes the concept.
If the ask comes with a long, specific prompt: every explicit requirement in
it becomes a checklist line in `brief.md` → `## Requirements` and is re-read
at the final gate.

## 2. The pipeline
| # | Phase | Skill | Artifact (in `projects/<slug>/`) | Gate |
|---|---|---|---|---|
| 0 | Brief | this | `brief.md` | blockers answered |
| 1 | Song | `music-source` / `music-gen` → `track-edit` → `song-map` | `audio/master.wav` + source.json or brief, `audio/song.json`, stems, lyrics | master chosen and fitted to length; tempo + downbeat + word checks pass |
| 2 | Research | `reference-mesh` | `research/dossier.md`, refs in `knowledge/references/` | every lyric line has ≥1 visual idea with a recognizable anchor |
| 3 | Style bible | `style-bible` | `bible/bible.md`, style frames | 6 test frames on the real models read as one world, no slop |
| 4 | Cast & sets | `cast-and-sets` | `cast/*/sheet.png`, `sets/*.png`, `assets.json` | on-model across 3 poses + 3 expressions; sets leave room for text |
| 5 | Storyboard | `storyboard` | `storyboard.md`, `shots.json` | reads fit their time; hook ≤2 s; a transition at every seam |
| 6 | Base plates | `seedance-plates` | `plates/<shot>.mp4`, `plates/qa/` | draft passes sync + content check before finishing |
| 7 | Build layers | `code-motion`, `svg-transform`, `kinetic-lyrics`, `collage-motion`, `p5-paper-engine`, `rotoscope-paint` | `motion/<comp>/` (HyperFrames), Remotion layers, `scenes/*.js` (studio) | snapshots / sheet per shot reviewed; every transformation on its beat |
| 8 | Sound | `sound-design`, `js-scoring` | `audio/sfx/`, `audio/mix.wav` | vocal never masked; LUFS target hit |
| 9 | Composite, render & review | `code-motion` (HyperFrames master), `render-review` | `renders/vN.mp4`, `review/vN.md` | frame study + rubric ≥ bar on every line; I watched the whole file |

Present to the principal at three checkpoints only (don't wait on him in between):
(a) after phase 3–4 — bible + cast sheet + storyboard summary, one image
each; (b) first full cut (v1); (c) final. He can steer anywhere; silence
means continue.

## 3. Parallel work
Long projects split into chapters (song sections). For real parallelism I
create a factory line (`vex.factory.line.create`, read the Vex factory docs
first) named `mv-<slug>-chapters`: one item per chapter, one agent station
per step that binds a skill + acceptance (`skill:p5-paper-engine` → "sheet
per shot reviewed, no page errors"), `dispatchLimit` 2 (this box has 2
CPUs). Each worker gets ONLY: the bible, its `shots.json` slice, the engine
guide, its chapter file path, and the acceptance check. I stay the director:
I integrate, keep continuity, and own the final gate. Shared files (engine,
cast code, timing, lyrics engine) are edited by me only. Small projects: no
line, I build sequentially.

## 4. Budgeting
- Money: estimate before phase 6 — `n_shots × avg_seconds × rate × takes`
  (assume 2.5 takes per plate at draft, 1 finish). Must fit the cap.
- Time: renders are the long pole (see `render-review`); schedule renders
  as background executions and keep working.
- Disk: frames are temporary. `df -h /data` before any render.

## 5. The final gate
Re-read `brief.md → Requirements` line by line against the actual file.
Watch the full render twice (once as a stranger at full speed; once
scrubbing). Screenshot every lyric line. Grade with the rubric in
`render-review`. Anything below the bar goes back — to the phase that caused
it, not patched at the end.

## Acceptance
Done when the final MP4 is delivered to the principal, `review/final.md` shows every
requirement mapped to evidence (timestamp or frame), the ledger total is
within the cap, and the rubric passed. Then append the project's lessons to
the relevant skills' LEARNINGS.md and a one-paragraph project note to
`knowledge/projects/<slug>.md`.
