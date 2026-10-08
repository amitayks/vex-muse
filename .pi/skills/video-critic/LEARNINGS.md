# LEARNINGS — video-critic
One line per lesson, dated, as intent.

- 2026-10-07 First use on WHAT THE TIDE OWES v1: Gemini 3.1 Pro independently named the same two faults as the principal (lines read as theatre to camera; medium-speed drifts) plus lip-sync and dry dialogue. Use it before showing a cut.
- 2026-10-07 fal openrouter/router/video returns 400 "Reasoning is mandatory" for gemini-3.1-pro-preview unless reasoning=true.
- 2026-10-08 action-01 8F: on a 1.2 s clip the critic saw only 1-2 frames and denied a fast swing that the frames prove. For clips under about 2 s, send a 4x slow-motion copy (setpts=4*PTS) and say so in the context; keep pace judgements on measurements.
