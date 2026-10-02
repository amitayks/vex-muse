---
name: storyboard
description: Plan a music video shot by shot against song.json - sections as acts, one idea per lyric line, the reads timing sheet, composition zones for lyrics vs characters, text mode per line, technique per shot, transitions at every seam, the 2-second hook, attention cadence and escalation - and emit storyboard.md plus machine-readable shots.json that drives plates, painting, lyrics and render. Use in phase 5 of a video project, when re-cutting, or whenever timing or coherence is in doubt.
license: MIT
metadata:
  author: muse
  version: "1.3.0"
---

# storyboard — the video exists on paper first

Inputs: `brief.md`, `audio/song.json`, `research/dossier.md` (line map),
`bible/`, cast & sets. Output: `storyboard.md` (human) + `shots.json`
(machine). No generation or painting before this gate.

## Macro pass
1. Sections from `song.json` → acts (see
   `knowledge/references/music-video-grammar.md`). Write the arc: what the
   protagonist wants, how the world accelerates, the twist, the release.
2. Palette/set per section; the chorus stage and how it escalates each time.
3. The hook (0–2 s): hero text + the most arresting image. The first frame
   is already the thumbnail.
4. The motif and the ending rhyme. Name the **invariant** — the one object/idea the video is
   about — and make each section a different *projection* of it (another view, slice, scale or
   medium); move between sections by changing the view continuously, not by replacing the thing.
   Option: the **Flatland reveal** — lawful partial views first, the whole at the payoff ([[tesseract]]).
5. Thread plan: performance (lip-sync) / narrative / inserts — which thread
   owns each phrase. Lip-sync only where it pays (hook lines, chorus,
   emotional peaks); elsewhere cut away.

## Shot pass (per lyric line or phrase, cut on bars/beats from song.json)
For each shot write:
`id · t0–t1 (snapped to beats) · section · thread · technique (plate |
plate+overlay | plate-through-mask | js-character | js-abstract | hf-type |
hf-graphic | svg-transform | remotion-layer | three | collage | text) · engine
(HyperFrames / Remotion / p5 / Seedance, per [[tool-selection]]) · set · cast · event (what changes) ·
camera · text mode (hero | integrated | subtitle | none) + text zone
(left | right | top | center-stack | in-world) · transition in/out · sfx cue`
and the **reads** table: `start–end · what the viewer must understand ·
where the eye is when it starts`.

## Rhythm plan (write it before the shot pass)
Name the cut pattern per section in bars/beats, shaped by *this* song's energy curve (an
accelerando into a hard stop is one option, not a formula); the ending holds long enough to land.
The motif — taken from this song's world — gets three jobs: open, carry transitions (with a device
that belongs to it), end; each is a shot line. Transformations (`svg-transform`) are written
as `A → B because <meaning>` on a beat.

## Timing law (from the reference repos, enforced)
- Each read gets time to be found, understood, registered: ≥0.5 s for a big
  central obvious read, ≥1 s for small/subtle/new ones; hero text ≥ its
  sung duration + 0.3 s hold.
- Never two important reads at once; cause → reaction in sequence.
- A shot with more reads than time is split or simplified, never squeezed.
- Cut density follows the energy curve (K-pop cadence); vary it.

## Composition law
- Text zone and character zone never overlap; the plate prompt describes
  the calm zone explicitly. Text over footage gets a zone that is dark or
  light enough for its colour (or a local scrim), checked at 360 px.
- One center per frame. Screen direction consistent across a sequence.

## shots.json contract
`[{id,t0,t1,section,thread,technique,set,cast[],event,camera,text:{mode,zone,words:[w indexes]},transition:{in,out},sfx[],plate:{audio_slice:[a,b],offset,prompt_notes}}]`
— times in song seconds; `words` index into `song.json.words` (the lyric
engine reads timing from there, never retyped).

## Self-attack before the gate
Weakest shot? Line with no idea? Seam without transition? Moment where the
eye has nowhere to go? Two reads colliding? A chorus that doesn't escalate?
Fix, then gate.

## Acceptance
Every second of the song belongs to exactly one shot; every shot has an
event, a transition in and out, a text mode, and reads that fit; the hook
is ≤2 s; `shots.json` validates against song.json (t0<t1, beat-snapped,
word indexes exist); spend estimate for plates written.
