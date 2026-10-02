# LEARNINGS — p5-paper-engine
One line per lesson, dated, as intent.
- 2026-09-26 Measured on this box (2 CPU, SwiftShader): the kit demo costs ~75 s per 1080p frame with watercolor fills; page setup ~3 min. Local = sheets/strips only; full renders go to the farm.
- 2026-09-26 Upstream render.mjs waited for `networkidle0` on Google Fonts and hung offline; fork inlines fonts. Never make a render depend on the network.
- 2026-09-26 In this sandbox Chrome's URL font loader (data: URIs included) failed intermittently in lab probes while FontFace(ArrayBuffer) always worked: verify fonts render in every sheet with text; if blank, register the studio fonts from bytes.
