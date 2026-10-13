#!/usr/bin/env python3
"""push_binary.py <local> <remote> [...pairs] - PUT binary files into the server (head) workspace (Vex files API),
GET them back and compare sha256. Text files go through the workspaces.writeFile RPC instead (execute_actions)."""
import hashlib, json, os, sys, urllib.parse, urllib.request

cfg = json.load(open(os.path.expanduser("~/.vex/ws/muse/state/mac-node/config.json")))["server"]
base, ws = cfg["url"], cfg["headWorkspaceId"]
creds = json.load(open(os.path.expanduser("~/.vex/credentials.json")))
tok = creds.get(base) or creds.get(base.rstrip("/"))
url = lambda p: f"{base}/api/workspaces/{ws}/files/content?path={urllib.parse.quote(p)}"
out = []
args = sys.argv[1:]
for local, remote in zip(args[0::2], args[1::2]):
    data = open(local, "rb").read()
    req = urllib.request.Request(url(remote), data=data, method="PUT",
                                 headers={"Authorization": "Bearer " + tok, "content-type": "application/octet-stream"})
    st = urllib.request.urlopen(req, timeout=600).status
    back = urllib.request.urlopen(urllib.request.Request(url(remote), headers={"Authorization": "Bearer " + tok}), timeout=600).read()
    a, b = hashlib.sha256(data).hexdigest(), hashlib.sha256(back).hexdigest()
    out.append({"remote": remote, "bytes": len(data), "put": st, "sha256": a, "readback_ok": a == b})
print(json.dumps(out, indent=1))
