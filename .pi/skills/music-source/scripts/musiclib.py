#!/usr/bin/env python3
"""musiclib.py — get any song, beat or soundtrack as a first-class asset, plus Muse's small music library.

Run with $PY (tools/env.sh; needs the yt_dlp module + ffmpeg).

  musiclib.py search "<query>" [--kind song|instrumental|beat|ost|acappella|extended] [--src yt,sc] [--n 8]
  musiclib.py fetch <url | "query"> [--kind ...] [--out DIR] [--via auto|local|modal] [--lufs -14] [--expect SECONDS]
  musiclib.py lyrics "<artist>" "<title>" [--duration S] [--out DIR]        # LRCLIB synced (.lrc) + plain (.txt)
  musiclib.py meta "<artist>" "<title>"                                      # MusicBrainz + Deezer (bpm, isrc) + iTunes
  musiclib.py open "<query>" [--src openverse|archive|ccmixter] [--license cc0,by] [--n 10] [--get I --out DIR]
  musiclib.py add <audio> [--title T --artist A --kind K --tags a,b --source URL --license L --song song.json]
  musiclib.py ls [--q text] [--kind beat] [--tag t] [--bpm 120-130] [--key "A minor"] [--max-dur 60]
  musiclib.py rm <slug> | du

fetch writes <out>/<slug>.<ext> (best audio stream, untouched), <slug>.norm.mp3 (320k, loudness-normalised
two-pass to --lufs / -1 dBTP) and <slug>.source.json (url, extractor, title, uploader, duration, codec,
fetched_at, via). YouTube is bot-walled from this box's IP: --via auto tries local, then Modal
(song-map/scripts/modal_audio.py::fetch), then the best duration-matched SoundCloud/Bandcamp copy.
No DRM circumvention: encrypted streams (Spotify, Apple Music, Tidal, Deezer full tracks) are out of scope.
Library: library/music/<slug>/ + library/music/index.json; hard cap LIB_CAP_MB (disk law).
"""
import sys, os, json, re, subprocess, time, shutil, urllib.request, urllib.parse, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[4]
LIB = ROOT / "library" / "music"; INDEX = LIB / "index.json"; LIB_CAP_MB = 1500
UA = "Muse/1.0 (music-video studio; personal non-commercial)"
PY = os.environ.get("PY", sys.executable)
KIND_Q = {"song": "{q} official audio", "instrumental": "{q} official instrumental", "beat": "{q} type beat",
          "ost": "{q} original soundtrack", "acappella": "{q} acapella", "extended": "{q} extended mix", "any": "{q}"}
AVOID = re.compile(r"\b(live|cover|sped ?up|slowed|nightcore|8d|reverb|bass ?boosted|karaoke|reaction|tutorial|remix)\b", re.I)

