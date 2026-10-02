#!/usr/bin/env python3
"""Port of projects/lab-motion-tools/tesseract-src/turn.src.html to a Tesseract (.tsrct) project.
Same 4D math, same beat timing, same palette; every frame is scripted per property (layerTimeJsCode).
Writes .w/actions.json (layers, top -> bottom) given measured caption widths."""
import json, sys
from PIL import ImageFont

FONTS = "/tmp/tsrct-lab/fonts/Unbounded-{}.ttf"
FACE = {"Medium": ("Unbounded Medium", "Regular"), "SemiBold": ("Unbounded SemiBold", "Regular"), "Bold": ("Unbounded", "Bold")}
DUR = 8.1; B = 60 / 128; at = lambda bar, beat=0: (bar * 4 + beat) * B
MS = lambda s: int(round(s * 1000))
T0 = {"anchorPoint": [0, 0], "position": [0, 0], "scale": [100, 100], "rotation": 0, "opacity": 100}
INK = [0x1C / 255, 0x1D / 255, 0x1A / 255, 1]; PINK = [1, 0x48 / 255, 0xB0 / 255, 1]; PAPER = [0xCD / 255, 0xD1 / 255, 0xC4 / 255, 1]

PRE = r"""
const B=60/128, DUR=8.1, t=input.time.seconds;
const at=(bar,beat)=>(bar*4+(beat||0))*B, clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>{x=clamp(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;};
const easeOut=x=>1-Math.pow(1-clamp(x),3);
"""
POSE = r"""
const V=[];for(let k=0;k<16;k++)V.push([0,1,2,3].map(b=>(k>>b)&1?1:-1));
const turns=[[1,[[0,3]]],[2,[[1,3]]],[3,[[0,1],[2,3]]]];
const rots=[];let act=null,prog=0;
for(const tr of turns){const p=ease((t-at(tr[0]))/(3*B));if(p>0)tr[1].forEach(q=>rots.push([q[0],q[1],Math.PI*p]));if(t>=at(tr[0])){act=tr[1];prog=p;}}
const rot=(v,i,j,a)=>{const c=Math.cos(a),s=Math.sin(a),o=v.slice();o[i]=c*v[i]-s*v[j];o[j]=s*v[i]+c*v[j];return o;};
const yaw=0.55+0.16*t/DUR,pitch=-0.38,cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
const P=V.map(v=>{let p=v;for(const r of rots)p=rot(p,r[0],r[1],r[2]);const k4=1/(3.5-p[3]);const x=p[0]*k4,y=p[1]*k4,z=p[2]*k4;
 const x2=cy*x+sy*z,z1=-sy*x+cy*z,y2=cp*y-sp*z1,z2=sp*y+cp*z1,f=560*4/(4-z2);return [820+x2*f,480-y2*f,z2,p[3]];});
const grow={inner:easeOut(t/(0.7*B)),outer:easeOut((t-at(0,1))/(0.7*B)),ray:easeOut((t-at(0,2))/(0.7*B))};
const fillIn=easeOut((t-at(0,3))/(0.5*B));
"""

def js(body, pose=False):
    return PRE + (POSE if pose else "") + body

def anim(lid, prop, code):
    return {"type": "setFxPropertyAnimator", "compositionId": "main", "property": {"layerId": lid, "propertyType": prop},
            "animator": {"type": "jsScript", "layerTimeJsCode": code}, "dependencies": []}

def shape(lid, name, start, dur, stroke=None, fill=None, path=None):
    sh = {"path": {"commands": path or [{"type": "moveTo", "x": 0, "y": 0}, {"type": "lineTo", "x": 1, "y": 0}]},
          "strokes": [], "fills": []}
    if stroke: sh["strokes"].append({"paint": {"type": "solid", "color": stroke[0]}, "width": stroke[1], "cap": "round", "join": "round",
                                     "miterLimit": 4, "opacity": 100, "blendMode": "normal", "dashes": []})
    if fill: sh["fills"].append({"paint": {"type": "solid", "color": fill}, "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": 100})
    return {"type": "createFxShapeLayer", "compositionId": "main", "layerId": lid, "name": name,
            "activeRange": {"start": MS(start), "duration": MS(dur)}, "transform": dict(T0), "shape": sh}

