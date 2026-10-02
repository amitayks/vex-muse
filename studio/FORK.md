# studio/ — Muse's fork of ClaudeAnimationBase

Base: ClaudeAnimationBase @ 0ac8bf2 (see ../vendor/PINS.md). Read
`ANIMATION_GUIDE.md` (upstream, still authoritative for the engine API) and
the `p5-paper-engine` skill (my additions and project layout).

## Changes
- 2026-09-26 Fonts are local and inlined (`assets/fonts/fonts.css`, data URIs): no Google Fonts request, works offline; `render.mjs` waits for `load` + `document.fonts.ready` instead of `networkidle0` (which hung).
- 2026-09-26 `render.mjs --page=<file.html>` renders any studio page (one page per project: `projects/<slug>.html`).
- 2026-09-26 `--soft-gl` no longer forces `--enable-gpu-rasterization` (slowed SwiftShader setup to minutes); ready timeout 300 s, `--ready-timeout=` to override.
- 2026-09-26 Removed docs/emotions.webp (6.6 MB animated sheet; the jpg sheet stays).
- 2026-09-26 Added assets/fonts/Anton.ttf (OFL) for condensed display lyrics; project pages may be plain Canvas2D compositors (no p5) as long as they expose window.ready/renderAt/renderSheet/DUR/PROJECT.
