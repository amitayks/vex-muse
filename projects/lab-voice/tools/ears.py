#!/usr/bin/env python3
"""ears.py — blind listening proxy for the v3/v4/v4turbo bench (OpenAI gpt-audio via antioch ear.py).
 - accent: blind accent ID on the Scouse (boh_line) and Glaswegian (fir_plain) takes, per model
 - identity: "same speaker?" v3 take vs v4 / v4turbo take of the same voice
 - prefer: pairwise "which delivery is better", run in BOTH orders; only order-robust wins count
Writes ../review/ears.json. Treat as shortlisting evidence, never as the final ear."""
import json, sys, re, concurrent.futures as cf
sys.path.insert(0, "/data/workspaces/<workspace>/projects/antioch-1098/tools")
import ear
P = "/data/workspaces/<workspace>/projects/lab-voice"; T = f"{P}/takes"
MODELS = ["v3", "v4", "v4turbo"]

def js(s):
    m = re.search(r"\{.*\}", s, re.S)
    try: return json.loads(m.group(0)) if m else {"raw": s}
    except Exception: return {"raw": s}

def accent(model, item, take):
    f = f"{T}/{model}/{item}_t{take}.mp3"
    return dict(kind="accent", model=model, item=item, take=take, **js(ear.call([{"type": "text", "text": ear.ACCENT_Q}, ear.clip(f)])))

SAME_Q = ("Two short clips. Judge ONLY the speaker's vocal identity (timbre, pitch, accent), not the words or recording quality. "
          "Reply as compact JSON: {\"same_speaker\": 0-1 probability, \"differences\": up to 8 words}")
def identity(item, other):
    a, b = f"{T}/v3/{item}_t1.mp3", f"{T}/{other}/{item}_t1.mp3"
    return dict(kind="identity", item=item, pair=f"v3~{other}", **js(ear.call([{"type": "text", "text": SAME_Q}, ear.clip(a), ear.clip(b)])))

PREF_Q = ("Two takes of the same line for a narrated audio drama. Clip 1 then clip 2. Which is the better performance for a "
          "listener: natural prosody, believable emotion, clean audio, correct pronunciation, no glitches? "
          "Reply as compact JSON: {\"winner\": 1 or 2, \"margin\": \"slight|clear|large\", \"why\": up to 12 words}")
def prefer(item, a, b, order):
    fa, fb = f"{T}/{a}/{item}_t1.mp3", f"{T}/{b}/{item}_t1.mp3"
    clips = [fa, fb] if order == 0 else [fb, fa]
    r = js(ear.call([{"type": "text", "text": PREF_Q}] + [ear.clip(c) for c in clips]))
    w = r.pop("winner", None); r["said"] = w
    try: w = int(w)
    except Exception: w = None
    winner = None if w not in (1, 2) else ([a, b] if order == 0 else [b, a])[w - 1]
    return dict(kind="prefer", item=item, pair=f"{a}|{b}", order=order, winner=winner, **r)

if __name__ == "__main__":
    jobs = []
    for m in MODELS:
        for it in ("boh_line", "fir_plain"):
            for t in (1, 2): jobs.append((accent, (m, it, t)))
    for it in ("nar_long", "boh_line", "fir_plain"):
        for o in ("v4", "v4turbo"): jobs.append((identity, (it, o)))
    for it in ("nar_long", "nar_names", "boh_line", "fir_whisper", "nar_he"):
        for a, b in (("v3", "v4"), ("v4", "v4turbo")):
            for order in (0, 1): jobs.append((prefer, (it, a, b, order)))
    def safe(j):
        try: return j[0](*j[1])
        except Exception as e: return dict(kind=j[0].__name__, args=list(j[1]), error=str(e)[:200])
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(safe, jobs))
    json.dump(res, open(f"{P}/review/ears.json", "w"), indent=1, ensure_ascii=False)
    for r in res: print(json.dumps(r, ensure_ascii=False)[:220])
