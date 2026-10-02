#!/usr/bin/env python3
"""trim_logo.py — make the document logo from the OFFICIAL Shift files: no white background, framed at its own borders.

usage:  python3 trim_logo.py OFFICIAL_DIR OUT_DIR
        OFFICIAL_DIR holds the untouched shift-labs-ai/assets avatars/svg/*.svg (original.svg + 15 colourways)

For each file it (1) removes ONLY the white 512x512 background <rect>, (2) keeps the <g transform> and every
<path> byte for byte, (3) sets viewBox/width/height to the exact outer border of the keycap (the lip), computed
from the path geometry (cubic extrema, stroke allowance) and rounded outward to 0.01 — so nothing of the logo is
cut and nothing else is left. Writes OUT_DIR/<name>.svg and prints a JSON report with SHA-256 of source and output.
Refuses any file whose structure differs from the official template. Stdlib only.
"""
import hashlib, json, math, os, re, sys

NUM = re.compile(r'-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?', re.I)


def die(msg):
    sys.stderr.write('trim_logo.py: ' + msg + '\n')
    sys.exit(1)


def cubic_extrema(p0, p1, p2, p3):
    """t in (0,1) where the derivative of one coordinate of a cubic Bezier is 0."""
    a = -p0 + 3 * p1 - 3 * p2 + p3
    b = 2 * (p0 - 2 * p1 + p2)
    c = p1 - p0
    ts = []
    if abs(a) < 1e-12:
        if abs(b) > 1e-12:
            ts.append(-c / b)
    else:
        d = b * b - 4 * a * c
        if d >= 0:
            r = math.sqrt(d)
            ts += [(-b + r) / (2 * a), (-b - r) / (2 * a)]
    return [t for t in ts if 0 < t < 1]


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3


def path_bbox(d):
    """Exact bbox of an SVG path using M/m L/l H/h V/v C/c Z/z."""
    toks = re.findall(r'[MmLlHhVvCcZz]|' + NUM.pattern, d)
    i, cmd, x, y, sx, sy = 0, None, 0.0, 0.0, 0.0, 0.0
    xs, ys = [], []

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v
    while i < len(toks):
        t = toks[i]
        if re.fullmatch(r'[A-Za-z]', t):
            cmd = t; i += 1
            if cmd in 'Zz':
                x, y = sx, sy
                continue
        elif cmd is None:
            die('path starts without a command')
        rel = cmd.islower()
        C = cmd.upper()
        if C == 'M':
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            sx, sy = x, y
            xs.append(x); ys.append(y)
            cmd = 'l' if rel else 'L'   # implicit lineto after moveto
        elif C == 'L':
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            xs.append(x); ys.append(y)
        elif C == 'H':
            nx = num(); x = x + nx if rel else nx; xs.append(x); ys.append(y)
        elif C == 'V':
            ny = num(); y = y + ny if rel else ny; xs.append(x); ys.append(y)
        elif C == 'C':
            v = [num() for _ in range(6)]
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y, v[4] + x, v[5] + y]
            px = (x, v[0], v[2], v[4]); py = (y, v[1], v[3], v[5])
            xs += [x, v[4]] + [bez(*px, t) for t in cubic_extrema(*px)]
            ys += [y, v[5]] + [bez(*py, t) for t in cubic_extrema(*py)]
            x, y = v[4], v[5]
        else:
            die('unsupported path command ' + cmd)
    return min(xs), min(ys), max(xs), max(ys)


TEMPLATE = re.compile(
    r'^<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">\n'
    r'  <rect width="512" height="512" fill="#FFFFFF"/>\n'
    r'  <g transform="translate\(([\d.]+), ([\d.]+)\) scale\(([\d.]+)\)">\n'
    r'((?:    <path [^\n]*/>\n)+)'
    r'  </g>\n</svg>\n?$')


def trim(src):
    m = TEMPLATE.match(src)
    if not m:
        die('not the official avatar template (white rect + one scaled <g> of paths)')
    tx, ty, sc = float(m.group(1)), float(m.group(2)), float(m.group(3))
    paths = m.group(4)
    x0 = y0 = math.inf
    x1 = y1 = -math.inf
    for p in re.findall(r'<path [^\n]*/>', paths):
        a, b, c, d = path_bbox(re.search(r' d="([^"]+)"', p).group(1))
        sw = re.search(r'stroke-width="([\d.]+)"', p)
        if sw and 'stroke=' in p:   # stroke reaches past the fill; allow the full miter
            lim = float((re.search(r'stroke-miterlimit="([\d.]+)"', p) or [0, 4])[1])
            k = float(sw.group(1)) / 2 * lim
            a, b, c, d = a - k, b - k, c + k, d + k
        x0, y0, x1, y1 = min(x0, a), min(y0, b), max(x1, c), max(y1, d)
    X0, Y0 = math.floor((tx + sc * x0) * 100) / 100, math.floor((ty + sc * y0) * 100) / 100
    X1, Y1 = math.ceil((tx + sc * x1) * 100) / 100, math.ceil((ty + sc * y1) * 100) / 100
    W, H = round(X1 - X0, 2), round(Y1 - Y0, 2)
    f = lambda v: ('%.2f' % v).rstrip('0').rstrip('.')
    out = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="%s %s %s %s">\n' % (f(W), f(H), f(X0), f(Y0), f(W), f(H)) +
           '  <g transform="translate(%s, %s) scale(%s)">\n' % (m.group(1), m.group(2), m.group(3)) + paths + '  </g>\n</svg>\n')
    assert paths in out and '<rect' not in out
    return out, {'viewBox': [X0, Y0, W, H], 'removed_margins_512': {'left': X0, 'top': Y0, 'right': round(512 - X1, 2), 'bottom': round(512 - Y1, 2)}}


def main():
    if len(sys.argv) != 3:
        die(__doc__)
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for fn in sorted(os.listdir(src_dir)):
        if not fn.endswith('.svg'):
            continue
        raw = open(os.path.join(src_dir, fn), 'rb').read()
        out, info = trim(raw.decode('utf-8'))
        with open(os.path.join(out_dir, fn), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(out)
        info.update(source_sha256=hashlib.sha256(raw).hexdigest(), sha256=hashlib.sha256(out.encode()).hexdigest())
        report[fn[:-4]] = info
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
