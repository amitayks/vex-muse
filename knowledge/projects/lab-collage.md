---
kind: project
seen: 2026-09-26
---
# lab-collage — the paper-collage explainer, studied and rebuilt in code (Sep 2026)
Brief: the principal sent @omarsar0's post of a Pexo AI video (30 s vertical "rise of Microsoft", torn paper,
halftone cutouts, stickers, big blue years, page transitions) and asked me to analyse it, work out how
to recreate the style, and save that as a skill and knowledge I can reuse.

**Worked**
- `framestudy.py` plus full-res crops broke the reference into numbers: 7 chapters of about 4.3 s each, 17 % holds, stop-motion pop-ins, and no beat-authored cuts. They also exposed how it was made: one image-model page per chapter, then a video model interpolating between pages. The tells are garbled small text ("ALBUQVERQVE"), a header cropped by the camera, and letters that morph mid-shot.
- The code-first rebuild beat it on every axis the generated route loses:
  - DOM type, spelled right and stamped on the beat.
  - 15 fps stepped builds under a smooth camera.
  - A depth sandwich (the year sits between the room and the teen, via a SAM 3 subject mask).
  - A zoom-through with the cassette carried across the cut into chapter 2.
  - A coded page peel into the end card.
  - The carried cassette lands again on the title card, so the ending rhymes with the opening.
- Procedural paper, tape and ink cost $0. The only paid work was 4 Nano Banana Pro assets.
- Render: 18.3 s of 1080×1920 at 30 fps in 3–5 min (draft, 2 workers, software GL).

**Didn't / lessons** (all folded into `collage-motion` LEARNINGS)
- Bria kept 97 % of a busy room as foreground; SAM 3 with the prompt "person" gave a clean subject mask for $0.005.
- Round-cap marker strokes painted dots before their draw started.
- The progress row showed before its page arrived.
- Rays and clones stacked above the headline cut through "COPIES".
- Torn strips had saw-tooth ends and corner spikes. The fix: edge points per ~9 px of the measured size, and corners shared between edges.
- The end-card payoff cassette first covered the "E" of "HOME".
- The first 0.9 s was only paper, so the hook was pulled earlier.
- In v3 the chapter 2 caption finished typing 0.1 s before the peel, so it could not be read. The v4 fix pulled chapter 2's last builds one beat earlier and moved the peel one beat later, which gives about a 1 s hold. The bed was recut to 18.6 s to cover the extra beat.
  - Rule now in the skill's review gate: measure a hold from the caption's last typed character (start + chars/cps), never from the last slap.
- Known limits of v4:
  - The first 0.4 s is only the page and the blue strip. The hero and the headline land by 1.1 s, which is inside the 2 s rule but not an instant hook.
  - It is a draft render on software GL; no final-quality render was made for the lab.
  - "Living photos" (a Seedance plate inside a torn frame) are described in the skill but untested.
- fal.py counted SAM's repeated mask URL twice; it is now fixed to count unique URLs.

## Outputs
- **Renders:**
  - `projects/lab-collage/renders/collage_v4.mp4`: the accepted draft.
  - `collage_v1`–`v3`: earlier drafts, reviewed in `review/v1`–`v4`, with notes in `review/notes.md`.
- **Skill `collage-motion` 1.1.0** (new):
  - `scripts/cutout.py` and `scripts/paper.py`.
  - `assets/collage-template/`, containing `collage.js` and the lab comp as the mechanics scaffold.
  - `references/prompts.md` and `references/recipes.md`.
  - LEARNINGS.
- **Reference:** [[paper-collage-explainer]].
- **Routing:**
  - [[tool-selection]] row.
  - mv-director 1.3.1, step 7.
  - fal-media 1.2.0: SAM 3 row, unique-URL cost count.
- **Spend:** $0.623 actual. The ledger shows $0.628 because the SAM double count happened before the fix.
- **Delivery (2026-09-26):**
  - Sent to the principal's web chat with `send_file`: the full-quality `collage_v4.mp4` (13 MB, 18.3 s, 549 frames) and the plain-language report `outbox/collage-style-study.md`.
  - Review log: `projects/lab-collage/review/notes.md`.
  - Filed on spine matter `muse-studio` as a status encounter with refs file:1761–1764 (render, SKILL.md, reference note, report). The next action is the principal's review of the video.

## How the principal works with this
He points at a piece he likes and wants the *capability*, not a copy. The reference's cobalt/cream "RISE OF" look is recorded as a fingerprint to avoid by default; the skill parameterizes palette, type, paper and transitions per project.
