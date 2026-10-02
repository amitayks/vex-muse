---
name: reference-mesh
description: Research and grow Muse's reference compendium - audit the live zeitgeist of a target audience (memes, events, in-jokes, the words around them), study music videos and motion design for technique, and map every lyric line to recognizable visual anchors. Use in phase 2 of any video project, when a brief names an audience or culture (e.g. SF tech Twitter, K-pop fandom), when asked "what's the vibe / what are people posting" or what is shipping now in motion and design (whatships.com launch films), or when the library lacks references for a technique.
license: MIT
compatibility: Web read (URLs, X posts, YouTube pages), steel browser for pages that need a real browser; image read for screenshots.
metadata:
  author: muse
  version: "1.3.0"
---

# reference-mesh — anchors the audience already carries

A reference works only if the viewer decodes it in under a second. Research
is not mood-boarding; it is finding the shared images already in the
audience's head and the techniques that make images land.

## Library (`knowledge/references/`) — one file per entry, tagged
Front matter: `kind` (meme | event | person-archetype | technique | video |
style | typography | sound), `tags`, `audience`, `half_life` (days it stays
fresh), `rights` (safe | parody | avoid), `seen` (date checked live).
Body: what it is · why this audience knows it · **visual signature** (how to
draw/stage it so it reads in 1 s) · the words/captions that travel with it ·
where it has been used well · links. Index: `knowledge/references/_index.md`.
Seed files are there already (music-video grammar, K-pop direction,
kinetic type, anti-slop, internet-brutalism) — read them before researching.

## Zeitgeist audit (per project)
1. Define the audience in one line and its home feed (e.g. SF tech on X).
2. Pull the last ~90 days: top posts and quote-chains on the topic, recurring
   screenshots, charts and phrases; Know Your Meme / Reddit for meme lineage;
   news for the events people cite. Read the actual posts, not summaries.
   Tech / design / AI audiences: also pull the last 14–30 days of launch films
   (`scripts/whatships.py`, below) — it is what their eye is already tired of.
3. For each candidate: is it still alive (half-life vs today), is it
   visually encodable, what's its rights risk?
4. Keep 15–30 entries. Rank by decode speed × emotional charge × fit to the
   song's arc (anticipation → acceleration → vertigo → release, or whatever
   the song's arc is).
5. Write `research/dossier.md`: the ranked list + the **line map** — every
   lyric line → 1–3 anchors (or a deliberate no-reference image) + the
   feeling it should carry. Lines with no idea are flagged for the storyboard.

## Pulling X posts and videos (no paid API)
`python3 scripts/xfetch.py <x.com status URL> [--out DIR] [--sheet-fps 2]` → post.json/post.md
(text, stats, quoted post), images, `video_N.mp4` (best bitrate) + audio, and 6×4 contact
sheets to read in order. Default DIR `research/x/<author>-<id>/`; videos stay out of git.
Read-only; posting to X is never done from here (rails in AGENTS.md).

## What is shipping now (whatships.com)
Curated X launch films (2.2 k, dated, categorised, each with its original X post). Knowledge +
current fingerprint: [[whatships]]. `python3 scripts/whatships.py`:
`find [text] --cat motion,design --days 14 [--sort views]` (rows + X URLs) · `show <slug>` (record +
citation) · `wall … --cols 6` (numbered poster wall + legend) · `fetch <slug>… [--study]` (hand-off to
`xfetch.py` then `framestudy.py`) · `tools` / `studios` / `cats`. Data comes from the site's public repo
(the site's JSON answers 403 here); `sync --from FILE` takes a saved `search-index.json`. Cite the
directory page and the original X post; videos are for study in `research/`, never re-hosted.

## Technique study (when the library lacks it)
Watch the reference with `$PY scripts/framestudy.py <video> [--fps 6] [--out DIR]`: timecoded
sheets, a 960 px key frame per shot, a strip for every transition (every 2nd frame, −0.15…+0.25 s),
`motion.png` (motion energy vs cuts vs audio onsets/beats) and `study.json` (tempo, beat phase,
cuts-on-beat, hold share, 5-colour palette per shot). Read study.json → motion.png → sheets → strips
→ keys, crop full-res frames for HUD/type/texture detail, then write a technique entry: what the editor/
director is doing with attention (cut rate vs bar, framing, color blocking,
text placement, callbacks), the rule behind it, and how to reproduce it with
our tools. Intent, not description.

## Rules
- Recognizable beats clever. Obscure references are for the second viewing,
  never the hook.
- A meme is a visual grammar, not a stock asset: redraw it in the piece's
  style unless the brief calls for raw internet-collage inserts (then crop,
  degrade and frame them deliberately — see internet-brutalism entry).
- Real people: allude by archetype, costume, prop or silhouette; no
  photoreal likeness of real people in generated plates.
- Stale is worse than absent: check `seen` against today; re-verify anything
  older than its half-life.

## Acceptance
`research/dossier.md` exists with a ranked anchor list (each with decode
line + rights), every lyric line mapped or flagged, and new/updated library
entries written with `seen` = today and indexed. Tech/design audiences: the dossier
names what is shipping now (a whatships pull dated this week) and which of it to avoid.
