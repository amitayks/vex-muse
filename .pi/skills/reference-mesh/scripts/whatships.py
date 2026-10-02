#!/usr/bin/env python3
"""whatships.py — query whatships.com (curated launch videos from X) as a live reference source.

  whatships.py sync  [--from FILE] [--force]         cache the catalog (auto on first use, max age 24 h)
  whatships.py find  [TEXT] [--cat motion,design] [--since YYYY-MM-DD | --days N] [--until YYYY-MM-DD]
                     [--author HANDLE] [--min-views N] [--sort date|views|dur] [--limit 20] [--json]
  whatships.py show  SLUG                            one entry, full fields + original X URL
  whatships.py cats                                  categories with counts and newest date
  whatships.py tools [TEXT] | studios [TEXT]         the site's tool / studio directories
  whatships.py wall  [find filters] [--cols 4] [--out FILE]   poster contact wall (numbered) + legend
  whatships.py fetch SLUG... [--study] [--no-video] [--sheet-fps 2]   hand-off: xfetch.py the original X
                                                               post, then framestudy.py its video (--study)

Source: the site's public repo (github.com/dingyi/whatships.com, src/data/*.json via
raw.githubusercontent.com) — whatships.com's own JSON endpoints answer 403 (Cloudflare) from this box.
--from FILE accepts a saved videos.json, or the site's /search-index.json (no dates, no X URLs).
Cache: <workspace>/research/whatships/ (videos.json, tools.json, studios.json, meta.json with commit + fetch time).
Rights: study only. Cite the directory page AND the original X post; never re-host the videos.
wall/fetch need ffmpeg (source tools/env.sh); --study needs $PY (numpy/opencv).
"""
import json, os, sys, time, subprocess, datetime, urllib.request, tempfile, shutil, glob

RAW = "https://raw.githubusercontent.com/dingyi/whatships.com/main/"
API = "https://api.github.com/repos/dingyi/whatships.com/commits?path=src/data/videos.json&per_page=1"
SITE = "https://whatships.com"
UA = {"User-Agent": "muse-reference-mesh/1.0 (+study; cites original X posts)"}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))          # workspace root (script lives in .pi/skills/…)
CACHE = os.environ.get("WHATSHIPS_CACHE", os.path.join(ROOT, "research", "whatships"))
MAX_AGE = 24 * 3600


def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        b = r.read()
        return b if raw else json.loads(b)


def p(name): return os.path.join(CACHE, name)


def sync(src=None, force=False):
    os.makedirs(CACHE, exist_ok=True)
    meta = json.load(open(p("meta.json"))) if os.path.exists(p("meta.json")) else {}
    if not force and not src and meta and time.time() - meta.get("fetched", 0) < MAX_AGE:
        return meta
    if src:  # local file: full videos.json (list of entries) or the site's search-index.json
        try: d = json.load(open(src))
        except ValueError: sys.exit(f"error: {src} is not JSON (a saved Cloudflare 403 page?) — save the endpoint body itself")
        if d and "tweetUrl" not in d[0]:  # search-index shape -> minimal entries
            d = [{"slug": x.get("slug"), "title": x.get("name"), "company": (x.get("meta") or "").split(" · ")[0],
                  "category": ((x.get("meta") or "").split(" · ") + [""])[1].lower(), "product": x.get("name"),
                  "description": x.get("searchText", ""), "tags": [], "tweetUrl": None, "publishedAt": None,
                  "status": "published", "poster": x.get("poster")} for x in d if x.get("kind", "video") == "video"]
        json.dump(d, open(p("videos.json"), "w")); meta = {"fetched": time.time(), "source": os.path.abspath(src), "n": len(d)}
    else:
        d = get(RAW + "src/data/videos.json")
        json.dump(d, open(p("videos.json"), "w"))
        for extra in ("tools", "studios"):
            try: json.dump(get(RAW + f"src/data/{extra}.json"), open(p(f"{extra}.json"), "w"))
            except Exception as e: print(f"warn: {extra}.json {e}", file=sys.stderr)
        commit = {}
        try:
            c = get(API)[0]; commit = {"sha": c["sha"][:10], "date": c["commit"]["committer"]["date"], "msg": c["commit"]["message"][:100]}
        except Exception: pass
        meta = {"fetched": time.time(), "source": RAW + "src/data/", "n": len(d), "commit": commit}
    json.dump(meta, open(p("meta.json"), "w"), indent=1)
    return meta


