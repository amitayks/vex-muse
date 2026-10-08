#!/usr/bin/env python3
"""critic_step.py (skill crew) — the bash station a line runs after a maker step.
Reads $VEX_ITEM_DATA (needs: dir; optional: rubric, critic_model) and $VEX_STEP_OUTPUTS (the maker's last
output must carry "files": [abs paths] and "kind": text|image|video). Runs critic.py once per file for video
(takes are judged one by one, then ranked) or once for all files otherwise. Prints one JSON line (the step output):
{"pass": bool, "best": path|null, "verdicts": [{file, pass, score, out}], "rubric": ...}. Exit 0 when judged."""
import json, os, subprocess, sys, pathlib

S = pathlib.Path(__file__).resolve().parent
data = json.loads(os.environ.get("VEX_ITEM_DATA") or "{}")
outs = json.loads(os.environ.get("VEX_STEP_OUTPUTS") or "{}")
if isinstance(outs, list): outs = {str(i): o for i, o in enumerate(outs)}
maker = None
for name, o in reversed(list(outs.items())):
    o = o.get("output", o) if isinstance(o, dict) else o
    if isinstance(o, dict) and o.get("files"): maker = o; break
if not maker: print(json.dumps({"pass": False, "error": "no maker output with files"})); sys.exit(0)
d = pathlib.Path(data["dir"]); kind = maker.get("kind", "text")
rubric = (data.get("rubrics") or {}).get(kind) or data.get("rubric") or str(S.parent / "references/rubrics" / (
    "voice.md" if data.get("kind") == "voice" else {"text": "script.md", "image": "cast.md", "video": "take.md"}[kind]))
ledger = d / "ledger.jsonl"
cdir = d / "critic"; cdir.mkdir(exist_ok=True)
ctx = d / "bible/bible.md"
unit0 = str(data.get("id") or data.get("angle") or data.get("character") or "item")
extra = {k: v for k, v in data.items() if k not in ("dir", "rubric", "rubrics", "project")}
if extra:                                   # the unit's own brief (shot, character) goes to the critic as context
    c2 = cdir / f"{unit0}-ctx.md"
    scr = d / "scripts" / str(data.get("script", "")) if data.get("script") else None
    dec = d / "assets.json"
    c2.write_text("THIS UNIT:\n" + json.dumps(extra, indent=1) + "\n\n" + (ctx.read_text() if ctx.exists() else "")
                  + ("\n\nCURRENT SCRIPT (the director's latest version; its edits are decisions, not defects):\n" + scr.read_text()[:30000] if scr and scr.exists() else "")
                  + ("\n\nDIRECTOR'S RECORD (assets.json):\n" + dec.read_text()[:6000] if dec.exists() else ""))
    ctx = c2
unit = str(data.get("id") or data.get("angle") or data.get("character") or os.environ.get("VEX_ITEM_ID", "item"))
# audio in a text record becomes a listening reel (critic.py)
EXT = {"text": (".md", ".txt", ".json", ".mp3", ".wav", ".m4a"), "image": (".jpg", ".jpeg", ".png", ".webp"), "video": (".mp4", ".mov", ".webm")}
files = [f for f in maker["files"] if str(f).lower().endswith(EXT[kind]) and pathlib.Path(f).exists()]
if not files: print(json.dumps({"pass": False, "error": f"no {kind} files to judge in the maker output"})); sys.exit(0)
groups = [[f] for f in files] if kind == "video" else [files]
verdicts = []
for i, g in enumerate(groups):
    out = cdir / f"{unit}-{kind}-{i + 1}.json"
    cmd = ["python3", str(S / "critic.py"), kind, rubric, str(out), *g, "--ledger", str(ledger)]
    if ctx.exists(): cmd += ["--context", str(ctx)]
    if data.get("critic_model"): cmd += ["--model", data["critic_model"]]
    refs = data.get("refs") or []
    if not refs and (d / "assets.json").exists():           # the director's per-shot canon list
        refs = (json.loads((d / "assets.json").read_text()).get("shot_refs") or {}).get(str(data.get("id")), [])
    refs = [r for r in refs if pathlib.Path(r).exists()][:4]
    if kind == "image" and refs: cmd += ["--refs", ",".join(refs)]   # approved set/cast images
    r = subprocess.run(cmd, capture_output=True, text=True)
    v = json.loads(out.read_text()) if out.exists() else {"pass": False, "score": 0, "error": r.stderr[-400:]}
    verdicts.append({"file": g[0] if len(g) == 1 else g, "pass": v.get("pass"), "score": v.get("score"), "out": str(out),
                     "defects": v.get("defects", [])[:6]})
if os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY"):      # calibrated second opinion on each verdict
    for v in verdicts:
        jo = pathlib.Path(v["out"]).with_suffix(".jev.json")
        cmd = ["python3", str(S / "jev_gate.py"), v["out"], rubric, str(jo)]
        if kind == "text" and isinstance(v["file"], list) and len(v["file"]) == 1: cmd += ["--artifact", v["file"][0]]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if jo.exists():
            j = json.loads(jo.read_text()); v["jev"] = {k: j.get(k) for k in ("p_pass", "decision", "min_confidence")}
best = max(verdicts, key=lambda v: (bool(v["pass"]), v["score"] or 0))
print(json.dumps({"pass": bool(best["pass"]), "best": best["file"], "best_score": best["score"], "rubric": rubric,
                  "verdicts": verdicts})[:15000])
