---
kind: video
tags: [case-study, ai-film, trailer, photoreal, voice, performance, editing, sound]
audience: AI film X / YouTube sci-fi
half_life: 120
rights: reference-only
seen: 2026-10-07
summary: "Gossip Goblin × Fable trailer for Gods Don't Give Gifts, measured on the 4K file - edit anatomy, shot and motion stats, the six signature moves, the voice-over timing and mix, what is generated and what is human, and the gap table and actor-driven route to the same bar."
---
# Case: "Gods Don't Give Gifts" trailer (Gossip Goblin × Fable)

The principal sent the X post with "Break this down, I want us to be able to produce this level of moves, voices, and quality." The full visual breakdown is `projects/lab-cinematic/research/breakdown.html` (PDF in `outbox/gods-dont-give-gifts-breakdown.pdf`). The raw study is next to it: `study.json`, `motion.png`, `transcript_vocals.json` and `frames/`.

## Facts
- The trailer runs 1:48 at 3840×1608 (2.39:1 scope), 24 fps and 14.4 Mbps. The post is https://x.com/Gossip_Goblin/status/2107501548989210740.
- The film is an R-rated anthology of four stories. It opens in US and UK theatres on Dec 4 2026, with a Best Animated Feature campaign (Deadline). The producer is Edward Saatchi (Fable).
- **Only the pictures are generated.** The end card credits 7 voice actors (with Claire Boucher), 3 composers, a sound designer (Marian Bălan), an editor and a 5-person animation team. London told THR that the voices are all human actors.
- **Method (secondary sources).** Every piece starts with a script. Stills come from Midjourney (personal profile and sref codes), then Nano Banana edits, then a grade, and then shot-by-shot animation. He reported ~400 prompts / 1,600 images for one cast's faces and ~150 generations for a 90 s scene. 2025 shorts used ElevenLabs voices, with HeyGen and Runway Act-Two for driving performances. The Pomegranate lead was cast before the script was written.

## Measured (framestudy + Demucs + Whisper word timings)
- **Shots.** There are 72 picture shots plus 25 flash frames (< 0.3 s). The median picture shot is 0.90 s (p25 0.57, p75 1.5, max 4.1). 21 s are on black cards (11.6 s of them mid-trailer).
- **Motion.** 46 % of shots are near-still holds, 38 % slow moves and 17 % action. Action comes in bursts of 0.2–0.7 s.
- **Acts.** Cold open 0–24.7 s (median shot 1.58 s, no words). World montage to 47.9 s (0.62 s). Dialogue beat to 65 s (1.81 s, 3× slower). Escalation to 94.2 s (0.67 s). Then one 4.1 s title-shout close-up, the title and credits.
- **Voice.** 8 lines and 53 words between 24.3 and 98.3 s. The lines take 46 s, so the pace inside a line is ~70 wpm (the studio narrator: ~150, [[voice-casting]]). Gaps inside a line reach 3.7 s, and the picture plays in the gaps. 6 of 8 lines are VO. Only 3 shots speak on camera: one CU two-hander, one wide silhouette and one non-human mouth.
- **Mix.** Integrated −19.0 LUFS, LRA 7.4 LU. **The bass stem falls from ~−25 to ~−80 dB under every line and returns in the gap.** The whole mix drops to −40 dB for ~1 s before "Without degradation". A soft female sung vocal plays under the pastoral open.
- Framestudy found 159.75 BPM and 59/103 cuts on beat. Treat both as noise: trailer cuts follow hits, not a grid.

## Signature moves (all reproducible)
1. **Identity-swap burst** (19.1–21.5 s, 12 cuts): the same framing and pose, with the body swapped every 2–3 frames. The theme is said by the edit alone.
2. **In-world glitch transitions:** pixel-slice and datamosh that read as a mind-transfer signal and hide cuts.
3. **Question cards:** a small kicker over a big thin wide sans, with a 2–3 frame glitch-in and a 1.4–2.4 s hold.
4. **Press quotes over hero shots,** with the type layered on the figure.
5. **Pastoral bait-and-switch cold open:** 24 s with no words before the first line.
6. **Silence drop** before the key line.

Camera grammar: slow push-in on faces, ground-level dolly, a locked wide with the figure walking away, POV from inside a monster's mouth, top-down, a handheld charge. Most subjects sit dead centre, which is a weakness to beat.

## Why it reads as cinema
- It uses photographic stills with real skin (pores, wet eyes, catch-lights) and fine grain at 4K.
- **Creatures look practical (silicone, metal, puppetry) and not CG.** This is the strongest anti-slop tell.
- Each world gets one grade, and the scope ratio carries much of the cinematic read.
- The model is only asked for 1–2 s of subtle life per shot. The edit does the rest.

## Gap vs Muse and the route
- **No gap:** edit, cards, glitch, kinetic type (HyperFrames).
- **Small gap:** score and SFX, lip-sync, finish.
- **Medium gap:** photoreal stills (no Midjourney API; test a "film still / practical FX" token set on Nano Banana Pro, GPT Image 2, FLUX 3 and Seedream; select 20–40 per hero face). Faces in motion (Kling v3 Pro; Seedance refused close shots of a real person's face, and generated photoreal faces are untested).
- **Large gap:** acting and voice.
- **Route = actor-driven:**
  - A person acts the shot on a phone. Kling v3 Pro motion-control ($0.168/s) or `minimax/h3-max/recast` transfers the acting to the character.
  - The person performs each line as a voice note. `fal-ai/elevenlabs/voice-changer` ($0.30/min) changes it into the cast voice, and keeps the human timing and breath.
  - Use sync `react-1` ($10/min, emotion) only on the few on-camera lines.
- **Driver sources without the principal on camera** (the principal does not want to act on camera; only the first is tested):
  1. An AI actor: Veo 3.1 or Seedance makes a plain actor in a plain room who performs the line with voice. That clip drives the transfer. This is the same idea as his HeyGen driving performances. Tested: Kling v3 Pro motion-control won, H3 Recast drifted the face toward the driver and Wan Motion failed ([[generation-field-notes]], performance transfer).
  2. Hired self-tapes (Fiverr, Backstage, an estimated $20 to $50 per short scene): real acting and a real voice.
  3. Stock footage (Pexels, Pixabay: free, edits allowed): use it for body action only. The face is replaced.
  4. Mocap libraries (Mixamo, CMU free; Rokoko, ActorCore paid): body only, rendered in Blender.
- **Blender** (the principal will connect it): a Python-posed rig and blended mocap, with an exact lens, camera height and dolly path. Render it as a grey dummy, then use it as a driver (Wan Motion reads the pose; Kling asks for a real-looking human, so a dummy may transfer badly). Faces and lips do not come from hand keys. Use an actor driver or lip-sync models.
- A 30 s teaser on this route cost $17.07, plus $8.43 for the driver test, against an estimate of about $70 ([[lab-cinematic]]). Judge such work against this trailer with the same frame study.

Related: [[escape-velocity-case]] (MJ + Seedance production record), [[voice-casting]], [[generation-field-notes]], [[anti-slop]], [[tool-selection]].