def load(name="videos.json"):
    sync()
    return json.load(open(p(name))) if os.path.exists(p(name)) else []


def opt(a, f, d=None): return a[a.index(f) + 1] if f in a else d


def positional(a):
    """Arguments that are not flags or flag values."""
    out, skip = [], False
    for i, x in enumerate(a):
        if skip: skip = False; continue
        if x.startswith("--"):
            skip = x not in ("--json", "--study", "--force", "--all", "--no-video")
            continue
        out.append(x)
    return out


def text_of(v):
    return " ".join(str(v.get(k) or "") for k in ("title", "product", "company", "description", "authorHandle", "authorName")) \
        + " " + " ".join(v.get("tags") or [])


def find(a):
    v = load(); q = " ".join(positional(a)).lower().split()
    cats = set((opt(a, "--cat") or "").lower().split(",")) - {""}
    since = opt(a, "--since"); until = opt(a, "--until"); days = opt(a, "--days")
    if days: since = (datetime.date.today() - datetime.timedelta(days=int(days))).isoformat()
    author = (opt(a, "--author") or "").lower().lstrip("@"); minv = int(opt(a, "--min-views", 0))
    r = []
    for x in v:
        if x.get("status", "published") != "published" and "--all" not in a: continue
        if cats and (x.get("category") or "") not in cats: continue
        d = (x.get("publishedAt") or "")[:10]
        if since and (not d or d < since): continue
        if until and (not d or d > until): continue
        if author and (x.get("authorHandle") or "").lower() != author: continue
        if minv and (x.get("views") or 0) < minv: continue
        t = text_of(x).lower()
        if q and not all(w in t for w in q): continue
        r.append(x)
    key = {"date": lambda x: x.get("publishedAt") or "", "views": lambda x: x.get("views") or 0,
           "dur": lambda x: x.get("durationSeconds") or 0}[opt(a, "--sort", "date")]
    r.sort(key=key, reverse=True)
    return r[: int(opt(a, "--limit", 20))]


def row(x):
    views = x.get("views"); views = f"{views / 1000:.0f}k" if views else "-"
    return (f"{(x.get('publishedAt') or '?')[:10]}  {(x.get('category') or '?'):<15} {str(x.get('durationSeconds') or '?'):>4}s "
            f"{views:>6}  {x['slug']:<32} {(x.get('title') or '')[:64]}\n{'':>12}{x.get('tweetUrl') or '(no X url in this source)'}")


def show(slug):
    for x in load():
        if x["slug"] == slug:
            return x | {"page": f"{SITE}/videos/{slug}/", "cite": f"{x.get('title')} — {x.get('company')}; "
                        f"{SITE}/videos/{slug}/ ; original X post: {x.get('tweetUrl')}"}
    return None


