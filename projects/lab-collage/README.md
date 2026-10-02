# lab-collage — code-first paper-collage explainer (proof for skill `collage-motion`)

Reference: @omarsar0's Pexo "Rise of Microsoft" video, studied in
`research/x/omarsar0-2103575986772070862/` → [[paper-collage-explainer]].
Replica for study, not a Muse style sample: archetype topic "THE HOME STUDIO" (1979–83), no real
people, no brands.

| Path | What |
|---|---|
| `gen/raw/` | Nano Banana Pro assets (bedroom photo, cassette, hand, boombox) — `ledger.jsonl` |
| `gen/sam/` | SAM 3 `person` mask of the bedroom photo (reuse with `cutout.py --mask`) |
| `motion/collage-src/index.src.html` | the composition source (edit this) |
| `motion/collage/` | built HyperFrames project (`hf_build.py` output + assets) |
| `renders/collage_v4.mp4` | accepted draft (v1–v3 = review history) |
| `review/` | snapshots, `v1/`–`v4/` frame studies, `notes.md` |

Rebuild + render:
```bash
cd /data/workspaces/<workspace> && source tools/env.sh
python3 .pi/skills/code-motion/scripts/hf_build.py projects/lab-collage/motion/collage-src/index.src.html projects/lab-collage/motion/collage
cd projects/lab-collage && export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_BROWSER_PATH=$CHROME_PATH
npx hyperframes render motion/collage --quality draft --fps 30 --workers 2 -o renders/collage_vN.mp4
```
`motion/collage/assets/js/collage.js` is a copy of the skill's master
(`.pi/skills/collage-motion/assets/collage-template/assets/js/collage.js`) — edit the master, copy here.
Spend: $0.623.
