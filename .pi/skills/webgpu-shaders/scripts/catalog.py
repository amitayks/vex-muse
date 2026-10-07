#!/usr/bin/env python3
"""catalog.py — the Shaders component reference, filtered for frame-exact video work.

  catalog.py list [category]     component names per category, with flags
  catalog.py show Name [Name..]  every prop: type, default, range (and requiresChild)
  catalog.py materials           the shape-effect materials (take a `shape` prop)
  catalog.py safe                every component that is safe for a parallel / random-seek render
  catalog.py refresh             re-download the reference

Source: https://shaders.com/llms-full.txt (all components, props, defaults, ranges), cached at
~/.cache/shaders/llms-full.txt. The doc tracks the latest npm release: after an upgrade, `refresh`.
Flags: CHILD = filter, needs children · SIM = state carries frame to frame (never in a parallel or
random-seek render) · NET = loads web fonts over the network (never in a render) · INPUT = needs a
pointer, webcam or video (untested) · data:url = works only with a data: URL.
"""
import os, re, sys, urllib.request

URL = 'https://shaders.com/llms-full.txt'
CACHE = os.path.expanduser('~/.cache/shaders/llms-full.txt')
SIM = {'Particles', 'SmokeFill', 'ReactionDiffusion', 'TimeTrail', 'DataMosh', 'Smoke', 'SmokeFlow', 'InkFlow',
       'FlowField', 'Boids', 'ParticleFlow', 'Liquify', 'Shatter', 'PixelThrow', 'PixelSort', 'MagneticFilings',
       'ChromaFlow', 'GridDistortion', 'Fog'}
NET = {'Text', 'Ascii'}
INPUT = {'CursorTrail', 'CursorRipples', 'WebcamTexture', 'VideoTexture', 'HTMLInCanvas', 'ObjectTracker'}
DATA_URL = {'ImageTexture'}  # usable: give it a data: URL (fetch cannot read file://)


def load(refresh=False):
    if refresh or not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        urllib.request.urlretrieve(URL, CACHE)
    return open(CACHE, encoding='utf-8').read()


def parse(text):
    comps, cat = {}, None
    for block in re.split(r'\n(?=## |### )', text):
        head = block.split('\n', 1)[0]
        if head.startswith('## Category: '):
            cat = head[len('## Category: '):].strip()
        elif head.startswith('### ') and cat:
            name = head[4:].strip()
            if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', name):
                continue  # the doc's worked examples share the heading level
            props = re.findall(r'- `(\w+)` \(([^)]*)\) - Default: `([^`]*)`(?: - Range: ([^\n]*))?', block)
            comps[name] = {'cat': cat, 'child': 'Requires Child**: Yes' in block, 'props': props}
    return comps


def flags(name, c):
    f = []
    if c['child']: f.append('CHILD')
    if name in SIM: f.append('SIM')
    if name in NET: f.append('NET')
    if name in INPUT: f.append('INPUT')
    if name in DATA_URL: f.append('data:url')
    if any(p[0] == 'shape' for p in c['props']): f.append('shape')
    return ','.join(f)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    text = load(refresh=(cmd == 'refresh'))
    comps = parse(text)
    stamp = re.search(r'Last updated: (\S+)', text)
    if cmd == 'refresh':
        print(f'{len(comps)} components, doc updated {stamp.group(1) if stamp else "?"}'); return
    if cmd == 'list':
        want = sys.argv[2].lower() if len(sys.argv) > 2 else None
        cats = {}
        for n, c in comps.items(): cats.setdefault(c['cat'], []).append(n)
        for cat, names in cats.items():
            if want and want not in cat.lower(): continue
            print(f'## {cat} ({len(names)})')
            print('  ' + '  '.join(n + (f'[{flags(n, comps[n])}]' if flags(n, comps[n]) else '') for n in names))
    elif cmd == 'show':
        for n in sys.argv[2:]:
            c = comps.get(n)
            if not c: print(f'?? {n}: not in the reference (case-sensitive)'); continue
            print(f'### {n}  ({c["cat"]}) {flags(n, c)}')
            for p, kind, d, rng in c['props']:
                print(f'  {p:22s} {kind:16s} default {d[:60]}' + (f'  [{rng.strip()}]' if rng else ''))
    elif cmd == 'materials':
        for n, c in comps.items():
            if any(p[0] == 'shape' for p in c['props']) and c['cat'] == 'Shape Effects':
                print(f'{n:14s} {flags(n, c)}')
    elif cmd == 'safe':
        print(' '.join(n for n in comps if n not in SIM | NET | INPUT))
    else:
        print(__doc__); sys.exit(2)


if __name__ == '__main__':
    main()