def wall(a):
    if not shutil.which("ffmpeg"): sys.exit("error: ffmpeg not on PATH — run `source tools/env.sh` first")
    r = find(a); cols = int(opt(a, "--cols", 4)); out = opt(a, "--out", p(f"wall-{datetime.date.today()}.jpg"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="wswall-"); legend = []
    try:
        k = 0
        for x in r:
            pos = (x.get("poster") or f"/posters/{x['slug']}.webp").replace(".webp", "-960.webp")
            try: b = get(RAW + "public" + pos, raw=True)
            except Exception:
                try: b = get(RAW + "public" + (x.get("poster") or ""), raw=True)
                except Exception: continue
            k += 1; open(os.path.join(tmp, f"{k:03d}.webp"), "wb").write(b)
            legend.append(f"{k:>2}. {x['slug']} · {(x.get('publishedAt') or '')[:10]} · {x.get('tweetUrl')}")
        if not k: return {"error": "no posters matched"}
        rows = (k + cols - 1) // cols
        # images differ in size: normalise each to 480x270 letterboxed, then tile; ffmpeg has no drawtext here,
        # so numbering lives in the legend (reading order: left-to-right, top-to-bottom).
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%03d.webp"), "-vf",
                        f"scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2:color=0x111111,"
                        f"tile={cols}x{rows}:padding=6:margin=6:color=0x222222", "-frames:v", "1", "-q:v", "3", out], check=True)
        open(out.rsplit(".", 1)[0] + ".txt", "w").write("\n".join(legend) + "\n")
        return {"wall": out, "legend": out.rsplit(".", 1)[0] + ".txt", "n": k}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fetch(a):
    res = []
    for slug in positional(a):
        x = show(slug)
        if not x or not x.get("tweetUrl"): res.append({"slug": slug, "error": "unknown slug or no X url"}); continue
        # run from the workspace root so xfetch's own convention holds: research/x/<poster>-<id>/
        cmd = [sys.executable, os.path.join(HERE, "xfetch.py"), x["tweetUrl"], "--sheet-fps", opt(a, "--sheet-fps", "2")]
        if "--no-video" in a: cmd.append("--no-video")
        pr = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        try: rep = json.loads(pr.stdout.strip().splitlines()[-1]); rep["out"] = os.path.join(ROOT, rep["out"])
        except Exception: res.append({"slug": slug, "error": (pr.stderr or pr.stdout)[-400:]}); continue
        rep["videos"] = [v | {"file": os.path.join(ROOT, v["file"])} for v in rep.get("videos", [])]
        json.dump({k: x.get(k) for k in ("slug", "title", "company", "category", "publishedAt", "durationSeconds", "tags",
                   "tweetUrl", "page", "cite")}, open(os.path.join(rep["out"], "whatships.json"), "w"), indent=1)
        item = {"slug": slug, "out": rep["out"], "videos": [v["file"] for v in rep.get("videos", [])]}
        if "--study" in a:
            for vf in item["videos"]:
                sp = subprocess.run([os.environ.get("PY", sys.executable), os.path.join(HERE, "framestudy.py"), vf],
                                    capture_output=True, text=True)
                try: item.setdefault("study", []).append(json.loads(sp.stdout.strip().splitlines()[-1]))
                except Exception: item.setdefault("study", []).append({"error": (sp.stderr or sp.stdout)[-400:]})
        res.append(item)
    return res


def main():
    a = sys.argv[1:]
    KNOWN = {"--from", "--force", "--cat", "--since", "--days", "--until", "--author", "--min-views", "--sort", "--limit",
             "--json", "--cols", "--out", "--study", "--no-video", "--sheet-fps", "-h", "--help"}
    bad = [x for x in a if x.startswith("-") and x not in KNOWN]
    if bad: sys.exit(f"unknown option(s): {' '.join(bad)} (see --help; category filter is --cat)")
    if not a or a[0] in ("-h", "--help"): print(__doc__); return
    cmd, a = a[0], a[1:]
    if cmd == "sync":
        print(json.dumps(sync(opt(a, "--from"), force=True), indent=1))
    elif cmd == "find":
        r = find(a)
        if "--json" in a: print(json.dumps(r, indent=1, ensure_ascii=False))
        else: print("\n".join(row(x) for x in r) or "(no matches)"); print(f"-- {len(r)} shown · cache {p('meta.json')}")
    elif cmd == "show":
        x = show(positional(a)[0]); print(json.dumps(x, indent=1, ensure_ascii=False) if x else "(unknown slug)")
    elif cmd == "cats":
        from collections import defaultdict
        c = defaultdict(lambda: [0, ""])
        for x in load():
            if x.get("status", "published") != "published": continue
            e = c[x.get("category") or "?"]; e[0] += 1; e[1] = max(e[1], (x.get("publishedAt") or "")[:10])
        for k, (n, d) in sorted(c.items(), key=lambda kv: -kv[1][0]): print(f"{k:<16} {n:>5}  newest {d}")
    elif cmd in ("tools", "studios"):
        q = " ".join(positional(a)).lower()
        for x in load(f"{cmd}.json"):
            if q in json.dumps(x).lower(): print(f"{x.get('name'):<24} {x.get('category') or x.get('kind') or '':<10} {x.get('url')}  — {x.get('tagline')}")
    elif cmd == "wall":
        print(json.dumps(wall(a), indent=1))
    elif cmd == "fetch":
        print(json.dumps(fetch(a), indent=1, ensure_ascii=False))
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
