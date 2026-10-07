#!/usr/bin/env python3
"""jev_gate.py (skill crew) — the calibrated gate call. Gemini (critic.py) describes; Jev decides.
Reads a critic verdict JSON (+ optionally the artifact text) and asks Jev (TypeSafe System One, text in,
typed calibrated answers out) one Score question per rubric item, plus Noul questions per major defect
("this defect would be visible to a first-time viewer at phone size"). Combines them in code:
p_pass = product over items of P(score >= pass level). Prints and writes JSON:
{"p_pass": 0-1, "items": {item: {"score", "p_ok", "confidence"}}, "blocking": [...], "decision": "pass|redo|ask"}.

usage: jev_gate.py VERDICT.json RUBRIC.md OUT.json [--artifact FILE] [--threshold 0.7]
Key: JEV_API_KEY (or TYPESAFE_API_KEY). Exit 0 when Jev answered; 2 on transport/billing errors
(the caller then falls back to the critic's own pass)."""
import json, os, re, sys, pathlib, urllib.request, urllib.error

a = sys.argv[1:]
def opt(k, d=None):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
art = opt("--artifact"); thr = float(opt("--threshold", "0.7"))
if len(a) < 3: print(__doc__); sys.exit(1)
verdict = json.loads(pathlib.Path(a[0]).read_text()); rubric = pathlib.Path(a[1]).read_text(); out = pathlib.Path(a[2])
key = os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
if not key: print(json.dumps({"error": "no JEV_API_KEY"})); sys.exit(2)

items = re.findall(r"^\s*\d+\.\s*([^:]+):\s*(.+)$", rubric, re.M)          # "1. name: description"
state = "CRITIC FINDINGS (independent reviewer):\n" + json.dumps(
    {k: verdict.get(k) for k in ("scores", "defects", "verdict")}, indent=1)
if art and pathlib.Path(art).suffix in (".md", ".txt", ".json"):
    state += "\n\nARTIFACT:\n" + pathlib.Path(art).read_text()[:40000]
levels = ["Fails: a clear, visible fault", "Weak: below a professional bar", "Passable: meets the bar with flaws",
          "Strong: professional", "Outstanding: nothing a top professional would change"]
qs = {f"item_{i}": {"type": "score", "instructions": f"{name.strip()}: {desc.strip()} How well does the work meet this?",
                    "criteria": levels} for i, (name, desc) in enumerate(items)}
majors = [d for d in verdict.get("defects", []) if (d.get("severity") or "major") == "major"][:12]
for j, d in enumerate(majors):
    qs[f"defect_{j}"] = {"type": "noul", "instructions": f"This defect is real and would be noticed by a first-time viewer at phone size: "
                                                          f"[{d.get('where')}] {d.get('what')}"}
body = {"model": "jev-latest", "state": state, "questions": qs}
req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=json.dumps(body).encode(),
                             headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
try: r = json.load(urllib.request.urlopen(req, timeout=60))
except urllib.error.HTTPError as e: print(json.dumps({"error": f"HTTP {e.code}", "detail": e.read()[:300].decode("utf8", "replace")})); sys.exit(2)
ans = r.get("answers", {})
res, p = {}, 1.0
for i, (name, _) in enumerate(items):
    x = ans.get(f"item_{i}", {}); pr = {int(k): v for k, v in (x.get("probabilities") or {}).items()}
    p_ok = sum(v for k, v in pr.items() if k >= 2)                     # passable or better
    res[name.strip()] = {"score": x.get("score"), "p_ok": round(p_ok, 3), "confidence": x.get("confidence")}
    p *= max(p_ok, 1e-6)
blocking = [{"where": d.get("where"), "what": d.get("what"), "p_real": ans.get(f"defect_{j}", {}).get("noul")}
            for j, d in enumerate(majors) if (ans.get(f"defect_{j}", {}).get("noul") or 0) >= 0.5]
conf = min([v["confidence"] or 0 for v in res.values()] or [0])
decision = "pass" if p >= thr and not blocking else ("redo" if p < 0.3 or blocking else "ask")
outj = {"p_pass": round(p, 3), "decision": decision, "min_confidence": conf, "items": res, "blocking": blocking,
        "model": r.get("model"), "usage": r.get("usage")}
out.write_text(json.dumps(outj, indent=1)); print(json.dumps(outj)[:4000])
