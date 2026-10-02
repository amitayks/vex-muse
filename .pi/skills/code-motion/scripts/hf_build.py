#!/usr/bin/env python3
"""hf_build.py — build a HyperFrames project's index.html from a source file kept OUTSIDE the project.

  python3 hf_build.py SRC.html PROJECT_DIR

Why a build step:
  * On this box Chrome's URL font loader fails (NetworkError even for data: URIs), so text in @font-face
    families renders invisible. FontFace(ArrayBuffer) always works. Every `@font-face { font-family:"X";
    [font-style:Y;] src:url("assets/fonts/F"); }` in SRC keeps its rule (lint + other hosts) and gains a
    synchronous inline script that registers the same family from bytes before any timeline code runs.
  * HyperFrames Studio/preview writes data-hf-id attributes into project HTML and lint rejects two root
    compositions in one dir — so the editable source lives outside PROJECT_DIR (e.g. <project>-src/).
Paths in @font-face src are relative to PROJECT_DIR. Prints the families registered.
"""
import base64, os, re, sys

if len(sys.argv) != 3:
    print(__doc__); sys.exit(1)
src_path, proj = sys.argv[1], sys.argv[2]
src = re.sub(r' data-hf-id="[^"]*"', "", open(src_path).read())
faces = re.findall(r'@font-face\s*{\s*font-family:\s*"([^"]+)";\s*(?:font-style:\s*(\w+);\s*)?(?:font-weight:\s*(\w+);\s*)?src:\s*url\("([^"]+)"\)', src)
if not faces:
    print("warning: no @font-face rules found — generic families render NOTHING on this box (no system fonts)")
js = ["<script>/* hf_build: font bytes -> FontFace (sync, bypasses the URL loader) */(function(){var F=["]
for fam, style, weight, path in faces:
    fp = os.path.join(proj, path)
    if not os.path.exists(fp): sys.exit(f"missing font file {fp}")
    js.append(f'["{fam}","{style or "normal"}","{weight or "normal"}","{base64.b64encode(open(fp, "rb").read()).decode()}"],')
js.append("];F.forEach(function(f){var s=atob(f[3]),u=new Uint8Array(s.length);for(var i=0;i<s.length;i++)u[i]=s.charCodeAt(i);"
          "var ff=new FontFace(f[0],u.buffer,{style:f[1],weight:f[2]});document.fonts.add(ff);ff.load();});})();</script>")
if "<body>" not in src: sys.exit("SRC has no <body> tag")
out = src.replace("<body>", "<body>\n" + "".join(js), 1)
open(os.path.join(proj, "index.html"), "w").write(out)
print("built", os.path.join(proj, "index.html"), "fonts:", [f[0] for f in faces])
