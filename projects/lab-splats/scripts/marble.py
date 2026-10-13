#!/usr/bin/env python3
"""marble.py - World Labs Marble (World API) client for Muse. Stdlib only. Key: env WLT_API_KEY (never printed).

  python3 marble.py credits
  python3 marble.py gen --name lane --model marble-1.1-plus (--text "..." | --image a.png | --pano p.png |
        --images a.png:0,b.png:180 | --video v.mp4) [--prompt "..."] [--seed 7] --out DIR --ledger L.jsonl --tag T
  python3 marble.py export --world <id> [--res full_res] --out DIR      # free PLY export -> ply_url in DIR/world.json
  python3 marble.py get --world <id> --out DIR

gen writes DIR/world.json (assets, semantics_metadata, cost) and downloads the pano, thumbnail, collider GLB and the
full-res SPZ into DIR. The PLY is exported (free) and only its URL is kept: fetch it straight into the Modal volume
with modal_splat.py::url (PLY ~0.5 GB, keep it off /data). Cost: 1,250 credits = $1.
"""
import argparse, base64, json, os, pathlib, sys, time, urllib.request, urllib.error

API = "https://api.worldlabs.ai/marble/v1"
USD_PER_CREDIT = 1 / 1250

def req(method, path, body=None, timeout=120):
    key = os.environ.get("WLT_API_KEY")
    if not key: sys.exit("WLT_API_KEY missing")
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"WLT-Api-Key": key, "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(r, timeout=timeout) as f:
                return json.loads(f.read() or b"{}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:800]
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(5 * (attempt + 1)); continue
            sys.exit(f"HTTP {e.code} {method} {path}: {msg}")
        except urllib.error.URLError as e:
            if attempt < 4: time.sleep(5); continue
            raise

def b64ref(path):
    p = pathlib.Path(path)
    return {"source": "data_base64", "data_base64": base64.b64encode(p.read_bytes()).decode(), "extension": p.suffix.lstrip(".").lower()}

def upload(path, kind):
    p = pathlib.Path(path); ext = p.suffix.lstrip(".").lower()
    prep = req("POST", "/media-assets:prepare_upload", {"file_name": p.name, "kind": kind, "extension": ext})
    ui = prep["upload_info"]
    r = urllib.request.Request(ui["upload_url"], data=p.read_bytes(), method=ui.get("upload_method", "PUT"),
                               headers=ui.get("required_headers") or {})
    urllib.request.urlopen(r, timeout=600).read()
    return {"source": "media_asset", "media_asset_id": prep["media_asset"].get("media_asset_id") or prep["media_asset"].get("id")}

def poll(op_id, every=10, limit=3600):
    t0 = time.time()
    while True:
        op = req("GET", f"/operations/{op_id}")
        if op.get("done"):
            return op
        if time.time() - t0 > limit: sys.exit(f"timeout on operation {op_id}")
        st = ((op.get("metadata") or {}).get("progress") or {}).get("status")
        print(f"  .. {int(time.time() - t0)}s {st}", file=sys.stderr, flush=True)
        time.sleep(every)

def fetch(url, dest):
    with urllib.request.urlopen(url, timeout=600) as f, open(dest, "wb") as g:
        while True:
            b = f.read(1 << 20)
            if not b: break
            g.write(b)
    return os.path.getsize(dest)

def save_world(world, out: pathlib.Path, download=True):
    out.mkdir(parents=True, exist_ok=True)
    a = world.get("assets") or {}
    got = {}
    if download:
        for name, url in [("pano.png", (a.get("imagery") or {}).get("pano_url")),
                          ("thumb.jpg", a.get("thumbnail_url")),
                          ("collider.glb", (a.get("mesh") or {}).get("collider_mesh_url")),
                          ("world_full.spz", ((a.get("splats") or {}).get("spz_urls") or {}).get("full_res")),
                          ("world_500k.spz", ((a.get("splats") or {}).get("spz_urls") or {}).get("500k"))]:
            if url:
                try: got[name] = fetch(url, out / name)
                except Exception as e: got[name] = f"ERR {e!r}"
    return got

def ledger_row(ledger, tag, model, credits, extra):
    if not ledger: return
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "endpoint": f"worldlabs/{model}", "tag": tag,
           "credits": credits, "est_usd": round((credits or 0) * USD_PER_CREDIT, 4), **extra}
    with open(ledger, "a") as f: f.write(json.dumps(row) + "\n")

