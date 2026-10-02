#!/usr/bin/env python3
"""musicgen.py — one music brief -> any generator, through the ledgered fal client (or Modal for open models).

  musicgen.py providers                                   # the menu: endpoint, price, what it controls
  musicgen.py input <provider> <brief.json>                # print the provider-native input (dry run, $0)
  musicgen.py gen <provider> <brief.json> --out DIR --ledger L [--seed N] [--takes 1]
  musicgen.py gen acestep15 <brief.json> --out DIR       # open model on Modal (modal_acestep.py), cost from GPU wall time

Brief JSON (see references/briefs.md): id, prompt (style words), instrumental, duration, bpm, key,
sections[{t0,t1,name,desc,lyrics}], lyrics, hits[], reference (audio path, style conditioning), overrides{provider:{...}}.
Output: DIR/<provider>[-<take>].<ext> + DIR/<provider>.json (input, request id, cost, wall time).
Needs FAL_KEY (fal providers) or MODAL_TOKEN_ID/SECRET (acestep15). Run with $PY (tools/env.sh).
"""
import sys, os, json, subprocess, pathlib, time, shutil

HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[3]
FAL = ROOT / ".pi/skills/fal-media/scripts/fal.py"; PY = os.environ.get("PY", sys.executable)

PROVIDERS = {  # name: (endpoint, price note, controls)
    "eleven":      ("elevenlabs/music/v2.5", "$0.60 per started minute", "sections with exact ms durations (composition plan), lyrics per section, audio style reference, seed"),
    "lyria35":     ("google/lyria-3.5", "$0.10 per song", "timestamped sections in the prompt, lyrics, songs up to minutes, image inspiration"),
    "lyria3pro":   ("fal-ai/lyria3/pro", "$0.08 per song", "prompt, lyrics"),
    "lyria3":      ("fal-ai/lyria3", "$0.04 per clip", "30 s clips, prompt, lyrics"),
    "minimax3":    ("minimax/music-3", "$0.002/s", "structured caption (genre/BPM/key/arrangement), tagged lyrics (required), seed, max duration"),
    "minimax26":   ("fal-ai/minimax-music/v2.6", "$0.15 per song", "prompt, tagged lyrics, instrumental flag"),
    "sa3":         ("fal-ai/stable-audio-3/medium/text-to-audio", "$0.038 per clip", "exact duration (<=380 s), negative prompt, seed; instrumental only; inpaint/outpaint/audio-to-audio siblings"),
    "sa3-a2a":     ("fal-ai/stable-audio-3/medium/audio-to-audio", "$0.042 per clip", "re-generate a reference/source clip toward a prompt (init_noise_level 0.1 keep - 1.0 replace); instrumental"),
    "sa3-extend":  ("fal-ai/stable-audio-3/medium/audio-outpainting", "$0.045 per clip", "extend a clip before/after (seconds), prompt-guided"),
    "sa25":        ("fal-ai/stable-audio-25/text-to-audio", "$0.20 per clip", "exact duration, seed; instrumental"),
    "sonilo":      ("sonilo/v1.1/text-to-music", "$0.0025/s per sample", "exact duration, up to 3 samples; instrumental"),
    "acestep":     ("fal-ai/ace-step", "$0.0002/s", "tags, tagged lyrics, duration, seed (ACE-Step v1)"),
    "yue2":        ("modal:muse-yue2", "L40S GPU seconds (~$0.04 per 60 s song)", "style words + [Verse]/[Chorus] lyrics; writes an editable ABC score (key/tempo it chose); length from the lyrics (no duration control); covers from a score"),
    "acestep15":   ("modal:muse-acestep", "L4 GPU seconds (~$0.80/h)", "BPM, key, time signature, duration, lyrics, reference audio, cover/repaint (ACE-Step 1.5 open weights)"),
}

def mmss(t): return f"{int(t // 60)}:{int(round(t % 60)):02d}"

