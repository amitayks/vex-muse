---
kind: project
seen: 2026-10-07
tags: [lab, ai-film, performance-transfer, kling, voice-changer]
summary: "lab-cinematic: closing the gap to the Gossip Goblin trailer (acting and voice) with AI-actor drivers, Kling v3 Pro motion-control and the ElevenLabs voice changer, proven on What the Tide Owes, a 30 s folk-horror teaser that cost $25.50 including the driver test."
---
# lab-cinematic: AI-actor performance and What the Tide Owes

**Brief.** the principal sent the Gossip Goblin × Fable "Gods Don't Give Gifts" trailer: "Break this down, I want us to be able to produce this level of moves, voices, and quality." The measured breakdown ([[gossip-goblin-trailer-case]]) showed that only the pictures are AI, and that the studio's gaps were acting and voice. He then asked: "Can we find a source of acters to get and use instead of actually filming myself?" After Muse listed four driver sources he said "test with our best option for now", and after the test reel, "lets go". Cap $150, target about $70.

**The piece.** *What the Tide Owes*, 30 s at 2.39:1. On a North Atlantic fishing island the sea gives back what it takes, but as porcelain. A widow, Maeve, asks for her drowned husband. The ferryman, who asked for his wife and got a porcelain cheek, warns her. They row out anyway. The lanterns die, a porcelain hand takes her wrist, and the husband walks out of the shallows and says her name.

**What worked**
- **The actor route** ([[generation-field-notes]], performance transfer). A Veo 3.1 Fast AI actor performs each line with voice in a plain version of the set. Kling v3 Pro motion-control moves the acting onto a Nano Banana Pro still, and the ElevenLabs voice changer re-voices the line (Irish library voices Declan, Labhaoise and Cillian). Both dialogue shots held identity and the porcelain prosthetic on the first take.
- **The driver test** (one 8 s line in five versions) picked the route before any teaser spend: Kling won, H3 Recast drifted the face toward the driver, and Wan Motion failed.
- **Stills by job.** Nano Banana Pro won the faces and the cast. GPT Image 2 won the bell and the calm title water.
- **The mix.** Every line was levelled to the same active loudness. The score was split at 180 Hz: the low band ducked at ratio 20 and the mids at ratio 3, keyed by the voices. A gate gave true silence (−80 dB) before the two key lines, the reference's silence-drop move.
- **Against the reference, on the same frame study:** median picture shot 1.52 s (the reference's dialogue act is 1.81 s), a burst of four shots under 1 s, and a 4.1 s held close-up before the title, as in the reference. Review scores were 4–5 on every rubric line.

**What didn't**
- **"Anamorphic lens" in a Nano Banana Pro prompt adds black letterbox bars** inside a 16:9 image. "Spherical 35mm lens, the image fills the frame edge to edge" fixed it; trim any bars before an image becomes a start frame.
- **A one-word name defeats Whisper and the audio-model ear** ("Maeve" heard as "My way"). A targeted 0–10 ear question scored the actor's own take 8/10 and the Cillian voice 5/10, so both were layered.
- **The first grain finish went past 90 MB for 30 s** (grain `c0s=7`, CRF 16). Grain `c0s=4`, CRF 18 and `-tune grain` gave 34.5 MB.
- **The principal's two notes on v1:** the scene moved at one medium speed, and the dialogue played as theatre, one person reciting at a time. A blind Gemini 3.1 Pro watch named both, plus weak lip-sync and dry voices that do not sit in the scene ([[critic-models]]).
- **Weak spots left in v1:** S14 is a 720p source and slightly soft; the oar mechanics in S09 and the floating hair in S11 read as generated; S11 is greener than the grade; lip-sync is lag-compensated but not checked frame by frame (sync scored 4, not 5). The v2 fix list is in `review/v1.md`.

**Spend.** $25.50 of the $150 cap. The driver test was $8.43: the Recast price was misread, so it ran over the $5 quoted. The teaser was $17.07: stills $3.45, drivers and voices $4.50, plates $7.92, score $1.20. SFX ran on the direct ElevenLabs key ($0 cash). Ledger: `projects/lab-cinematic/ledger.jsonl`.

**Final.** `projects/lab-cinematic/renders/v1.mp4` (30.0 s, 1080p24 with a 2.39:1 matte, −14 LUFS, 34.5 MB) and `review/v1.md`. A chat-size preview went on WhatsApp. WhatsApp refused the master at its 16 MB cap, so the principal downloads it from the Vex web view ([[generation-field-notes]], messaging caps). The trailer breakdown PDF and the driver-test reel (`test-driver/out/compare_v1.mp4`) went to him too. His verdict: "Really good results… That is fantastic progress for first Gen."

## How the principal works with this
- He does not want to act on camera himself. Performance comes from AI actors, hired actors or capture, and he plans to connect Blender for body and camera blocking.
- "Break this down" on a reference means a measured study plus a route to reach the same bar, not a description.
- He lets Muse pick the method ("our best option") and approves the whole production from one comparison reel.
- **Pace rule:** "fast action or slow events", never medium-speed movement in between.
- **Dialogue rule:** scenes with two or more people are a natural discussion between them, never "Theater play".
- The crew, "real product" and Blender-first rules that came after this lab are in [[action-01]].
- He pushes for the best available tools (for example Gemini 3.1 to watch videos) and sets the bar with a reference: the next action bar is [[masters-of-the-air-case]].
