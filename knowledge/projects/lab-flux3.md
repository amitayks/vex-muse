---
kind: project
seen: 2026-10-04
---
# lab-flux3 — FLUX 3 Image vs our image models on 4 real jobs (Oct 2026)
Brief: The principal sent BFL's FLUX 3 Image launch post (bounding-box layout, edits that keep every other pixel, 10 refs,
4K) and asked whether it would be better or cheaper for us. I ran it head to head against Nano Banana Pro
(and GPT Image 2 for the medieval look) on four jobs from past projects, at 2K, with the original prompts.
Files: `projects/lab-flux3/` (inputs in `in/`, sheets and scripts in `review/` and `tools/`, raw outputs were in /tmp).
Summary sheet: `projects/lab-flux3/review/flux3_vs_nano.jpg`.

**Results**
| Job (source project) | Winner | Evidence |
|---|---|---|
| Exact edit: raise the cleaver, keep the rest (a client brand film) | **Nano** | Outside the edit boxes, 90 % of Nano's pixels stayed within 4 levels of the source; FLUX 3 kept **~1 %** (both prompt styles). FLUX re-tinted the whole frame (backdrop +10 R / +11 G, aqua → mint) and returned another size (2736×1536 from a 2608×1456 input; 1360×768 from 1376×768). After removing a fitted global gain it was 89 % vs Nano's 93 %, so the damage is mostly a regrade. Its box prompt placed the cleaver exactly (vertical, at the top edge); its plain instruction tilted it |
| Same character in new shots (`pdoom-test` sheet + stage) | tie | both on-model (star clip, headset, jacket, skirt, boots) in close-up and wide. FLUX honoured "one third of the frame height"; Nano drew her at ~¾ |
| Lyric zone: left half calm, singer right third, knees up | **FLUX 3** | FLUX put her inside her box at the asked crop. Nano drifted centre-right, drew her full-body and added a hand mic. Both left zones were calm (gradient 2.1 / 1.8 against 2.07 on the source plate, 0 % ink); Nano made no blank panel with the "backdrop continues" phrasing |
| House styles, text only ([[lab-collage]] halftone prop, `antioch-1098` pen drawing) | **Nano / GPT Image 2** | FLUX ignored the halftone and pure-white tokens: it made a modern product shot on grey with a cast shadow, and a tame procession on parchment. Both break the white-key / multiply pipeline |

**Other facts**
- Content filter: FLUX 3 refused all 3 prompts that named "Sailor Moon 1992 and Satoshi Kon Perfect Blue" (422
  content_policy_violation). The same prompts passed once the names were removed, and Nano had accepted them.
- Speed: FLUX took 50–90 s per 2K image, Nano 34–50 s.
- Price: $0.024 per output MP. That is about $0.10–0.12 at 2K (≈4.2 MP; the ledger rounds up to 5 MP) and about $0.05 at 1K,
  against Nano's flat $0.15. Images are a small slice of a project, so the saving is a few dollars at most.
- Spend: $1.34 estimated (6 FLUX calls at 2K, 1 at 1K, 3 Nano). The 3 refused calls are not in the ledger. The fal
  usage API returned 403 for this key, so billed amounts were not confirmed.

**Decision**: not a replacement. FLUX 3 is the **layout specialist**: use it for plates where placement and scale
must be exact (lyric zones, a character at a set size or crop), with a box table in the prompt. Keep Nano for
identity edits, start/end frame pairs and halftone. Keep GPT Image 2 for period line art. Never pair a FLUX edit
with its source as a Seedance start/end frame without colour-matching it first.
