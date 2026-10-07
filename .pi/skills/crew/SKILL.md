---
name: crew
description: Open and run a project's own film crew on Vex factory lines - writers' room, casting (one actor per main character who owns its face, voice and every take), extras, production design, cinematographer per shot, sound - as headless workers bound to Muse's skills, with an independent critic station (a different model, Gemini, judging against a rubric) and Muse as director answering every approval gate. Use at the start of any film, scene, teaser or music video with more than a handful of shots or more than one character, when work can run in parallel, or when the principal asks for a crew, casting, actors or a production team.
license: MIT
compatibility: Vex factory (vex.factory.*), FAL_KEY, tools/env.sh.
metadata:
  author: muse
  version: "1.3.1"
---

# crew — a crew per project, Muse directs

The crew is Muse in many sessions. Each worker gets one role, one skill, the project bible and its own
slice; it never sees the rest. Makers never judge their own work: the critic is another model.

## Open the crew (per project `<slug>`)
1. Project folder `projects/<slug>/` with `brief.md`, `bible/` (bible.md, tokens.md), `assets.json`.
2. For each line template in `vex/lines/` (`crew-script`, `crew-design`, `crew-cast`, `crew-shots`) create the project's
   line: same JSON, `name` → `<slug>-script` etc. (`vex.factory.line.create`, from the director's chat).
   Set `dispatchLimit` by budget (scripts 3, cast 3, shots 4–6), `maxItemAgeSec` 3600.
3. Insert items (they start `waiting`; set them `running` only when the director's gate before them passed):
   - script: one item per **angle** (a concept direction) — the writers' room writes in parallel.
   - cast: one item per **character** (main cast) and one per **extras group**.
   - shots: one item per **shot** from `shots.json`, after the storyboard gate.
4. Item data always carries `project` (slug), `dir` (absolute project path) and the unit's id + brief.

## Everything on screen is real (the principal, 2026-10-07)
Every thing the film shows is designed for real first, by a specialist in its own session: a house on a
blueprint gets architects; an aircraft gets an aeronautical engineer; a procedure gets an operator from
that field; a product gets its product designer. The script's **design list** names each one. The
`<slug>-design` line (template `crew-design`, rubric `design.md`) runs one item per unit, with item data
`unit`, `field` (the specialist), `brief`, `script`. Approved specs live in `design/<unit>.md`; cast, set and
frame stations draw from them (item data `spec`), and the director applies any 'Script notes' to the script.

## Set canon (the principal, 2026-10-07)
A set has ONE architecture. From its approved spec, the production designer makes an empty-set canon:
the master view first, then every other camera position as an edit of the master (the master image as
reference + the spec's window, post and panel list named side by side). No set frame is ever made from
text alone; every start frame is an edit of the canon view for its camera. The critic gets the canon
images (`refs`), and I compare architecture side by side at the storyboard gate myself: the critic
misses window and post changes (2026-10-07 test).

## Roles (role card = the station's job; method stays in the bound skill)
| Station | Role | Skill | Output |
|---|---|---|---|
| script.write / revise | writer | `scene-writing` | `scripts/<angle>.md` |
| design.design | specialist (engineer, architect, operator...) | `crew` (this law) | `design/<unit>.md` |
| cast.design | casting director + the actor | `cast-and-sets`, `performance` | sheet, voice id, audition files |
| shots.perform | the actor(s) in the shot | `performance` | driver takes, re-voiced lines |
| shots.shoot | cinematographer | `seedance-plates` (+ field notes) | plate takes |
| *.critic | independent critic | `scripts/critic.py` (bash) | verdict JSON |
| *.approve | director (Muse, as foreman) | — | answer: continue / redo / close |

## Critic station
`scripts/critic.py text|image|video <rubric.md> <out.json> <files…> --ledger <ledger> --context bible/bible.md`
returns pass, score 0–10, per-item scores and located defects. Rubrics live in `references/rubrics/`
(`script.md`, `cast.md`, `set.md`, `frame.md`, `take.md`, `voice.md`; item data `rubrics: {image, video}` overrides per kind; item data `kind: "voice"` selects `voice.md`; the unit's own data is sent to the critic as context). Audio files in a `text` record are played to the critic as one listening reel (video route). A fail goes back to the maker with the defects (the approve gate
answers `redo`); two fails in a row → the director rethinks the unit, never a third blind retry.

## Directing (Muse's job, in the main chat)
- Answer gates from evidence: the maker's output + the critic JSON + one look of my own (sheet, strip).
- Keep continuity myself: shared files (bible, tokens, assets.json, shots.json, edit, mix) are edited only
  by me; workers write only their own unit's files.
- Budget: read the ledger total at every gate; stop a line (`enabled: false`) at the cap.
- the principal sees the checkpoints (concept pick, look + cast + storyboard, v1); everything else I decide.

## Acceptance
Every project line exists with its stations; every item that reached `done` has a maker output, a critic
verdict and a director answer on record; no worker edited a shared file; spend is inside the cap.
