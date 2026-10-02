---
kind: project
seen: 2026-09-26
---
# lab-music — full music capability: source, understand, edit, generate (Sep 2026)
**Brief.** the principal asked for full capability on music. Songs are first-class
material (personal, non-commercial). He wanted three things: get any song,
beat or soundtrack; understand and edit tracks; and generate our own music,
testing what exists now. Cap $25; the report had to be in plain words.

**What worked.**
- **Sourcing.** YouTube is bot-walled from the box, but a yt-dlp fetch
  inside a Modal container reached 4/4 songs.
- **Analysis.**
  - Stems: htdemucs_ft on a Modal L4 took 37 s per 4-min song (≈$0.013).
  - Beats: beat_this was the only tracker to get 171 BPM (3 s GPU).
  - Two bugs in the local tracker were fixed: a 46 ms frame-stamp bias
    and frame-quantised tempo.
  - Key: Essentia EDMA.
  - Lyrics: whisper runs in chunks, anchored on LRCLIB with automatic
    detection of the LRC's edit offset. Line starts land within 1 s of
    LRCLIB for 95–100 % of heard lines.
- **Editing.** Every edit is local and free: bar-grid fits, loops,
  rubberband tempo and pitch, stem remixes, a beat-matched DJ transition
  (kick phase continuous), a key- and tempo-matched mashup, ducking and
  mastering.
- **Generation.** Eleven generators ran on four briefs (YuE2 on the song only); results in
  [[music-tools]]. Defaults per job:
  - ElevenLabs v2.5 composition plans for exact beats and songs.
  - Lyria 3.5 for cheap full songs.
  - Stable Audio 3 for exact-length instrumentals.
  - ACE-Step 1.5 on Modal as the open model we own.
  - The winning combination for picture cues: an exact-length bed at a
    BPM that puts the hits on bar lines, plus impacts written in code.
    Hits landed within 1–2 ms in the lab render, but −33 / +9 / +10 ms
    in the delivered MP3. That is within a frame, not within 2 ms (see
    [[music-tools]]).

**What didn't.**
- No model hit an absolute timestamp on its own.
- Lyria 3.5 ignores length; MiniMax 3 stops early and misses tempo;
  ACE-Step 1.5 sometimes ends early.
- ElevenLabs refuses a commercial song as audio reference.
- Whisper on full mixes drops verses.
- The auto-sync committed 263 MB of lab audio to git before audio was
  ignored, including stems of commercial songs (Get Lucky, Blinding
  Lights, Levels). The files are untracked now, but the history still
  carries them. The workspace auto-syncs to `your workspace's git remote`,
  which is **private** (unauthenticated API and web both return 404), so
  nothing was published. The principal chose to keep that history and only stop
  future audio from syncing (below).

**Decisions after delivery (the principal, 2026-09-26).**
- **Default singer:** he listened to samples 1 and 2. ACE-Step 1.5 (open,
  ~$0.02) sounds better than ElevenLabs: cleaner, more human in high and
  low notes. It is now the default singer (see [[music-tools]]), even
  though the measurements had scored both about the same.
- **Git history:** no cleanup; the old history stays as it is. From now
  on no audio syncs. Every audio extension is git-ignored workspace-wide.
  The 77 audio files already tracked were untracked, not deleted, and
  remain on disk.
- **Suno and Udio:** out, since neither has an official API.

**Spend.** $5.45.

**Evidence.**
- Measurements: `projects/lab-music/review/results.md`.
- Listening samples: `outbox/music-lab/` (6 MP3s).
- Report: `outbox/music-capabilities-study.md`.

**Skills.**
- New: `music-source` 1.0.0, `music-gen` 1.0.0, `track-edit` 1.0.0.
- Upgraded: `song-map` 1.1.0, `fal-media` 1.1.0, `sound-design` 1.1.0,
  `js-scoring` 1.1.0, `mv-director` 1.3.0.
