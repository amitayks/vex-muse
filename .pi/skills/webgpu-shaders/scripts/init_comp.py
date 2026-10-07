#!/usr/bin/env python3
"""init_comp.py — scaffold a HyperFrames comp with a WebGPU (shaders) layer.

  init_comp.py <src_dir> <comp_dir> --font <file.ttf|otf|woff2> --dur <s>
               [--song <song.json> --t0 <s>] [--bpm 120] [--w 1920 --h 1080 --fps 30] [--title T]
               [--gsap <gsap.min.js>] [--force]

Writes <src_dir>/index.src.html (the template; editable source, kept outside the comp dir) and fills
<comp_dir>: hyperframes.json, assets/js/{gsap.min.js, hf-shaders.iife.js, beats.js},
assets/fonts/display.<ext>. beats.js = window.BEATS in comp seconds: the song.json beats in
[t0, t0+dur] shifted by -t0, or a constant --bpm grid. Audio is not touched: put the cut mix at
<comp_dir>/assets/audio/mix.wav (skill track-edit). Then build:
  python3 .pi/skills/code-motion/scripts/hf_build.py <src_dir>/index.src.html <comp_dir>
"""
import argparse, json, os, shutil, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.abspath(os.path.join(SKILL, '../../..'))
GSAP_CANDIDATES = ['projects/lab-motion-tools/node_modules/gsap/dist/gsap.min.js', 'node_modules/gsap/dist/gsap.min.js']
HF_JSON = os.path.join(WS, '.pi/skills/code-motion/assets/reel-template/hyperframes.json')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src_dir'); ap.add_argument('comp_dir')
    ap.add_argument('--font', required=True); ap.add_argument('--dur', type=float, required=True)
    ap.add_argument('--song'); ap.add_argument('--t0', type=float, default=0.0); ap.add_argument('--bpm', type=float, default=120.0)
    ap.add_argument('--w', type=int, default=1920); ap.add_argument('--h', type=int, default=1080); ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--title', default='TITLE'); ap.add_argument('--gsap'); ap.add_argument('--force', action='store_true')
    a = ap.parse_args()

    gsap = a.gsap or next((os.path.join(WS, c) for c in GSAP_CANDIDATES if os.path.exists(os.path.join(WS, c))), None)
    if not gsap or not os.path.exists(gsap):
        sys.exit('gsap.min.js not found: `npm i -D gsap@3.15.0` in the project and pass --gsap <path>')
    if not os.path.exists(a.font):
        sys.exit(f'font not found: {a.font} (no system fonts here: every face must ship with the comp)')
    os.makedirs(a.src_dir, exist_ok=True)
    src = os.path.join(a.src_dir, 'index.src.html')
    if os.path.exists(src) and not a.force:
        sys.exit(f'{src} exists (use --force to overwrite)')

    ext = os.path.splitext(a.font)[1].lower()
    html = open(os.path.join(SKILL, 'assets/template/index.src.html'), encoding='utf-8').read()
    for k, v in {'__W__': a.w, '__H__': a.h, '__DUR__': a.dur, '__FPS__': a.fps, '__TITLE__': a.title}.items():
        html = html.replace(k, str(v))
    html = html.replace('assets/fonts/display.ttf', f'assets/fonts/display{ext}')
    open(src, 'w', encoding='utf-8').write(html)

    for d in ('assets/js', 'assets/fonts', 'assets/audio'):
        os.makedirs(os.path.join(a.comp_dir, d), exist_ok=True)
    shutil.copy(HF_JSON, os.path.join(a.comp_dir, 'hyperframes.json'))
    shutil.copy(gsap, os.path.join(a.comp_dir, 'assets/js/gsap.min.js'))
    shutil.copy(os.path.join(SKILL, 'assets/driver/hf-shaders.iife.js'), os.path.join(a.comp_dir, 'assets/js/hf-shaders.iife.js'))
    shutil.copy(a.font, os.path.join(a.comp_dir, f'assets/fonts/display{ext}'))

    if a.song:
        s = json.load(open(a.song))
        raw = [b['t'] if isinstance(b, dict) else b for b in s['beats']]
        beats = [round(b - a.t0, 4) for b in raw if a.t0 - 1e-3 <= b <= a.t0 + a.dur + 1e-3]
        src_note = f'{os.path.basename(a.song)} beats {a.t0}..{a.t0 + a.dur} s'
    else:
        step = 60.0 / a.bpm
        beats = [round(i * step, 4) for i in range(int(a.dur / step) + 1)]
        src_note = f'constant {a.bpm} BPM grid'
    if not beats:
        sys.exit('no beats in the window: check --t0/--dur against song.json')
    open(os.path.join(a.comp_dir, 'assets/js/beats.js'), 'w').write(
        f'/* {src_note}, in comp seconds */\nwindow.BEATS = {json.dumps(beats)};\n')
    print(json.dumps({'src': src, 'comp': a.comp_dir, 'beats': len(beats), 'first_beats': beats[:4],
                      'next': f'python3 .pi/skills/code-motion/scripts/hf_build.py {src} {a.comp_dir}'}))


if __name__ == '__main__':
    main()