def text(lid, name, start, dur, s, style, size, x, y, color, just="left"):
    return {"type": "createFxTextLayer", "compositionId": "main", "layerId": lid, "name": name,
            "activeRange": {"start": MS(start), "duration": MS(dur)},
            "transform": {**T0, "position": [x, y]},
            "sourceText": {"text": s, "fontFamily": FACE[style][0], "fontStyle": FACE[style][1], "fontSize": size, "tracking": -10, "fillColor": color,
                           "justification": just}}

acts, lid = [], [100]
def nid():
    lid[0] += 1; return lid[0]

# ---- captions (topmost): prefix / highlighted word / suffix, measured so the word sits where the browser put it ----
caps = [(0, "a tesseract, seen from its ", "fourth", " direction"), (1, "turn in X–W: the ", "inner", " cube comes outside"),
        (2, "turn in Y–W: back in, by another way", "", ""), (3, "X–Y and Z–W at once: a turn no 3D thing can make", "", "")]
fm = ImageFont.truetype(FONTS.format("Medium"), 34); fb = ImageFont.truetype(FONTS.format("Bold"), 34)
CX, CY = 120, 943                                           # caption baseline (HF: top 910 + ascent)
for bar, pre, word, post in caps:
    start = at(bar); dur = (at(bar + 1) if bar < 3 else DUR) - start
    rise = "const k=easeOut(t/(0.5*B));"
    parts = [(pre, "Medium", CX)]
    if word:
        x1 = CX + fm.getlength(pre) - 0.34 * len(pre); x2 = x1 + fb.getlength(word) - 0.34 * len(word)
        u = nid(); acts.append(shape(u, f"cap{bar} underline", start, dur, fill=PINK,
                   path=[{"type": "moveTo", "x": x1, "y": CY - 2}, {"type": "lineTo", "x": x2, "y": CY - 2},
                         {"type": "lineTo", "x": x2, "y": CY + 8}, {"type": "lineTo", "x": x1, "y": CY + 8}, {"type": "close"}]))
        acts += [anim(u, "opacity", js(rise + "return k;")), anim(u, "positionY", js(rise + "return (1-k)*18;"))]
        parts += [(word, "Bold", x1), (post, "Medium", x2)]
    for s, sty, x in parts:
        i = nid(); acts.append(text(i, f"cap{bar} {s.strip()[:12]}", start, dur, s, sty, 34, x, CY, INK))
        # text opacity is 0-100, shape opacity 0-1 (tsrct 0.2.0)
        acts += [anim(i, "opacity", js(rise + "return 100*k;")), anim(i, "positionY", js(rise + f"return {CY}+(1-k)*18;"))]

# ---- plane indicator: X Y Z W + two arcs (polyline ellipse arcs; the engine has no SVG arc command) ----
planes_in = "return clamp((t-at(0,3))/B);"
axX = [1500, 1590, 1680, 1770]
for name, j in (("arcA", 0), ("arcB", 1)):
    i = nid(); acts.append(shape(i, name, 0, DUR, stroke=(PINK, 6)))
    acts.append(anim(i, "shapePath", js(r"""
const axX=[1500,1590,1680,1770]; const pl=act?act[%d]:null;
if(!pl||prog<=0){const c=[];for(let n=0;n<=40;n++)c.push({type:n?'lineTo':'moveTo',x:-50,y:-50});return {commands:c};}
const x0=axX[pl[0]],x1=axX[pl[1]],r=(x1-x0)/2,cx=x0+r,y=872,N=40,c=[];
for(let n=0;n<=N;n++){const a=Math.PI*clamp(prog)*n/N;c.push({type:n?'lineTo':'moveTo',x:cx-r*Math.cos(a),y:y-r*.8*Math.sin(a)});}
return {commands:c};""" % j, pose=True)))
    acts.append(anim(i, "opacity", js(planes_in)))
