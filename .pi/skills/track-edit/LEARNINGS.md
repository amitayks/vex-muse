# LEARNINGS — track-edit
- 2026-09-26 The box's static ffmpeg 7.0.2 has rubberband, loudnorm, ebur128 and sidechaincompress: every edit, stretch, duck and master runs locally for $0.
- 2026-09-26 Edits need correct downbeats: a mix-only DP grid picked the wrong bar phase on a four-on-the-floor song (downbeat F 0.0); with the drum stem + chord-change cue it was 0.99. Map with stems before cutting.
- 2026-09-26 ffmpeg sidechaincompress ducking cut the output to the voice's length and dipped ~15 dB for a nominal 8; ducking is now a numpy envelope follower: measured exactly -8.0 dB under the voice, 0.0 dB elsewhere.
- 2026-09-26 Verify a DJ transition by kick phase, not by re-tracking the whole mix (a breakdown after the join fooled the tracker): kicks sat at 0.01 beat before and 0.02 beat after the join.
- 2026-09-26 A fit plan must keep a real ending: the first edit-mode plan kept 0 s of ending on a 30 s target; spans now need >= 4 bars (or a third of the target) on each side.
- 2026-09-26 Measured: 30 s / 90 s fits land exactly (stretch 1.2 % when within 3 %), cut points click-free (spike 0.38-0.89 vs context), masters within 0.1 LU of -14.
