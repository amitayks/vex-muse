#!/usr/bin/env python3
"""Build hf/index.html from index.src.html.
Fonts: on this box Chrome's URL font loader fails (NetworkError even for data: URIs), while
FontFace(ArrayBuffer) always works. So each @font-face keeps its relative src (lint + other hosts) and a
synchronous inline script registers the same family from bytes before any timeline code runs."""
import base64, re, os
HERE = os.path.dirname(os.path.abspath(__file__)); HF = os.path.join(HERE, "..", "hf")
src = open(os.path.join(HERE, "index.src.html")).read()
faces = re.findall(r'@font-face\s*{\s*font-family:\s*"([^"]+)";\s*(?:font-style:\s*(\w+);\s*)?src:\s*url\("([^"]+)"\);\s*}', src)
js = ["<script>/* font bytes -> FontFace (sync, no URL loader) */(function(){var F=["]
for fam, style, path in faces:
    b64 = base64.b64encode(open(os.path.join(HF, path), "rb").read()).decode()
    js.append(f'["{fam}","{style or "normal"}","{b64}"],')
js.append("];F.forEach(function(f){var s=atob(f[2]),u=new Uint8Array(s.length);for(var i=0;i<s.length;i++)u[i]=s.charCodeAt(i);"
          "var ff=new FontFace(f[0],u.buffer,{style:f[1]});document.fonts.add(ff);ff.load();});})();</script>")
out = src.replace("<body>", "<body>\n" + "".join(js), 1)
open(os.path.join(HF, "index.html"), "w").write(out); print("fonts via buffer:", [f[0] for f in faces])
