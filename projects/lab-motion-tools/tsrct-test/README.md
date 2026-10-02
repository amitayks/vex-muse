# Tesseract (Mirage) engine test — 2026-09-26, $0
Same piece as `renders/tesseract_turn_v2.mp4` (HyperFrames), rebuilt in Tesseract CLI 0.2.0.
- `build_turn.py` → 156 actions (50 layers, every property scripted per frame); `check.py` → drawn/motion/diff vs reference.
- `turn.tsrct` — the editable Tesseract project (fonts + audio packed inside).
- Engine + software Vulkan driver installed off the shared disk in `/tmp/tsrct-lab` (env: `/tmp/tsrct-lab/env.sh`), telemetry disabled.
- Renders: `renders/tesseract_turn_tsrct_v3.mp4`, side by side `renders/engine_compare_hf_vs_tsrct.mp4`.
- Report: `outbox/tesseract-engine-test.md`. Not adopted; skills unchanged.
