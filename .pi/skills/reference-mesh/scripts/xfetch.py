#!/usr/bin/env python3
"""xfetch.py — pull an X post (text, author, stats, quoted post, images, videos) without the paid X API.

  xfetch.py <x.com or twitter.com status URL> [--out DIR] [--sheet-fps 2] [--no-video]

Uses the public fxtwitter JSON mirror (api.fxtwitter.com, no auth). Writes to DIR (default
research/x/<author>-<id>/): post.json, post.md (readable), images, video.mp4 (best-bitrate variant),
video_audio.mp3, and contact_*.jpg sheets (frames at --sheet-fps, 24 per sheet, labeled with time)
so a video can be "watched" by reading the sheets in order. Needs ffmpeg on PATH (tools/env.sh).
Replies/threads: fetch each status URL; the quoted post is included automatically.
"""
import json, os, re, sys, subprocess, urllib.request, glob

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        b = r.read(); return b if raw else json.loads(b)

def best_video(v):
    vs = [x for x in (v.get("variants") or []) if (x.get("content_type") or "video/mp4") == "video/mp4" and x.get("url")]
    return max(vs, key=lambda x: x.get("bitrate") or 0)["url"] if vs else v.get("url")

def sheets(video, out, fps):
    """Tile frames 6x4 per sheet in one ffmpeg pass; sheet k covers seconds [(k-1)*24/fps, k*24/fps)."""
    os.makedirs(out, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},scale=320:-2,tile=6x4",
                    os.path.join(out, "contact_%02d.jpg")], check=True)
    n = len(glob.glob(os.path.join(out, "contact_*.jpg")))
    open(os.path.join(out, "README.txt"), "w").write(f"{n} sheets, 24 frames each at {fps} fps, left-to-right, top-to-bottom. Sheet k starts at {24 / fps:g}*(k-1) s.\n")
    return n

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    m = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", a[0])
    if not m: print(json.dumps({"error": "not a status URL"})); sys.exit(1)
    user, sid = m.groups()
    t = get(f"https://api.fxtwitter.com/{user}/status/{sid}").get("tweet")
    if not t: print(json.dumps({"error": "post not found or protected"})); sys.exit(1)
    out = opt("--out", os.path.join("research", "x", f"{t['author']['screen_name']}-{sid}")); os.makedirs(out, exist_ok=True)
    json.dump(t, open(os.path.join(out, "post.json"), "w"), indent=1, ensure_ascii=False)
    media = t.get("media") or {}; files = []
    for i, p in enumerate(media.get("photos") or []):
        f = os.path.join(out, f"image_{i + 1}.jpg"); open(f, "wb").write(get(p["url"], raw=True)); files.append(f)
    vids = media.get("videos") or []
    report = {"author": t["author"]["screen_name"], "text": t.get("text"), "likes": t.get("likes"), "reposts": t.get("retweets"),
              "views": t.get("views"), "created": t.get("created_at"), "quote": (t.get("quote") or {}).get("url"), "images": files, "videos": []}
    if vids and "--no-video" not in a:
        for i, v in enumerate(vids):
            f = os.path.join(out, f"video_{i + 1}.mp4"); open(f, "wb").write(get(best_video(v), raw=True))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", f.replace(".mp4", "_audio.mp3")], check=False)
            ns = sheets(f, os.path.join(out, f"video_{i + 1}_sheets"), float(opt("--sheet-fps", 2)))
            report["videos"].append({"file": f, "duration": v.get("duration"), "size": [v.get("width"), v.get("height")], "sheets": ns})
    md = f"# @{report['author']} — {report['created']}\n\n{report['text']}\n\nlikes {report['likes']} · reposts {report['reposts']} · views {report['views']}\n"
    if t.get("quote"): md += f"\n> quoting @{t['quote']['author']['screen_name']}: {t['quote'].get('text')}\n"
    open(os.path.join(out, "post.md"), "w").write(md)
    print(json.dumps(report | {"out": out}, ensure_ascii=False))

if __name__ == "__main__":
    main()