def export_ply(world_id, res="full_res"):
    op = req("POST", f"/worlds/{world_id}:export", {"asset_type": "splats", "format": "ply", "resolution": res}, timeout=600)
    if not op.get("done"): op = poll(op["operation_id"], every=5)
    return op

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("credits")
    g = sub.add_parser("gen")
    g.add_argument("--name", required=True); g.add_argument("--model", default="marble-1.1-plus")
    g.add_argument("--text"); g.add_argument("--image"); g.add_argument("--pano"); g.add_argument("--images"); g.add_argument("--video")
    g.add_argument("--prompt", help="text prompt to go with an image/pano/video input"); g.add_argument("--seed", type=int)
    g.add_argument("--out", required=True); g.add_argument("--ledger"); g.add_argument("--tag", default="")
    g.add_argument("--no-ply", action="store_true")
    rs = sub.add_parser("resume"); rs.add_argument("--op", required=True); rs.add_argument("--name", required=True)
    rs.add_argument("--model", default="marble-1.1-plus"); rs.add_argument("--out", required=True); rs.add_argument("--ledger"); rs.add_argument("--tag", default="")
    e = sub.add_parser("export"); e.add_argument("--world", required=True); e.add_argument("--res", default="full_res"); e.add_argument("--out", required=True)
    gg = sub.add_parser("get"); gg.add_argument("--world", required=True); gg.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.cmd == "resume":
        op = poll(a.op, every=5); finish(op, a.name, a.model, "image", a.out, a.ledger, a.tag, time.time()); return
    if a.cmd == "credits":
        print(json.dumps(req("GET", "/credits"))); return
    if a.cmd == "get":
        w = req("GET", f"/worlds/{a.world}"); w = w.get("world", w)
        out = pathlib.Path(a.out); got = save_world(w, out)
        (out / "world.json").write_text(json.dumps(w, indent=1)); print(json.dumps({"downloaded": got})); return
    if a.cmd == "export":
        op = export_ply(a.world, a.res); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / f"export_{a.res}.json").write_text(json.dumps(op, indent=1)); print(json.dumps(op.get("response"), indent=1)); return

    # gen
    wp = None
    if a.text: wp = {"type": "text", "text_prompt": a.text}
    elif a.image: wp = {"type": "image", "image_prompt": upload(a.image, "image"), "is_pano": False}
    elif a.pano: wp = {"type": "image", "image_prompt": upload(a.pano, "image"), "is_pano": True}
    elif a.images:
        items = []
        for spec in a.images.split(","):
            path, az = spec.rsplit(":", 1); items.append({"azimuth": float(az), "content": upload(path, "image")})
        wp = {"type": "multi-image", "multi_image_prompt": items}
    elif a.video: wp = {"type": "video", "video_prompt": upload(a.video, "video")}
    else: sys.exit("one input is required")
    if a.prompt and wp["type"] != "text": wp["text_prompt"] = a.prompt
    body = {"display_name": a.name, "model": a.model, "world_prompt": wp, "permission": {"public": False}}
    if a.seed is not None: body["seed"] = a.seed
    t0 = time.time()
    op = req("POST", "/worlds:generate", body)
    print(f"operation {op['operation_id']}", file=sys.stderr, flush=True)
    op = poll(op["operation_id"])
    finish(op, a.name, a.model, wp["type"], a.out, a.ledger, a.tag, t0, a.no_ply)

def finish(op, name, model, input_type, out_dir, ledger, tag, t0, no_ply=False):
    if op.get("error"): sys.exit(f"generation failed: {op['error']}")
    world = op["response"] or {}
    wid = world.get("world_id") or world.get("id") or (op.get("metadata") or {}).get("world_id")
    full = req("GET", f"/worlds/{wid}"); full = full.get("world", full)
    if full and full.get("assets"): world = full
    out = pathlib.Path(out_dir); got = save_world(world, out)
    credits = (op.get("cost") or {}).get("total_credits")
    rec = {"name": name, "world_id": wid, "model": model, "input": input_type, "wall_s": round(time.time() - t0, 1),
           "cost": op.get("cost"), "world": world, "downloaded": got}
    a = argparse.Namespace(no_ply=no_ply, ledger=ledger, tag=tag, name=name, model=model)
    if not a.no_ply:
        ex = export_ply(wid)
        rec["ply_export"] = ex.get("response"); rec["ply_url"] = (ex.get("response") or {}).get("url") or (ex.get("response") or {}).get("ply_url")
    (out / "world.json").write_text(json.dumps(rec, indent=1))
    ledger_row(a.ledger, a.tag or a.name, a.model, credits, {"world_id": wid, "wall_s": rec["wall_s"]})
    print(json.dumps({k: rec[k] for k in ("name", "world_id", "wall_s", "cost", "downloaded")} | {"ply_url": rec.get("ply_url"),
                      "semantics": ((world.get("assets") or {}).get("splats") or {}).get("semantics_metadata")}, indent=1))

if __name__ == "__main__":
    main()
