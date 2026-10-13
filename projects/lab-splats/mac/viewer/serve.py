#!/usr/bin/env python3
"""serve.py - local server for the Muse splat viewer. Stdlib only.

  python3 serve.py [--port 8765] [--vol ~/muse-splats/vol]
  open "http://127.0.0.1:8765/?file=runs/garden-brush1/ply/garden_brush1_30000.ply&cams=runs/garden-brush1/cameras.json"
  open "http://127.0.0.1:8765/?shot=shots/garden_orbit.json"

/        -> this folder (index.html, viewer.js, shotcam.js, vendor/)
/vol/... -> the local mirror of Modal volume muse-splats (runs/, worlds/, shots/)
Binds 127.0.0.1 only. Sends no-store so edited shots reload.
"""
import argparse, functools, http.server, os, pathlib

HERE = pathlib.Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
                      ".ply": "application/octet-stream", ".spz": "application/octet-stream", ".wasm": "application/wasm"}

    def __init__(self, *a, vol=None, **k):
        self.vol = vol
        super().__init__(*a, directory=str(HERE), **k)

    def translate_path(self, path):
        p = path.split("?", 1)[0].split("#", 1)[0]
        if p.startswith("/vol/"):
            rel = pathlib.PurePosixPath(p[5:])
            if ".." in rel.parts:
                return str(HERE / "__forbidden__")
            return str(pathlib.Path(self.vol) / rel)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):  # skip socket.getfqdn(): it can hang for a long time on macOS
        import socketserver
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--vol", default=os.environ.get("MUSE_SPLAT_VOL", str(HERE.parent / "vol")))
    a = ap.parse_args()
    vol = os.path.expanduser(a.vol)
    srv = Server(("127.0.0.1", a.port), functools.partial(Handler, vol=vol))
    print(f"viewer: http://127.0.0.1:{a.port}/   vol: {vol}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
