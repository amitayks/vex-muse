#!/usr/bin/env python3
"""craft_check.py (skill crew) — the craft rulebook, judged by Jev (the principal, 2026-10-08).
A great scene follows rules we can state ("silence is the threat: no score under the no-answer beat").
Each rule is ONE atomic question; Jev answers it against the measured STATE of one unit (a beat, a shot,
a music section) with a calibrated probability. Code combines the answers; low confidence goes to the director.

Division of labour: hard numbers (durations, LUFS, colour distance, onset error) are checked in CODE and
written into the state as facts; fuzzy fit ("does this cue leave room for the voice?") is JEV; seeing and
hearing (what is in the frame, what the music sounds like) is GEMINI, written into the state as description.

usage:
  craft_check.py run RULES.json STATE.json OUT.json [--domain D]
  craft_check.py script-state SCRIPT.md STATE.json      # one unit per beat: beat sheet row + scene text + coverage rows
RULES.json: {"domain": "...", "rules": [{"id", "type": "noul"|"score"|"choice", "q", "want": true|false (noul),
             "criteria": [...] | {...}, "pass": min index (score) | [ok choices] (choice), "weight", "source", "when": "substring in unit tags"}]}
STATE.json: {"context": "shared facts (bible, palette, the scene's purpose)", "units": [{"id", "tags": "...", "state": "measured facts + description"}]}
Key: JEV_API_KEY. Prints a summary; OUT.json has every answer."""
import json, os, re, sys, pathlib, urllib.request, urllib.error, concurrent.futures as cf

def jev(state, questions):
    key = os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=json.dumps({"model": "jev-latest", "state": state, "questions": questions}).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try: return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e: return {"error": f"HTTP {e.code}: {e.read()[:200].decode('utf8', 'replace')}"}

def judge(rule, a):
    """-> (ok: bool|None, p_ok: float, confidence)"""
    t = rule["type"]
    if t == "noul":
        p = a.get("noul"); p = None if p is None else (p if rule.get("want", True) else 1 - p)
        return (None if p is None else p >= 0.5), p, None
    pr = a.get("probabilities") or {}
    if t == "score":
        lo = rule.get("pass", 1); p = sum(v for k, v in pr.items() if int(k) >= lo)
        return p >= 0.5, round(p, 3), a.get("confidence")
    if t == "choice":
        ok = rule.get("pass", []); p = sum(v for k, v in pr.items() if k in ok)
        return p >= 0.5, round(p, 3), a.get("confidence")

def run(rules_f, state_f, out_f, domain=None):
    R = json.loads(pathlib.Path(rules_f).read_text()); S = json.loads(pathlib.Path(state_f).read_text())
    rules = [r for r in R["rules"] if not domain or R.get("domain") == domain]
    def one(u):
        rs = [r for r in rules if not r.get("when") or r["when"] in u.get("tags", "")]
        qs = {}
        for r in rs:
            q = {"type": r["type"], "instructions": r["q"]}
            if r["type"] in ("score", "choice"): q["criteria"] = r["criteria"]
            qs[r["id"]] = q
        res = jev(S.get("context", "") + "\n\nUNIT " + u["id"] + ":\n" + u["state"], qs) if qs else {"answers": {}}
        out = []
        for r in rs:
            a = (res.get("answers") or {}).get(r["id"], {})
            ok, p, conf = judge(r, a) if a else (None, None, None)
            out.append({"rule": r["id"], "q": r["q"], "ok": ok, "p_ok": p, "confidence": conf, "answer": a.get("choice", a.get("score", a.get("noul"))), "weight": r.get("weight", 1)})
        return {"unit": u["id"], "error": res.get("error"), "results": out}
    with cf.ThreadPoolExecutor(6) as ex: units = list(ex.map(one, S["units"]))
    fails = [(u["unit"], x["rule"], x["p_ok"]) for u in units for x in u["results"] if x["ok"] is False]
    doubt = [(u["unit"], x["rule"], x["confidence"]) for u in units for x in u["results"] if x["confidence"] is not None and x["confidence"] < 0.6]
    tot = sum(x["weight"] for u in units for x in u["results"] if x["ok"] is not None)
    good = sum(x["weight"] for u in units for x in u["results"] if x["ok"])
    summary = {"rules": len(rules), "units": len(units), "fit": round(good / tot, 3) if tot else None, "fails": fails, "doubtful": doubt,
               "errors": [u["unit"] for u in units if u["error"]]}
    pathlib.Path(out_f).write_text(json.dumps({"summary": summary, "units": units}, indent=1))
    print(json.dumps(summary, indent=1))

def script_state(script_f, out_f):
    s = pathlib.Path(script_f).read_text()
    rows = {int(n): r for n, r in re.findall(r"^\| (\d+) \| ([^\n]+)$", s, re.M) if "SLOW" in r or "FAST" in r}
    heads = [(m.start(), int(m.group(1))) for m in re.finditer(r"^\*\*[^\n]*· beat (\d+)", s, re.M)]
    end = s.find("## Coverage"); units = []
    for i, (pos, b) in enumerate(heads):
        nxt = heads[i + 1][0] if i + 1 < len(heads) else end
        cov = "\n".join(l for l in s[end:].splitlines() if re.match(rf"^\| \d+[A-Z] \|[^|]+\| {b} (SLOW|FAST)", l))
        speed = "FAST" if "FAST" in rows.get(b, "") else "SLOW"
        units.append({"id": f"beat {b}", "tags": f"script {speed.lower()}" + (" dialogue" if "**" in s[pos:nxt].split("\n", 1)[1] else ""),
                      "state": f"BEAT SHEET ROW: | {b} | {rows.get(b, '')}\n\nSCENE TEXT:\n{s[pos:nxt].strip()}\n\nCOVERAGE ROWS (shot | time | beat | size | camera | on screen | heard | eye-line | sound):\n{cov}"})
    prem = re.search(r"## Premise.*?\n(.+?)\n## ", s, re.S)
    json.dump({"context": "A 60 s action scene in a photoreal AI-made short film. PREMISE: " + (prem.group(1).strip() if prem else ""), "units": units},
              open(out_f, "w"), indent=1)
    print(len(units), "units")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    if a[0] == "run": run(a[1], a[2], a[3], a[a.index("--domain") + 1] if "--domain" in a else None)
    elif a[0] == "script-state": script_state(a[1], a[2])
