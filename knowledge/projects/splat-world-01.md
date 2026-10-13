---
kind: project
seen: 2026-10-10
tags: [gaussian-splatting, marble, world-labs, gsplat, modal, showcase, one-take]
summary: "ONE DAY: a 46 s one-take flight through five photoreal gaussian-splat worlds of Israel, joined by dust-wave world swaps on the score's downbeats; 16:9 and 9:16 masters for about $14.2 of $60. The principal: 'That are fantastic results.'"
---
# splat-world-01: ONE DAY

**Brief.** This is the showcase film of the splat lab ([[lab-splats]]). The principal asked for gaussian splats, "the real deal like the one used in rendering full worlds with realism presicion... Give me fantastic results." Muse set the brief: one unbroken camera move through 4–5 photoreal splat worlds, splat-native transitions, a music bed, 16:9 and 9:16, reviewed and delivered. Cap $60.

**The piece.** Dawn to night in one breath:
1. a Tel Aviv roof at dawn;
2. a Jerusalem stone alley in the morning;
3. the Ramon crater at noon;
4. Jaffa port at golden hour;
5. a lit kiosk on a night street.

Each world swap is one event on a downbeat of a 135 BPM D-minor score, with cuts at 7.86, 18.54, 29.2 and 36.32 s. At each swap, the old world dissolves far-to-near into glowing dust while the new world stands up behind it. The film opens with the roof condensing out of dawn haze and ends with the kiosk dissolving to black. Method and numbers are in [[splat-field-notes]].

**What worked**
- **Worlds:** Nano Banana Pro stills composed for the move, turned into worlds by World Labs Marble 1.1 Plus. Plus worlds held 6–21 m camera moves.
- **Camera:** code keys per world, joined by `build_chain.py` so the pose is continuous at every cut. No model invents the motion. Five worlds at different scales (1.5–7.2 m per unit) feel like one flight.
- **The world-swap wave** reads as one event and carries the cut on the beat.
- **Rendering cost:** the studio's gsplat lens renderer runs on Modal L40S, with 8 samples per frame for motion blur, depth of field and antialiasing. One 46 s film per aspect costs about $0.08 and 40–85 s of wall time. Three full renders of both aspects cost under $0.50.
- **9:16** is a second lens (`--fov-scale 1.45`), not a crop.
- **Sound:** an ElevenLabs Music v2.5 score, dust-wave SFX and one ambience bed per world, mastered once to −14 LUFS (`audio/mix_v2.sh`).

**What didn't**
- **v1 faults, all fixed by v3:**
  - Frame 0 was half dark: shutter samples before t = 0 saw no world.
  - The hook was black in the lower half for 1.2 s.
  - The SFX were 10 dB too hot, because they were levelled by the wrong meter.
  - A second loudness pass in the finish flattened the swaps.
- **Marble image tells remain:** garbled kiosk signage, soft nets and boat hulls, smeared far buildings. Next time, use signage-free stills for night and street worlds.
- **The Gemini critic was a noisy judge** across three passes ([[critic-models]]). Only notes that a measurement confirmed were acted on.

**Spend.** About $14.2 of the $60 cap (`projects/splat-world-01/ledger.jsonl` $14.07, plus the v3 renders):

| Item | Cost |
|---|---|
| Marble Plus worlds | $11.12 |
| Score | $1.20 |
| Stills | $0.75 |
| Modal renders | about $0.86 |
| SFX and ambience | $0.17 |
| Critic | $0.13 |

**Final.** Review: `projects/splat-world-01/review/review_v3.md`. Both masters are 1380 frames, 46.0 s, −14.1 LUFS.

| File | Delivery |
|---|---|
| `projects/splat-world-01/renders/oneday_v3_1920x1080.mp4` | Over both chat caps: a refused `send_file` in the WhatsApp chat, so the web view links the file to the Files download |
| `projects/splat-world-01/renders/oneday_v3_1080x1920.mp4` | The same route |
| Phone copies `oneday_v3_phone_1280x720.mp4` and `oneday_v3_phone_720x1280.mp4` (15.1 MiB each) | On WhatsApp |

The principal: "That are fantastic results."

## How the principal works with this
- He funds a tool at once when shown the unit cost. Asked whether 7,000 World Labs credits were enough, he bought $20 of credits, twice the $10 Muse asked for.
- **After a result he likes, he asks how to bring the pipeline home.** Here: could a Blender scene plus World Labs Atlas replace Seedance video ("make it all home")? He notes that time to build scenes in Blender is not a constraint, with Opus 5.5 as the builder. Muse's answer and the Atlas facts are in [[splat-field-notes]] (Atlas).
