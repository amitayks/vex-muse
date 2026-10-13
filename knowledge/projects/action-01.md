---
kind: project
seen: 2026-10-10
tags: [ai-film, crew, factory, action, dialogue, blender]
summary: "action-01, BACK IN TWELVE: the first film made by Muse's crew on Vex factory lines (writers' room, specialists, casting, 33 shots with a critic and a canon self-gate). v1 cost $151.63 of $180; the principal marked it a test, not for publishing, and parked the project until Blender is connected, because movement must come from a Blender scene with AI painting only the look."
---
# action-01: BACK IN TWELVE (crew test, parked for Blender)

**Brief.** After [[lab-cinematic]], the principal set the [[masters-of-the-air-case]] clip as the bar: "Lets take that video in the post, that is the goal in making action. Perfection, just like that." He asked Muse to run each project with its own crew of headless sessions on Vex factory lines, "And you stay as the director." He added: "Real product. Everything." The writers' room wrote three 60 s scripts; the principal picked BACK IN TWELVE (a water bomber in a fire canyon) over THE SLOT and TWO ON THE WIRE. The $150 default cap was raised to $180 at his yes.

**The piece.** A ground crew is trapped on a ridge saddle when the wind turns a wildfire onto them. The lead plane goes blind in the smoke. Captain Brandt drops Tanker 92's load alone, onto the crew. Silence. Then Kovac answers, coughing: all twenty alive, wet. "Copy, Bravo. Back in twelve." 33 shots and 29 lines over intercom, radio and an open-air speaker mic.

**What worked**
- **The writers' room was fast and cheap:** three scripts, each critic-checked, revised and approved, in about 12 minutes for $0.14.
- **Specialists before pictures.** Six specialists (aircraft, cockpit, lead-plane pilot, fire behaviour, aerial-firefighting ops, hotshot crew) wrote specs in `design/*.md` that fixed the geography and the radio procedure. Where a per-camera side map existed, space held across cuts.
- **Code over a locked frame.** The best shots cost $0 in generation: rigid cockpit locks, physical pushes from an approved frame and composites. This is the Blender route in miniature.
- **The canon self-gate** (per-spec yes/no checks against the set masters, [[critic-models]]) caught most continuity faults before the director, and several shots passed with no director fix.
- **The mix.** Sound perspective switches per cut, three voice treatments, and a score that stops for the silence before Kovac's answer. The critic said the silence works.

**What didn't**
- **AI video movement.** Bodies overshot their harnesses, smoke ran backwards, water floated like milk and props and faces morphed ([[generation-field-notes]], Kling image-to-video). Many takes were saved only by code.
- **Sets drawn from text drifted.** The cockpit's windows changed between frames, and a reverse shot put the pilot's window on the wrong side; the principal caught both. One master view per set, with every frame an edit of it, fixed this.
- **Lip-sync** on speaking close-ups stayed weak; a sync-lipsync v3 repair removed a wrong grin but did not raise sync.
- **Operations.** Workers ended runs while their own jobs ran, and three empty runs fail an item; 8 shots then sat failed for 2 h with no alarm. The `crew` skill now makes workers wait and retry permission faults, and a sensor reopens failed items.
- **The zero-fix goal was missed:** 10 director send-backs, mostly vehicles and people that looked pasted on (no scene light, haze or blur).

**Spend.** $151.63 of the $180 cap (`projects/action-01/ledger.jsonl`): images for cast, sets and start frames $74.20, Kling image-to-video $27.66, Veo actor drivers $17.40, critic calls $15.92, Kling motion-control $9.84, voices and audio $6.21, lip-sync and the rest under $0.50.

**Final.** v1: 60 s, 33 shots, −14.2 LUFS, with review notes in `outbox/back-in-twelve-v1-review.md`. A 720p preview (12 MB) and the review went to the principal on WhatsApp. The 288 MB master and the shot plates were kept only in `/tmp/a01`, because a private Drive connect timed out, and they were gone two days later. The preview `outbox/back-in-twelve-v1-preview.mp4` (1280×720) is now the only copy of the cut. The principal: "Let's mark it as testing v1. It's defently not worth publishing there are much to make better." The project is parked; `projects/action-01/PARKED.md` and `crew_sessions.json` list the materials and the crew session ids. Its drop sequence (8A–9B) was rebuilt in Blender with an AI paint pass in [[lab-blender]].

## How the principal works with this
- **Every film and scene passes three gates:** the writers' script goes to him for review; after his yes, a low-quality draft with no music goes to him for review; only after it passes the bar is the full version made. "That should be the basic of any regular generating and scene creating."
- **Blender first for film:** "The next versions will have to run on top of blender scene and only paint the colors. We can't relay on Ai video to make the movement right." See [[tool-selection]].
- **Each project gets its own crew** (skill `crew`), with Muse as director and independent critic models. His goal: "you will not need to fix anything". The measure is the number of director fixes, with a target of zero.
- **"Real product. Everything."** Whatever appears on screen is designed for real first by a specialist in its own session (a house shown as a blueprint gets architects), and the script lists every such item.
- He checks frames for spatial logic: which side of the frame each window and person sits on across reverse shots, and the same set architecture in every frame.
- He owns the workspace and set no tool limits, so a "permission denied" in a crew run is a bad call or a platform fault to retry. A stalled line must be caught and reopened without his "?".
- He brings tools and method ideas himself (Jev and the craft rulebook, [[critic-models]]), and raises a cap when Muse shows a forecast and the options.