def die(m): print(json.dumps({"error": m}), file=sys.stderr); sys.exit(1)
def slugify(s): return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:60] or "track"
def getj(url, timeout=40, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
def ytdlp(*args, check=True):
    r = subprocess.run([PY, "-m", "yt_dlp", "--no-warnings", "--js-runtimes", "node", *args], capture_output=True, text=True)
    if check and r.returncode: raise RuntimeError((r.stderr or r.stdout)[-800:])
    return r

# ---------- search ----------
def search(q, kind="song", srcs=("yt", "sc"), n=8):
    qq = KIND_Q.get(kind, "{q}").format(q=q); out = []
    for s in srcs:
        pre = {"yt": "ytsearch", "sc": "scsearch"}.get(s)
        if not pre: continue
        try: r = ytdlp("--flat-playlist", "-J", f"{pre}{n}:{qq}")
        except RuntimeError as e: out.append({"src": s, "error": str(e)[-200:]}); continue
        for e in json.loads(r.stdout).get("entries", []):
            url = e.get("url") or e.get("webpage_url")
            if s == "yt" and e.get("id"): url = f"https://www.youtube.com/watch?v={e['id']}"
            out.append({"src": s, "title": e.get("title"), "channel": e.get("channel") or e.get("uploader"),
                        "duration": e.get("duration"), "url": url, "views": e.get("view_count")})
    for c in out: c["score"] = score(c, q, kind)
    return sorted([c for c in out if "error" not in c], key=lambda c: -c["score"]) + [c for c in out if "error" in c]

def score(c, q, kind):
    t = f"{c.get('title') or ''} {c.get('channel') or ''}".lower(); s = 0.0
    s += sum(1 for w in re.findall(r"\w+", q.lower()) if w in t)
    if re.search(r"- topic|vevo|official", t): s += 2
    if kind in ("instrumental", "beat", "ost", "acappella") and re.search({"instrumental": "instrumental", "beat": "beat", "ost": "soundtrack|ost|score|theme", "acappella": "acapella|a cappella|vocals only"}[kind], t): s += 3
    if AVOID.search(t) and not AVOID.search(q): s -= 3
    d = c.get("duration") or 0
    if d and d <= 31: s -= 5  # SoundCloud Go+ previews are 30 s
    if c.get("views"): s += min(2, len(str(int(c["views"]))) / 5)
    return round(s, 2)

# ---------- fetch ----------
def loudnorm(src, dst, lufs=-14.0, tp=-1.0):
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", "44100", "-b:a", "320k", dst], check=True)
    return {"input_lufs": float(j["input_i"]), "input_tp": float(j["input_tp"])}

def fetch_local(url, out, slug):
    r = ytdlp("-f", "bestaudio/best", "--no-playlist", "-x", "-o", str(out / f"{slug}.%(ext)s"), "--print-json", url)
    info = json.loads(r.stdout.strip().splitlines()[-1])
    f = next((p for p in out.glob(f"{slug}.*") if not p.name.endswith((".json", ".norm.mp3", ".part"))), None)
    return f, info

def fetch_modal(url, out, slug):
    script = ROOT / ".pi/skills/song-map/scripts/modal_audio.py"
    tmp = out / f".modal-{slug}"; r = subprocess.run([PY, "-m", "modal", "run", f"{script}::fetch", "--url", url, "--out", str(tmp)], capture_output=True, text=True, cwd=ROOT)
    line = next((l for l in r.stdout.splitlines()[::-1] if l.startswith("{")), None)
    if r.returncode or not line: raise RuntimeError((r.stdout + r.stderr)[-600:])
    j = json.loads(line); src = pathlib.Path(j["file"]); dst = out / f"{slug}{src.suffix}"; shutil.move(src, dst); shutil.rmtree(tmp, ignore_errors=True)
    return dst, j["meta"]

def fetch(target, kind="song", out="projects/_inbox/audio", via="auto", lufs=-14.0, expect=None):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True); tried = []
    cands = [{"url": target, "title": None}] if re.match(r"https?://", target) else [c for c in search(target, kind) if "error" not in c]
    if not cands: die(f"no results for {target}")
    if expect and len(cands) > 1:  # a known album length (LRCLIB/iTunes/MusicBrainz) beats a music-video cut with skits
        near = [c for c in cands if c.get("duration") and abs(c["duration"] - float(expect)) <= max(4, 0.03 * float(expect))]
        if near: cands = near + [c for c in cands if c not in near]
    first = cands[0]
    slug = slugify(first.get("title") or target.rsplit("/", 1)[-1])
    # expected length: the hint, else the median of the top YouTube hits (official uploads agree with each other)
    yd = sorted(c["duration"] for c in cands[:6] if c.get("src") == "yt" and c.get("duration"))
    exp = float(expect) if expect else (yd[len(yd) // 2] if yd else None)
    ok = lambda c: c is first or (c.get("score", 0) > 0 and (not exp or not c.get("duration") or abs(c["duration"] - exp) / exp < 0.12))
    order = [first] + [c for c in cands[1:] if ok(c)][:5]
    for c in order:
        url = c["url"]; is_yt = "youtube.com" in url or "youtu.be" in url
        slug = slugify(c.get("title") or slug)
        modes = ["local", "modal", "modal"] if (via == "auto" and is_yt) else ([via] if via != "auto" else ["local"])
        for m in modes:
            try:
                f, info = (fetch_local if m == "local" else fetch_modal)(url, out, slug)
                if not f: raise RuntimeError("no file written")
                ln = loudness_probe(str(f))
                if ln is not None and ln > -5.0:  # bass-boosted / clipped re-upload, never a real master
                    f.unlink(); raise RuntimeError(f"rejected: {ln:.1f} LUFS input looks like a boosted re-upload")
                meta = {"url": url, "via": m, "kind": kind, "query": None if target == url else target, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "title": info.get("title"), "uploader": info.get("uploader") or info.get("channel"), "duration": info.get("duration"),
                        "extractor": info.get("extractor") or ("youtube" if is_yt else None), "acodec": info.get("acodec"), "abr": info.get("abr"),
                        "file": f.name, "fallback_from": tried or None}
                meta.update(loudnorm(str(f), str(out / f"{slug}.norm.mp3"), lufs)); meta["norm_file"] = f"{slug}.norm.mp3"; meta["norm_lufs"] = lufs
                (out / f"{slug}.source.json").write_text(json.dumps(meta, indent=1))
                print(json.dumps(meta)); return meta
            except Exception as e:
                tried.append({"url": url, "via": m, "error": str(e)[-160:]})
    die(json.dumps({"failed": tried}))

def loudness_probe(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", r[r.rfind("Summary:"):]); return float(m.group(1)) if m else None

# ---------- lyrics / metadata ----------
def lyrics(artist, title, duration=None, out=None):
    q = {"artist_name": artist, "track_name": title}
    if duration: q["duration"] = int(float(duration))
    try: d = getj("https://lrclib.net/api/get?" + urllib.parse.urlencode(q))
    except Exception:
        res = getj("https://lrclib.net/api/search?" + urllib.parse.urlencode({"q": f"{artist} {title}"}))
        if not res: die("no lyrics on LRCLIB")
        d = sorted(res, key=lambda r: (not r.get("syncedLyrics"), abs((r.get("duration") or 0) - float(duration or r.get("duration") or 0))))[0]
    rec = {"source": "lrclib", "id": d.get("id"), "artist": d.get("artistName"), "title": d.get("trackName"), "album": d.get("albumName"),
           "duration": d.get("duration"), "instrumental": d.get("instrumental"), "synced": bool(d.get("syncedLyrics"))}
    lines = []
    for l in (d.get("syncedLyrics") or "").splitlines():
        m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)", l)
        if m and m.group(3).strip(): lines.append({"t": round(int(m.group(1)) * 60 + float(m.group(2)), 2), "text": m.group(3).strip()})
    rec["lines"] = len(lines)
    if out:
        o = pathlib.Path(out); o.mkdir(parents=True, exist_ok=True)
        (o / "lyrics.txt").write_text((d.get("plainLyrics") or "\n".join(x["text"] for x in lines)).strip() + "\n")
        if lines: (o / "lyrics.lrc").write_text(d["syncedLyrics"]); (o / "lyrics_lines.json").write_text(json.dumps(lines, indent=0))
        rec["out"] = str(o)
    print(json.dumps(rec)); return rec

def meta(artist, title):
    out = {}
    try:
        mb = getj("https://musicbrainz.org/ws/2/recording?" + urllib.parse.urlencode({"query": f'recording:"{title}" AND artist:"{artist}"', "fmt": "json", "limit": 5}))
        out["musicbrainz"] = [{"mbid": r["id"], "title": r["title"], "length_s": (r.get("length") or 0) / 1000, "first_release": r.get("first-release-date"),
                               "artist": ", ".join(a["name"] for a in r.get("artist-credit", []))} for r in mb.get("recordings", [])]
    except Exception as e: out["musicbrainz"] = str(e)[:120]
    try:
        dz = getj("https://api.deezer.com/search?" + urllib.parse.urlencode({"q": f'artist:"{artist}" track:"{title}"', "limit": 3}))
        if not dz.get("data"):  # the advanced syntax often returns nothing (e.g. Avicii Levels): plain query
            dz = getj("https://api.deezer.com/search?" + urllib.parse.urlencode({"q": f"{artist} {title}", "limit": 3}))
        tr = []
        for t in dz.get("data", []):
            full = getj(f"https://api.deezer.com/track/{t['id']}")
            tr.append({"title": full.get("title"), "duration": full.get("duration"), "bpm": full.get("bpm"), "gain_db": full.get("gain"), "isrc": full.get("isrc"), "release": full.get("release_date")})
        out["deezer"] = tr  # deezer bpm is a hint (often 0 or ×2/½): verify with song-map
    except Exception as e: out["deezer"] = str(e)[:120]
    try:
        it = getj("https://itunes.apple.com/search?" + urllib.parse.urlencode({"term": f"{artist} {title}", "entity": "song", "limit": 3}))
        out["itunes"] = [{"title": t["trackName"], "artist": t["artistName"], "album": t.get("collectionName"), "genre": t.get("primaryGenreName"),
                          "duration": t.get("trackTimeMillis", 0) / 1000, "released": t.get("releaseDate", "")[:10]} for t in it.get("results", [])]
    except Exception as e: out["itunes"] = str(e)[:120]
    print(json.dumps(out, indent=1)); return out

# ---------- open libraries ----------
def open_search(q, src="openverse", license=None, n=10):
    res = []
    if src == "openverse":
        p = {"q": q, "page_size": n}
        if license: p["license"] = license
        d = getj("https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode(p))
        res = [{"title": r["title"], "by": r.get("creator"), "license": f"{r['license']} {r.get('license_version') or ''}".strip(), "duration": (r.get("duration") or 0) / 1000,
                "provider": r.get("source"), "url": r["url"], "page": r.get("foreign_landing_url"), "attribution": r.get("attribution")} for r in d.get("results", [])]
    elif src == "archive":
        qq = f"({q}) AND mediatype:audio" + (" AND licenseurl:*creativecommons*" if license else "")
        d = getj("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": qq, "fl[]": ["identifier", "title", "creator", "licenseurl"], "rows": n, "output": "json"}, doseq=True))
        for x in d["response"]["docs"]:
            files = getj(f"https://archive.org/metadata/{x['identifier']}/files").get("result", [])
            mp3 = next((f["name"] for f in files if f.get("name", "").lower().endswith((".mp3", ".flac", ".ogg"))), None)
            res.append({"title": x.get("title"), "by": x.get("creator"), "license": x.get("licenseurl"), "page": f"https://archive.org/details/{x['identifier']}",
                        "url": f"https://archive.org/download/{x['identifier']}/{urllib.parse.quote(mp3)}" if mp3 else None})
    elif src == "ccmixter":
        d = getj("http://ccmixter.org/api/query?" + urllib.parse.urlencode({"f": "json", "search": q, "limit": n, "sort": "rank"}))
        res = [{"title": x.get("upload_name"), "by": x.get("user_name"), "license": x.get("license_name"), "page": x.get("file_page_url"),
                "url": (x.get("files") or [{}])[0].get("download_url"), "tags": (x.get("upload_tags") or "")[:120]} for x in d]
    print(json.dumps(res, indent=1)); return res

def open_get(item, out):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True); slug = slugify(item["title"] or "open")
    ext = os.path.splitext(urllib.parse.urlparse(item["url"]).path)[1] or ".mp3"
    if "jamendo" in item["url"]: ext = ".mp3"
    f = out / f"{slug}{ext}"
    with urllib.request.urlopen(urllib.request.Request(item["url"], headers={"User-Agent": UA}), timeout=300) as r: f.write_bytes(r.read())
    m = dict(item, file=f.name, fetched_at=time.strftime("%Y-%m-%dT%H:%M:%S%z")); m.update(loudnorm(str(f), str(out / f"{slug}.norm.mp3"))); m["norm_file"] = f"{slug}.norm.mp3"
    (out / f"{slug}.source.json").write_text(json.dumps(m, indent=1)); print(json.dumps(m)); return m

