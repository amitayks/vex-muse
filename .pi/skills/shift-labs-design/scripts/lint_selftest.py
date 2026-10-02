#!/usr/bin/env python3
"""lint_selftest.py — prove lint.py still catches what the method forbids.

usage:  python3 lint_selftest.py [WORKDIR]

Builds assets/templates/report.src.html (must lint with 0 errors), then plants one fault at a time
into a copy, builds and lints it, and checks that lint reports the expected message. Run it after
any change to lint.py, the kit or the report template. Exit 1 if the clean report fails or any
planted fault slips through. Stdlib only; WORKDIR defaults to a temp dir (deleted afterwards).
"""
import json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', 'assets', 'templates', 'report.src.html'))

# (name, [(old, new)] applied once each, expected substring in an error — or "W:" prefix for a warning)
FAULTS = [
    ('causal claim, no level', [('<p class="s-note">Keep the two', '<p class="s-p">The rise was driven by new sensors.</p><p class="s-note">Keep the two')], 'causal or attribution claim'),
    ('record claim, no level', [('Every weekday is higher', 'It was a new record week. Every weekday is higher')], 'record claim'),
    ('act while evidence missing', [('data-kind="defer"', 'data-kind="act"')], '"act" decision'),
    ('approve while evidence missing', [('data-kind="reject"', 'data-kind="approve"')], '"approve" decision'),
    ('variance does not reconcile', [('"total":2044', '"total":2050')], 'variance does not reconcile'),
    ('variance change ≠ its data-total', [('data-total="turns-change" data-v="2044"', 'data-total="turns-change" data-v="2050"')], 'variance sums to'),
    ('columns do not reconcile', [('"values":[3817,', '"values":[3815,')], 'columns sums to'),
    ('tablegraph does not reconcile', [('["Sensors",13480,12012]', '["Sensors",13476,12012]')], 'tablegraph sums to'),
    ('heatmap does not reconcile', [('[[46,30,', '[[39,30,')], 'heatmap sums to'),
    ('trust field missing', [('<div data-trust="scope">', '<div data-x="scope">')], 'trust panel (.s-trust) missing: scope'),
    ('KPI without benchmark', [('<small class="s-vs">Matched prior week: <b>21,742</b></small>', '')], 'has no benchmark'),
    ('KPI without contract link', [(' data-metric="empty-share"><b', '><b')], 'has no data-metric'),
    ('contract row incomplete', [('<td>Test workspaces; turns cancelled before start</td>', '<td></td>')], 'metric contract "turns" needs nine cells'),
    ('banned chart type', [('<figure class="s-shape" data-shape="variance">', '<figure class="s-shape" data-shape="donut">')], 'is banned by the method'),
    ('smoothed line', [('"height":84,', '"height":84,"smooth":true,')], 'smoothed lines are banned'),
    ('derived number wrong', [('<span data-calc="(23786-21742)/21742*100">+9.4%</span>', '<span data-calc="(23786-21742)/21742*100">+13.1%</span>')], 'data-calc'),
    ('brief question unanswered', [('<div data-q="missing">', '<div data-x="missing">')], 'brief does not answer: missing'),
    ('ledger row without level', [('<tr data-evidence="suspected">', '<tr>')], 'ledger row'),
    ('unknown evidence level', [('<tr data-evidence="suspected"><td>Longer', '<tr data-evidence="probable"><td>Longer')], 'data-evidence "probable"'),
    ('no decomposition', [('data-shape="variance"', 'data-shape="shares"'), ('data-shape="tablegraph"', 'data-shape="shares"')], 'no decomposition'),
    ('decision field missing', [('<div data-field="owner"><dt>Owner</dt><dd>Infrastructure lead</dd></div>', '')], 'missing fields: owner'),
    ('bullet without target', [('"value":2.9,"target":2.5,', '"value":2.9,')], 'needs a value and a target'),
    ('heatmap wrong shape', [(',[38,23,23,57,132,198,236,246,255,265,236,181]]', ']')], 'heatmap values must be'),
    ('job missing', [(re.compile(r'<!-- job:.*?-->', re.S), '')], 'no <!-- job'),
    ('dead link', [('<span class="s-foot__end">', '<a href="#">More</a><span class="s-foot__end">')], 'dead link'),
    ('drivers section missing', [('data-part="drivers"', 'data-part="x"')], 'data-part="drivers"'),
    ('header badge missing', [('<span class="s-mode"></span>', '')], 'persistent data-mode badge'),
    ('conclusion as chart title', [('<h3 class="s-h3">Agent turns by day</h3>', '<h3 class="s-h3">Agent turns rose on every day</h3>')], 'W:reads like a conclusion'),
    ('single period without prior', [(',{"name":"31 Aug – 6 Sep","role":"prior","values":[3560,3720,3810,3690,3300,1870,1792]}', '')], 'W:without a matched prior'),
]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def lint(work, name, html):
    src = os.path.join(work, name + '.src.html')
    out = os.path.join(work, name + '.html')
    open(src, 'w', encoding='utf-8').write(html)
    b = run([sys.executable, os.path.join(HERE, 'build.py'), src, out])
    if b.returncode:
        return None, b.stderr.strip()
    r = run([sys.executable, os.path.join(HERE, 'lint.py'), out, '--json'])
    return json.loads(r.stdout), ''


def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='sl-selftest-')
    os.makedirs(work, exist_ok=True)
    base = open(SRC, encoding='utf-8').read()
    ok = True
    res, err = lint(work, 'clean', base)
    if res is None or res['errors']:
        print('FAIL clean report: %s' % (err or res['errors']))
        ok = False
    else:
        print('ok   clean report: 0 errors, %d warnings' % len(res['warnings']))
    for name, edits, want in FAULTS:
        html = base
        for old, new in edits:
            if isinstance(old, re.Pattern):
                html, n = old.subn(new, html, count=1)
            else:
                n = html.count(old)
                html = html.replace(old, new, 1)
            if not n:
                print('FAIL %s: fault could not be planted (template changed?)' % name)
                ok = False
                break
        else:
            slug = re.sub(r'\W+', '-', name).strip('-')
            res, err = lint(work, 'fault-' + slug, html)
            pool = res['warnings'] if want.startswith('W:') else (res['errors'] if res else [])
            needle = want[2:] if want.startswith('W:') else want
            hit = [m for m in pool if needle in m]
            print('%s %s → %s' % ('ok  ' if hit else 'FAIL', name, hit[0][:110] if hit else 'not caught'))
            ok = ok and bool(hit)
    if len(sys.argv) < 2:
        shutil.rmtree(work, ignore_errors=True)
    print('PASS' if ok else 'FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
