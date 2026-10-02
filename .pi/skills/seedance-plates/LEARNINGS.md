# LEARNINGS — seedance-plates
One line per lesson, dated, as intent.
- 2026-09-26 Audio lag must be measured on the container timeline (audio start_time vs video); decoding the stream alone hid a 120 ms offset in testing.
- 2026-09-26 Seedance places a word-named event late (pyro, mask reveal, eye flare all 0.5–1 s after the word); name events by second ('exactly at 3.0 s') and keep a time-remap in the conform as the cheap fix before re-drafting.
- 2026-09-26 Onset-envelope lag aliases on the beat period (S1: −450 ms ≈ one 132-BPM beat scored ≈ lag 0); when corr peak < 0.45 or two peaks are within 0.05, trust the mouth sheet, not the number.
- 2026-09-29 Seedance's mouth follows its OWN soundtrack (a copy of @Audio1) and drifts only where that copy diverges; verify with a time-resolved match of clip audio vs our slice (spectral curve + threshold over a null), cut on the last eighth before divergence and cover from that frame, instead of trusting one global lag ([[escape-velocity-case]] §1).
- 2026-09-29 Sung windows start in a word gap and quote the exact words sung ("@Image1 sings @Audio1 … every word in time: \"…\""); no two clips start from the same frame; motion clips get the full mix and "mouth stays closed" (escape-velocity-case §2).
- 2026-09-29 Model-made SFX (pyro, booms) can drown Seedance's copy of @Audio1: when sync reads no_copy the audio cannot vouch for the mouth — decide on the mouth sheet, never on a lag number; brief dips inside held vowels recover and are glitches, not divergences.