# ---------- library ----------
def lib_load(): return json.loads(INDEX.read_text()) if INDEX.exists() else {"tracks": []}
def lib_save(ix): LIB.mkdir(parents=True, exist_ok=True); INDEX.write_text(json.dumps(ix, indent=1))
def du(): return sum(p.stat().st_size for p in LIB.rglob("*") if p.is_file()) / 1e6 if LIB.exists() else 0.0

def add(audio, title=None, artist=None, kind="song", tags="", source=None, license=None, song=None):
    src = pathlib.Path(audio); side = src.with_name(src.name.replace(".norm.mp3", "").rsplit(".", 1)[0] + ".source.json")
    sj = json.loads(side.read_text()) if side.exists() else {}
    title = title or sj.get("title") or src.stem; slug = slugify(f"{artist + '-' if artist else ''}{title}")
    size = src.stat().st_size / 1e6
    if du() + size > LIB_CAP_MB: die(f"library would exceed {LIB_CAP_MB} MB (now {du():.0f} MB): rm something first")
    d = LIB / slug; d.mkdir(parents=True, exist_ok=True); dst = d / ("audio.mp3" if src.suffix == ".mp3" else f"audio{src.suffix}")
    shutil.copy2(src, dst)
    if not song:
        sm = ROOT / ".pi/skills/song-map/scripts/songmap.py"; song = d / "song.json"
        subprocess.run([PY, str(sm), "analyze", str(dst), "--out", str(song), "--no-words"], check=True, capture_output=True)
    else: shutil.copy2(song, d / "song.json"); song = d / "song.json"
    s = json.loads(pathlib.Path(song).read_text())
    ent = {"slug": slug, "title": title, "artist": artist or sj.get("uploader"), "kind": kind, "tags": [t for t in tags.split(",") if t],
           "source": source or sj.get("url"), "license": license or sj.get("license") or "personal-use", "file": str(dst.relative_to(ROOT)),
           "duration": s.get("duration"), "bpm": s.get("bpm"), "key": s.get("key"), "lufs": s.get("lufs"),
           "sections": [{"t0": x["t0"], "t1": x["t1"], "label": x.get("label"), "energy": x.get("energy")} for x in s.get("sections", [])],
           "hits": s.get("hits", [])[:12], "added": time.strftime("%Y-%m-%d")}
    ix = lib_load(); ix["tracks"] = [t for t in ix["tracks"] if t["slug"] != slug] + [ent]; lib_save(ix)
    print(json.dumps({k: ent[k] for k in ("slug", "title", "bpm", "key", "duration", "lufs")} | {"sections": len(ent["sections"]), "lib_mb": round(du(), 1)}))