def style_line(b):
    s = b["prompt"].rstrip(".") + "."
    if b.get("bpm"): s += f" {b['bpm']} BPM."
    if b.get("key"): s += f" Key of {b['key']}."
    if b.get("instrumental"): s += " Instrumental only, no vocals."
    return s

def build(p, b, seed=None):
    ov = (b.get("overrides") or {}).get(p, {}); d = float(b.get("duration") or 30); secs = b.get("sections") or []
    lyr = b.get("lyrics") or ""
    if p == "eleven":
        if secs:
            base = [x.strip() for x in b["prompt"].replace(".", ",").split(",") if x.strip()][:6]
            if b.get("bpm"): base.append(f"{b['bpm']} BPM")
            if b.get("key"): base.append(b["key"])
            if b.get("instrumental"): base.append("instrumental")
            chunks = []
            for i, s in enumerate(secs):
                ms = int(round((s["t1"] - s["t0"]) * 1000))
                text = f"[{s['name']}]" + (("\n" + s["lyrics"]) if s.get("lyrics") and not b.get("instrumental") else "") + f"\n{{{s['desc']}}}"
                ch = {"text": text, "duration_ms": max(3000, ms), "positive_styles": (base if i == 0 else base[:3]) + [s["desc"]]}
                if b.get("instrumental"): ch["negative_styles"] = ["vocals", "singing"]
                chunks.append(ch)
            if b.get("reference"): chunks[0]["audio_reference"] = {"audio_url": "@file:" + str(ROOT / b["reference"]), "strength": "high"}
            inp = {"composition_plan": {"chunks": chunks}, "output_format": "mp3_44100_192"}
            if seed is not None: inp["seed"] = seed
        else:
            if b.get("reference"):
                chunk = {"text": "[Track]", "duration_ms": int(d * 1000), "positive_styles": [style_line(b)],
                         "audio_reference": {"audio_url": "@file:" + str(ROOT / b["reference"]), "strength": "high"}}
                if b.get("instrumental"): chunk["negative_styles"] = ["vocals", "singing"]
                inp = {"composition_plan": {"chunks": [chunk]}, "output_format": "mp3_44100_192"}
            else:
                inp = {"prompt": style_line(b) + (f"\nLyrics:\n{lyr}" if lyr else ""), "music_length_ms": int(d * 1000),
                       "force_instrumental": bool(b.get("instrumental")), "output_format": "mp3_44100_192"}
    elif p in ("lyria35", "lyria3pro", "lyria3"):
        txt = style_line(b) + f" The track is exactly {int(d)} seconds long ({mmss(d)})."
        if secs:
            txt += "\n" + "\n".join(f"[{mmss(s['t0'])} - {mmss(s['t1'])}] {s['name']}: {s['desc']}." + (f"\n{s['lyrics']}" if s.get("lyrics") and not b.get("instrumental") else "") for s in secs)
        elif lyr and not b.get("instrumental"): txt += "\nLyrics:\n" + lyr
        inp = {"prompt": txt}
    elif p == "minimax3":
        cap = f"Genre and style: {b['prompt']}"
        if b.get("bpm"): cap += f" BPM: {b['bpm']}."
        if b.get("key"): cap += f" Key: {b['key']}."
        if secs: cap += " Arrangement: " + " ".join(f"{s['name']} ({mmss(s['t0'])}-{mmss(s['t1'])}): {s['desc']}." for s in secs)
        if b.get("instrumental"):
            ly = "\n".join(f"[{('instrumental' if s['name'].lower() not in ('intro', 'outro') else s['name'].lower())}]" for s in secs) or "[instrumental]"
        else: ly = lyr.replace("[Verse]", "[verse]").replace("[Chorus]", "[chorus]").replace("[Bridge]", "[bridge]")
        inp = {"prompt": cap, "lyrics": ly, "duration": d}
        if seed is not None: inp["seed"] = seed
    elif p == "minimax26":
        inp = {"prompt": style_line(b)[:2000], "lyrics": "" if b.get("instrumental") else lyr, "is_instrumental": bool(b.get("instrumental")),
               "audio_setting": {"format": "mp3", "sample_rate": 44100, "bitrate": 256000}}
    elif p in ("sa3", "sa25"):
        txt = style_line(b)
        if secs: txt += " Structure: " + "; ".join(f"{s['name']} {s['desc']}" for s in secs) + "."
        inp = {"prompt": txt}
        if p == "sa3": inp.update({"duration": d, "negative_prompt": "vocals, singing, speech, low quality, distorted", "output_format": "wav"})
        else: inp["seconds_total"] = d
        if seed is not None: inp["seed"] = seed
    elif p == "sa3-a2a":
        inp = {"prompt": style_line(b), "audio_url": "@file:" + str(ROOT / (b.get("source") or b["reference"])), "duration": d,
               "init_noise_level": 0.75, "negative_prompt": "vocals, singing", "output_format": "wav"}
    elif p == "sa3-extend":
        inp = {"prompt": style_line(b), "audio_url": "@file:" + str(ROOT / (b.get("source") or b["reference"])), "extend_seconds_after": d, "output_format": "wav"}
    elif p == "sonilo":
        inp = {"prompt": style_line(b), "duration": int(round(d)), "num_samples": 1}
    elif p == "acestep":
        tags = ", ".join([x.strip() for x in b["prompt"].replace(".", ",").split(",") if x.strip()][:8] + ([f"{b['bpm']} bpm"] if b.get("bpm") else []))
        inp = {"tags": tags, "lyrics": "[inst]" if b.get("instrumental") else lyr.lower(), "duration": d}
        if seed is not None: inp["seed"] = seed
    elif p == "yue2":
        inp = {"style": "English, " + style_line(b).replace(" Instrumental only, no vocals.", ""), "lyrics": lyr or "[Instrumental]", "seed": seed if seed is not None else 7}
    elif p == "acestep15":
        inp = {"caption": style_line(b), "lyrics": "[Instrumental]" if b.get("instrumental") else lyr, "duration": d, "thinking": True, "batch": 1}
        if b.get("bpm"): inp["bpm"] = int(b["bpm"])
        if b.get("key"): inp["keyscale"] = b["key"]
        inp["timesignature"] = "4"
        if b.get("reference"): inp["reference_audio"] = str(ROOT / b["reference"])
        if seed is not None: inp["seed"] = seed
    else: raise SystemExit(f"unknown provider {p}; see `musicgen.py providers`")
    inp.update(ov); return inp

