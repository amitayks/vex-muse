---
kind: video
tags: [source, launch-videos, x, motion-design, trend-watch, whatships, agent-video-tools]
audience: design-literate X / AI + dev-tools Twitter / startup launch viewers
half_life: 30
rights: safe
seen: 2026-09-26
---
# whatships.com — what is shipping now (a standing reference source)

**What it is.** A curated directory of product-launch videos posted on X (2,221 published entries as of
2026-09-23, Jan 2024 → now), each with a stable page, category, tags, duration, date, author and the
**original X post**. Plus a tools directory (78: motion editors, agent skills, AI video) and a studios
directory (7 launch-film studios/freelancers). Categories: ai 897 · developer-tools 436 · other 327 ·
design 207 · consumer 135 · productivity 92 · hardware 80 · motion 47. It is *the* place to see what
design-literate X is watching this week — i.e. what our audience's eye is already tired of.

**Use it for:** (1) research — who solved this kind of shot recently, how; (2) the style-bible
divergence gate — what is saturating right now; (3) a quick review — does our cut look like this
week's launches? It is not a style to copy ([[anti-slop]] → trend echo).

## Access (tested 2026-09-26)
| Surface | From this box |
|---|---|
| `whatships.com/llms.txt`, `/llms-full.txt`, `/robots.txt` | 200 — the site's own agent guide (crawl contract, citation policy) |
| `/openapi.json`, `/search-index.json`, `/sitemap.xml`, `/videos/<slug>/` (incl. `Accept: text/markdown`) | **403 (Cloudflare)** for every user-agent tried; the Vex `read` tool (web reader) can fetch them |
| Public repo `github.com/dingyi/whatships.com` → `src/data/videos.json` (+ `tools.json`, `studios.json`) via raw.githubusercontent.com | **200 — the full catalog**: title, product, company, category, tags, `publishedAt`, `durationSeconds`, `views`, `tweetUrl`, `videoUrl`, poster path, status. Posters at `public/posters/<slug>[-960].webp` |

Tool: `.pi/skills/reference-mesh/scripts/whatships.py` (stdlib; cache `research/whatships/`, 24 h):
```
whatships.py find "svg animation" --cat motion,design --days 14 --sort views --limit 10
whatships.py show cube-motion              # full record + page + a ready citation line
whatships.py wall --cat motion,design --days 14 --cols 6    # numbered poster wall + legend .txt
whatships.py fetch tesseract cube-motion --study            # xfetch the X post, then framestudy
whatships.py tools motion | studios | cats | sync [--from saved.json]
```
`--from` accepts a saved `videos.json` or the site's `search-index.json` (that one has no dates and no
X URLs — fallback only). Rules from the site: cite **both** the directory page and the original X post;
it is not a video CDN — `fetch` pulls the video from the original post via `xfetch.py`, for study in
`research/` only, never re-hosted.

## Snapshot 2026-09-26 — Motion + Design, Sep 14–22 (11 sampled, 4 watched)
Poster wall of 24: `research/whatships/wall-2026-09-26.jpg` (+ `.txt` legend).
Watched (xfetch → framestudy; evidence in `research/x/<author>-<id>/`):

- **Tesseract — Mirage** ([page](https://whatships.com/videos/tesseract/) · [X](https://x.com/trymirage/status/2102429594804429138),
  32 s, 1.8 M views). 44 shots, avg 0.73 s, 21/43 cuts on the beat (120 BPM). A 9 s held opening
  (a CRT in a night study typing "We rebuilt After Effects and Premiere for agents") → a wireframe cube
  becomes nested cubes → the agent transcript → **Muybridge's horse in ~15 treatments** (glass, film
  burn, onion-skin silhouette, low-poly, halftone, pixels, wire mesh, ASCII, skeleton, thermal) → a
  node graph (SOURCE/TIMING/TYPE/FRAME/EASING/SOUND/MIX) on a synthwave floor → a cut burst every
  ~0.17 s (20.5–27 s) → gradient-blur end card. *Principle:* one subject, many treatments — the range
  of the product with zero confusion, because the silhouette never changes (see [[tesseract]], "one
  object, many projections").
- **Cube Motion — Daniel White** ([page](https://whatships.com/videos/cube-motion/) · [X](https://x.com/dwhitedesign/status/2102014506192851303),
  35 s, 70 k views; "every frame is an SVG drawn in JavaScript"). 4 shots, 54 % held. One dot-particle
  system becomes everything: sphere → UI cards → the word *move* → *more* → a cube; chapter titles
  are the API (`rise()` `leave()` `morph()` `reveal()`); lavender on near-black; iris to off-white
  for the wordmark. *Principle:* one medium carries every state — transitions are re-formations, not
  cuts.
- **Code2Video Bench — HyperFrames** ([page](https://whatships.com/videos/hyperframes-code2video-bench/) · [X](https://x.com/HyperFrames_/status/2102084939026247684),
  88 s, 1.65 M views). 75 shots, avg 1.18 s. A **two-tier clock**: cuts on a strict 0.25 s grid for
  the first 12 s, then section changes every 4.0 s (16, 20, 24, 28 … s). Quoted tweets as evidence
  ("Motion design is dead!?"), report-card tables, terminal logs, a dot sphere as "the judge", a
  founder talking outdoors with integrated captions, A/B choice UI, tilted card walls, mint on black,
  a small bottom subtitle track throughout. *Principle:* a fast inner grid inside a slow outer grid —
  speed without losing your place.
- **Glyph — pmndrs** ([page](https://whatships.com/videos/glyph/) · [X](https://x.com/pmndrs/status/2100980802091708818),
  15 s). The wordmark as a physical toy: jelly letters on an icon wallpaper, an object knocks them
  over, a black hole eats them. Maximal colour on off-white — the loudest thing in the set.

Metadata/poster only: Quiver 2.0 (Paper, SVG generation, 305 k), Bot avatars (18 animated 3D bots,
zero-dep), Framer Skills, Motion Studio, ASCII Magic v2 (ASCII shader presets), SF Interface Numbers
(number-roll component), Launchvideo (agent skills for product videos). **The headline category this
month is "the agent makes the video"** (Tesseract, Code2Video, Motion MCP for ChatGPT/Codex,
Launchvideo, Diffusion Studio MCP, Powermove, Higgsfield) — and every such film says "made with".

## Saturating now (merged into the fingerprint in [[code-motion-showreels]] and [[anti-slop]])
Dot-particle solids that re-form (sphere → UI → word) · the agent transcript / prompt box typing as a
story beat · quoted-tweet cards as evidence · retro CRT + terminal green · Muybridge's horse as "motion"
· function-name chapter titles · a single mint or lavender accent on near-black · gradient-blur end
card · tilted walls of UI cards · "made with <tool>" as the thesis.

## Limits
Curated and X-only: heavy bias to AI / dev-tools launches; not music videos. Categories are editorial
labels. `views` is missing for the newest week (captured later). Text search in the script is a plain
AND of substrings. Only the documented flags work (`--cat`, not `--category`). An unknown flag used to be
silently ignored and returned unfiltered results; since 2026-09-26 it errors instead. The 403 means the script depends on the public repo staying public — if it
disappears, save `search-index.json` with the web reader and use `sync --from`. The catalog's
`authorHandle` / handle in `tweetUrl` is the credited account, not always the poster (X resolves a status
URL by id alone): `sf-interface-numbers` is filed under `wherescz` but was posted by `@wheresryan22`.
`fetch` therefore names evidence folders by the real poster (`research/x/<poster>-<id>/`, xfetch's own
convention), so look them up by tweet id, not by the catalog handle.