def ls(q=None, kind=None, tag=None, bpm=None, key=None, max_dur=None):
    rows = lib_load()["tracks"]
    if q: rows = [t for t in rows if q.lower() in json.dumps(t).lower()]
    if kind: rows = [t for t in rows if t.get("kind") == kind]
    if tag: rows = [t for t in rows if tag in t.get("tags", [])]
    if key: rows = [t for t in rows if (t.get("key") or "").lower() == key.lower()]
    if max_dur: rows = [t for t in rows if (t.get("duration") or 0) <= float(max_dur)]
    if bpm:
        lo, hi = (float(x) for x in bpm.split("-"))
        rows = [t for t in rows if t.get("bpm") and (lo <= t["bpm"] <= hi or lo <= t["bpm"] * 2 <= hi or lo <= t["bpm"] / 2 <= hi)]
    for t in rows: print(f"{t['slug']:<40} {t.get('kind',''):<12} {t.get('bpm') or '':>6} {t.get('key') or '':<10} {t.get('duration') or 0:>7.1f}s  {','.join(t.get('tags', []))}")
    print(f"-- {len(rows)} tracks, library {du():.1f} MB / cap {LIB_CAP_MB} MB")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    c = a[0]
    if c == "search":
        for r in search(a[1], opt("--kind", "song"), tuple(opt("--src", "yt,sc").split(",")), int(opt("--n", 8))): print(json.dumps(r))
    elif c == "fetch": fetch(a[1], opt("--kind", "song"), opt("--out", "projects/_inbox/audio"), opt("--via", "auto"), float(opt("--lufs", -14)), opt("--expect"))
    elif c == "lyrics": lyrics(a[1], a[2], opt("--duration"), opt("--out"))
    elif c == "meta": meta(a[1], a[2])
    elif c == "open":
        res = open_search(a[1], opt("--src", "openverse"), opt("--license"), int(opt("--n", 10)))
        if opt("--get") is not None: open_get(res[int(opt("--get"))], opt("--out", "projects/_inbox/audio"))
    elif c == "add": add(a[1], opt("--title"), opt("--artist"), opt("--kind", "song"), opt("--tags", ""), opt("--source"), opt("--license"), opt("--song"))
    elif c == "ls": ls(opt("--q"), opt("--kind"), opt("--tag"), opt("--bpm"), opt("--key"), opt("--max-dur"))
    elif c == "rm":
        ix = lib_load(); ix["tracks"] = [t for t in ix["tracks"] if t["slug"] != a[1]]; lib_save(ix); shutil.rmtree(LIB / a[1], ignore_errors=True); print(f"removed {a[1]}")
    elif c == "du": print(f"{du():.1f} MB / cap {LIB_CAP_MB} MB")
    else: print(__doc__)