for k, L in enumerate("XYZW"):
    i = nid(); acts.append(text(i, f"axis {L}", 0, DUR, L, "SemiBold", 54, axX[k], 930, INK, "center"))
    acts.append(anim(i, "opacity", js("return 100*clamp((t-at(0,3))/B);")))

# ---- 32 edges: path (with bar-1 growth), pen weight = 4D depth, pink when on the tracked cell ----
E = [(a, a ^ (1 << b)) for a in range(16) for b in range(4) if a < a ^ (1 << b)]
for (a, b) in E:
    wa, wb = (a >> 3) & 1, (b >> 3) & 1
    group = "ray" if wa != wb else ("inner" if wa == 0 else "outer")
    tracked = wa == 0 and wb == 0
    i = nid(); acts.append(shape(i, f"edge {a}-{b}", 0, DUR, stroke=(INK, 3)))
    acts.append(anim(i, "shapePath", js(f"""
const g=grow.{group}, A=P[{a}], Bv=P[{b}];
const gg=Math.max(g,0.0001); return {{commands:[{{type:'moveTo',x:A[0],y:A[1]}},{{type:'lineTo',x:A[0]+(Bv[0]-A[0])*gg,y:A[1]+(Bv[1]-A[1])*gg}}]}};""", pose=True)))
    acts.append(anim(i, "strokeWidth", js(f"""
if(grow.{group}<=0) return 0; const w4=(P[{a}][3]+P[{b}][3])/2; return 1.4+1.45*(w4+2)+({'fillIn>0?1.2:0' if tracked else '0'});""", pose=True)))
    if tracked:
        acts.append(anim(i, "strokeColor", js(f"return fillIn>0?[{0xE0/255},{0x25/255},{0x8F/255},1]:[{INK[0]},{INK[1]},{INK[2]},1];", pose=True)))

# ---- tracked cell fill: convex hull of its 8 projected vertices ----
i = nid(); acts.append(shape(i, "cell fill", 0, DUR, fill=PINK))
acts.append(anim(i, "shapePath", js(r"""
const Q=P.slice(0,8).map(p=>[p[0],p[1]]).sort((u,v)=>u[0]-v[0]||u[1]-v[1]);
const cr=(o,u,v)=>(u[0]-o[0])*(v[1]-o[1])-(u[1]-o[1])*(v[0]-o[0]); const lo=[],hi=[];
for(const q of Q){while(lo.length>1&&cr(lo[lo.length-2],lo[lo.length-1],q)<=0)lo.pop();lo.push(q);}
for(const q of Q.slice().reverse()){while(hi.length>1&&cr(hi[hi.length-2],hi[hi.length-1],q)<=0)hi.pop();hi.push(q);}
const h=lo.slice(0,-1).concat(hi.slice(0,-1)); while(h.length<8)h.push(h[h.length-1]); const c=h.map((p,n)=>({type:n?'lineTo':'moveTo',x:p[0],y:p[1]})); c.push({type:'close'});
return {commands:c};""", pose=True)))
acts.append(anim(i, "opacity", js("return 0.42*fillIn;", pose=True)))

# ---- paper ----
i = nid(); acts.append(shape(i, "paper", 0, DUR, fill=PAPER, path=[{"type": "moveTo", "x": 0, "y": 0}, {"type": "lineTo", "x": 1920, "y": 0},
        {"type": "lineTo", "x": 1920, "y": 1080}, {"type": "lineTo", "x": 0, "y": 1080}, {"type": "close"}]))

json.dump(acts, open(".w/actions.json", "w"))
print("actions", len(acts), "layers", sum(1 for x in acts if x["type"].startswith("create")))
