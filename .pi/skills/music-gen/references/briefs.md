# Music brief format (musicgen.py / musiceval.py)

One JSON per cue, saved in `projects/<slug>/audio/briefs/<id>.json`. The same
brief drives every provider (`musicgen.py input <provider> brief.json` shows
the translation) and the scoring (`musiceval.py measure`).

```json
{
  "id": "hook-beat",                       // file/ledger tag
  "prompt": "style words: genre, instruments, mood, production",
  "instrumental": true,
  "duration": 30,                          // seconds; 16 bars at 128 BPM = 30.0 s exactly
  "bpm": 128, "key": "A minor",
  "sections": [                            // optional timeline = cue points
    {"t0": 0,   "t1": 7.5,  "name": "Intro", "desc": "what happens"},
    {"t0": 7.5, "t1": 22.5, "name": "Main",  "desc": "...", "lyrics": "line\nline"}
  ],
  "lyrics": "[Verse]\n...\n[Chorus]\n...", // full tagged lyrics (vocal briefs)
  "hits": [8.0, 16.0, 24.0],               // picture hits to measure (and to add with js-scoring / SFX)
  "reference": "projects/<slug>/audio/ref-30s.mp3",   // style audio (own or open-licence material)
  "source": "path.wav",                    // for extend / audio-to-audio
  "overrides": {"lyria35": {"prompt": "..."}},        // provider-specific input fields win
  "measure": {"ref_song": "projects/<slug>/audio/ref.song.json"}  // style distance target
}
```

How each provider receives it:
- **eleven** (`elevenlabs/music/v2.5`): sections → `composition_plan.chunks`
  (duration_ms per section, `[Name]` + lyric lines + `{desc}`, positive styles
  = prompt words + section desc; negative "vocals" when instrumental);
  `reference` → `audio_reference` on chunk 1. No sections → prompt +
  `music_length_ms` + `force_instrumental`.
- **lyria35 / lyria3 / lyria3pro**: one prompt: style + BPM + key +
  "exactly N seconds" + `[m:ss - m:ss] Name: desc` lines + lyrics.
- **minimax3**: Structured Caption ("Genre and style: … BPM: … Key: …
  Arrangement: Name (m:ss-m:ss): …") + tagged lyrics (required; one tag per
  line; instrumental = `[intro]/[instrumental]/[outro]` tags).
- **sa3 / sa25 / sonilo**: prompt + structure sentence + exact duration
  (instrumental only).
- **sa3-a2a / sa3-extend**: `source` or `reference` as `audio_url`
  (`init_noise_level` 0.75 default; `extend_seconds_after` = duration).
- **acestep15** (Modal): caption, lyrics or `[Instrumental]`, bpm, keyscale,
  timesignature 4, duration, `reference_audio`.
