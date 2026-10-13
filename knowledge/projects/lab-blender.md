---
kind: project
seen: 2026-10-10
tags: [lab, blender, local-muse, paint-pass]
summary: "lab-blender: the first videos built on real Blender scenes, made overnight by Local Muse on the principal's Mac. S1 LIGHTS ON is Blender only; S2 THE DROP rebuilds the action-01 water drop with real gravity and an AI paint pass. Spend $4.07 of $40."
---
# lab-blender: first videos on real Blender scenes

**Brief.** After action-01 the principal set the rule that Blender makes the movement and AI only paints the look ([[tool-selection]], Blender row). He then wrote: "talk to local-muse and let's create a videos based on actual blender objects and world. Create couple smaplces and work on it all night. Bring me results in the morning." He pointed to a Blender project on his Mac, built by Opus 5.5 (Alpenglow, [[local-muse-mac-helper]]), as a reference. Muse directed from the server workspace, and Local Muse built and rendered on the Mac. There were two samples:
- **S1 LIGHTS ON:** 18 s, Blender only, on the Alpenglow world. The mountain gives its last light to the house: each cabin light strikes on a music note.
- **S2 THE DROP:** [[action-01]] shots 8A–9B (film time 38–46 s) rebuilt in Blender from the canyon and tanker specs, with an AI paint pass on top. A 3-up compare puts it beside the v1 AI video.

Lab cap: $40.

**What worked**
- Local Muse built every scene from one Python script, rendered unattended, and returned measured proof. The technical record is in [[blender-field-notes]].
- **S1 timing:**
  - Every light strikes on its exact frame (f19, f109, f127, f145, f163), checked by luminance at each lamp.
  - The cuts land on the bar (80 BPM, cuts at f73, f217, f361).
  - The music is an ElevenLabs bed plus js-scoring chimes on the same frames; each chime sits 9.6–61 dB above the bed in 0.8–6 kHz.
  - The end rhymes with the opening on the jetty lantern.
- **S2 physics, which AI video could not give:**
  - The canyon is at true scale, and the 29.4 m tanker flies at 68 m/s.
  - 12,000 water particles fall under gravity: 3.1–3.8 s from release to ground.
  - The contact gate on all 20 crew bodies passed: 0 float, 0 sink, 0 intersect.
- **The paint pass** made 8A, 8B and 8E photoreal and kept the Blender motion. Muse's review rates 8E (the slab pouring from the open door) as the best water the studio has made. The route and its rules are in [[render-repaint]].

**What didn't**
- **S2, 9A:** the paint model invented a second aircraft in the empty sky, so 9A was cut to 0.83 s. Shot 9B then starts 5 frames early against the v1 sound.
- **S2, 9B:** the distant water curtain reads as smoke and steam, not a wall of water. The foreground bank shows flat streaks.
- **S1 summit:** it dims evenly; no earth shadow climbs it.
- **S1 opening:** shot A is calm, with no hook in the first 0.75 s.
- **S1 continuity:** the boat in shot A is a cheated duplicate, and the exposure steps on the cut into D.
- **Lost overnight turns:** both finished renders landed by 06:55, but no turn acted on the two DONE reports, and the hourly watch fired only once. The paint pass therefore ran after 09:00 ([[local-muse-mac-helper]], Health).
- **v1 at 720p:** the v1 master was lost from `/tmp`, so the v1 side of the compare comes from the 720p preview.

**Spend.** $4.07 of the $40 cap, in 33 calls (`projects/lab-blender/ledger.jsonl`):
- music: $0.68;
- paint-pass tests: $1.03;
- paint takes for six shots: about $2.36.

The Mac renders cost $0. The S1 final took 61 min of Cycles on the M5 Pro.

**Final.** Review: `projects/lab-blender/review/v1.md` (S1 7/10, S2 6/10).

| File | Format | Delivery |
|---|---|---|
| `projects/lab-blender/renders/s1_lights_on_v1.mp4` | 1920×1080, 24 fps, 18 s, −13.9 LUFS, 26.2 MB | Over the WhatsApp cap: a 13.7 MB phone copy went on WhatsApp. The master was handed to his web-chat session to send; arrival is not confirmed. |
| `projects/lab-blender/renders/s2_the_drop_painted_v1.mp4` | 1280×720 in 2.39 scope, 8 s, v1 sound, 4.6 MB | Full quality on WhatsApp |
| `projects/lab-blender/renders/s2_the_drop_compare_v1.mp4` | Blender, painted and v1 stacked, 11.1 MB | Full quality on WhatsApp |

The principal gave no direct verdict. His next ask built on S1: turn the Alpenglow cabin into a bar with people talking, a 1-minute film made by the studio crew.

## How the principal works with this
- He gives overnight briefs ("work on it all night. Bring me results in the morning"), so the work must run unattended. Each stage needs a watch that is proven to keep firing.
- He points to an existing asset (here the Opus-built Alpenglow scene) as a reference, not as a style to copy.
- The Blender-first rule holds: Blender owns movement, geometry and cameras; AI paints only the look.