def gen(p, brief_path, out, ledger=None, seed=None, takes=1):
    b = json.loads(pathlib.Path(brief_path).read_text()); out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    for k in range(takes):
        sd = None if seed is None else seed + k; name = p if takes == 1 else f"{p}-{k + 1}"
        inp = build(p, b, sd); t0 = time.time()
        if p == "yue2":
            lf = out / f"{name}.lyrics.txt"; lf.write_text(inp["lyrics"]); tmp = out / f".{name}"
            r = subprocess.run([PY, "-m", "modal", "run", str(HERE / "modal_yue2.py") + "::gen", "--style", inp["style"], "--lyrics-file", str(lf), "--out", str(tmp), "--seed", str(inp["seed"])], capture_output=True, text=True, cwd=ROOT)
            summ = next((json.loads(l) for l in r.stdout.splitlines()[::-1] if l.startswith('{"load_s"')), None)
            if not summ: print(json.dumps({"provider": p, "error": (r.stdout + r.stderr)[-1500:]})); continue
            dst = out / f"{name}.flac"; shutil.move(str(tmp / "yue2.flac"), dst)
            if (tmp / "score.abc").exists(): shutil.move(str(tmp / "score.abc"), out / f"{name}.score.abc")
            rec = {"provider": p, "endpoint": "modal:muse-yue2", "input": inp, "file": str(dst), "est_usd": summ["est_usd"], "wall_s": round(time.time() - t0, 1), "timing": summ}
            if ledger:
                with open(ledger, "a") as f: f.write(json.dumps({"ts": int(t0), "endpoint": "modal:muse-yue2/L40S", "tag": f"{b['id']}:{name}", "est_usd": summ["est_usd"], "wall_s": rec["wall_s"], "files": [str(dst)]}) + "\n")
            shutil.rmtree(tmp, ignore_errors=True)
        elif p == "acestep15":
            jf = out / f"{name}.job.json"; jf.write_text(json.dumps(inp)); tmp = out / f".{name}"
            r = subprocess.run([PY, "-m", "modal", "run", str(HERE / "modal_acestep.py") + "::gen", "--job", str(jf), "--out", str(tmp)], capture_output=True, text=True, cwd=ROOT)
            summ = next((json.loads(l) for l in r.stdout.splitlines()[::-1] if l.startswith('{"out"')), None)
            if not summ: print(json.dumps({"provider": p, "error": (r.stdout + r.stderr)[-1500:]})); continue
            wav = sorted(tmp.glob("*.wav")); dst = out / f"{name}.wav"
            if wav: shutil.move(str(wav[0]), dst)
            meta = json.loads((tmp / "meta.json").read_text()) if (tmp / "meta.json").exists() else {}
            rec = {"provider": p, "endpoint": "modal:muse-acestep", "input": inp, "file": str(dst), "est_usd": summ["est_usd"], "gpu_wall_s": summ["container_wall_s"],
                   "wall_s": round(time.time() - t0, 1), "lm_metadata": meta.get("lm_metadata"), "timing": meta.get("timing")}
            if ledger:
                with open(ledger, "a") as f: f.write(json.dumps({"ts": int(t0), "endpoint": "modal:muse-acestep/L4", "tag": f"{b['id']}:{name}", "est_usd": summ["est_usd"], "wall_s": rec["wall_s"], "files": [str(dst)]}) + "\n")
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            ep = PROVIDERS[p][0]; jf = out / f"{name}.input.json"; jf.write_text(json.dumps(inp)); tmp = out / f".{name}"
            cmd = ["python3", str(FAL), "run", ep, str(jf), "--out", str(tmp), "--tag", f"{b['id']}:{name}"] + (["--ledger", ledger] if ledger else [])
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode: print(json.dumps({"provider": p, "error": (r.stderr or r.stdout)[-1500:]})); shutil.rmtree(tmp, ignore_errors=True); continue
            res = json.loads(r.stdout); files = res["ledger"]["files"]; auds = [f for f in files if f.endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg"))]
            dst = None
            if auds:
                dst = out / f"{name}{pathlib.Path(auds[0]).suffix}"; shutil.move(auds[0], dst)
            rec = {"provider": p, "endpoint": ep, "input": inp, "file": str(dst) if dst else None, "request_id": res["ledger"]["request_id"],
                   "est_usd": res["ledger"]["est_usd"], "wall_s": res["ledger"]["wall_s"],
                   "extra": {k: v for k, v in res["result"].items() if k in ("lyrics", "seed", "duration", "tags")}}
            shutil.rmtree(tmp, ignore_errors=True)
        (out / f"{name}.json").write_text(json.dumps(rec, indent=1)); print(json.dumps({k: rec[k] for k in ("provider", "file", "est_usd", "wall_s")}))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    if a[0] == "providers":
        for k, (ep, price, ctl) in PROVIDERS.items(): print(f"{k:<11} {ep:<46} {price:<28} {ctl}")
    elif a[0] == "input": print(json.dumps(build(a[1], json.loads(pathlib.Path(a[2]).read_text()), None), indent=1))
    elif a[0] == "gen": gen(a[1], a[2], opt("--out", "."), opt("--ledger"), int(opt("--seed")) if opt("--seed") else None, int(opt("--takes", 1)))
    else: print(__doc__)
