---
kind: project
seen: 2026-10-04
tags: [lab, video-matting, alpha, ltx, bria]
---
# lab-alphagen: LTX-2.5 Alpha-Gen video matting vs Bria v3

**Brief.** the principal sent @onihachi's X post testing LTX "AlphaGen" on fur, fire and translucent objects
(x.com/onihachi/status/2106529152119795965). He asked whether we can use it and whether it is a useful skill
for us. He then sent Lightricks' own launch post (x.com/ltx_io/status/2106015208221393339, "Alpha Gen (Beta)",
1.5M views) and asked whether it is worth having and paying for. Both posts are the same model: an IC-LoRA on
LTX-2.5-22B that turns an RGB clip into a frame-aligned grayscale alpha matte, with no green screen, mask or
prompt. Behaviour against Bria is in [[generation-field-notes]] (video matting).

**What worked**
- The free public ZeroGPU Space `hugging-apps/ltx-2-5-alpha-matte` runs through Gradio's HTTP API with a
  stdlib script (`projects/lab-alphagen/space_call.py`). It returned a 97-frame matte at 1280×704 in 55 s for $0.
- Both models were scored on the same plate by IoU, share of soft-edge pixels, frame-to-frame alpha change
  and a green-composite zoom. On the cel idol they agree (IoU 0.84); Bria's alpha changed 8e-3 per frame
  against Alpha-Gen's 15e-3.
- A cheap soft-edge test clip came from `fal-ai/ltx-2.3-22b/distilled/text-to-video` (1024×576 by default,
  97 frames, about $0.07, 110 s). Bria v3 kept its flyaway hair cleanly, dropped the haze and made a sheer
  sleeve opaque.

**What didn't**
- Alpha-Gen was never run on the soft-edge clip, the case it is built for. The Space's anonymous ZeroGPU quota
  covers about one run a day (the second request needed 80 s with 31 s left).
- No full-HD run, and the Modal cost per shot is an unmeasured estimate. Chunk seams on shots longer than
  145 frames are untested.

**Access and limits**
- Not on fal, and not on LTX's paid API; the hosted route is only the LTX Explore app.
- Weights are gated on Hugging Face (`Lightricks/LTX-2.5-22b-IC-LoRA-Alpha-Gen`). Accept the terms on that
  repo and on `Lightricks/LTX-2.5` before making the read token (`HF_TOKEN`); the same token lifts the Space
  quota. Self-hosting means ComfyUI or `python -m ltx_pipelines.ic_lora --skip-stage-2`.
- One pass takes at most 145 frames and 1920×1088, and full HD needs an H100-class GPU.
- The released version is the distilled one. A "full" version for complex scenes (shorter clips) is announced,
  with its workflow still to come.
- Licence: the LTX-2 community licence, free for entities under $10M annual revenue.

**Verdict.** Not worth paying for as a service. Bria v3 (or SAM 3) stays the default for cutting out a singer
or character. Alpha-Gen is a free extra for shots where a performer and smoke, haze, fire or glass must be kept
together. The gap is smaller than the launch suggests, since fire, sparks and glows can be generated on black and
blended in without a matte, and many effects can be drawn in code. Set it up (HF token, then Modal) the first
time a video calls for that kind of shot, and test it on that real shot.

**Spend.** About $0.31 of no set cap (two Bria v3 runs at $0.12 each, one LTX-2.3 test clip at about $0.07;
the Space was free). Ledger: `projects/lab-alphagen/ledger.jsonl` (the LTX-2.3 line was corrected by hand,
since `fal.py` has no rate for that endpoint).

**Final.** No deliverable. The comparison sheets are in `projects/lab-alphagen/cmp/`, and `README.md` there
holds the method.

## How the principal works with this
- He sends a bare X post and asks "can we use it / worth having and paying for?". He wants a verdict first,
  then what it would let us do, the cost per use, and a cheap test on our own footage rather than the launch demo.
