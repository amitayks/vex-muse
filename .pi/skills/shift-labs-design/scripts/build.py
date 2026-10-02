#!/usr/bin/env python3
"""build.py — turn a Shift Labs source HTML into ONE self-contained .html file.

usage:  python3 build.py SRC.src.html [OUT.html]

Markers the source uses (copy a template from assets/templates/):
  <!-- shift:head -->   inside <head>: fonts (registered from bytes) + kit CSS + the logo as favicon
  <!-- shift:js -->     just before </body>: kit runtime (window.SL)
  <img data-brand="logo" class="s-logo" alt="Shift Labs">
                       → the logo (assets/brand/logo.svg: the official artwork without its white background, framed at
                         its own border by trim_logo.py), byte for byte, as a data URI (hash-checked against PINS.json).
                         Never redrawn, recoloured or re-cropped — an <img> keeps page CSS out of it.
  <img data-brand="avatar-midnight" …>      → an official colourway, trimmed the same way (avatars only)
  src="brand:logo.png"                      → data URI from assets/brand/
  src="img.png" (relative to SRC)            → data URI (the output travels alone)

Fonts: Inter (OFL; the wordmark's face) as "Shift Sans"/"Shift Display", DejaVu Sans Mono as "Shift Mono",
embedded as bytes and registered with FontFace(ArrayBuffer) — works offline, from file://, in print-to-PDF and
in sandboxed headless Chrome where data:/URL font loads fail. Stdlib only. Exit 1 on unresolved marker/asset.
"""
import base64, hashlib, json, mimetypes, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))
KIT_CSS = os.path.join(ASSETS, 'kit', 'shift.css')
KIT_JS = os.path.join(ASSETS, 'kit', 'shift.js')
BRAND = os.path.join(ASSETS, 'brand')
FONTS = os.path.join(ASSETS, 'fonts')
FACES = [  # family, weight, style, file
    ('Shift Sans', 400, 'normal', 'Inter-Regular.woff2'),
    ('Shift Sans', 700, 'normal', 'Inter-Bold.woff2'),
    ('Shift Display', 700, 'normal', 'InterDisplay-Bold.woff2'),
    ('Shift Mono', 400, 'normal', 'DejaVuSansMono.woff2'),
    ('Shift Mono', 700, 'normal', 'DejaVuSansMono-Bold.woff2'),
    ('Shift Mono', 400, 'italic', 'DejaVuSansMono-Oblique.woff2'),
]


def die(msg):
    sys.stderr.write('build.py: ' + msg + '\n')
    sys.exit(1)


def read(p, mode='r'):
    with open(p, mode, **({} if 'b' in mode else {'encoding': 'utf-8'})) as f:
        return f.read()


def fonts_block():
    data = []
    for fam, w, st, fn in FACES:
        p = os.path.join(FONTS, fn)
        if not os.path.exists(p):
            die('missing font ' + p)
        data.append([fam, str(w), st, base64.b64encode(read(p, 'rb')).decode('ascii')])
    js = ('(function(){var F=%s;if(!window.FontFace||!document.fonts)return;F.forEach(function(f){try{'
          'var b=atob(f[3]),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);'
          'var ff=new FontFace(f[0],u.buffer,{weight:f[1],style:f[2]});document.fonts.add(ff);ff.load();}catch(e){}});})();') % json.dumps(data)
    return '<script data-shift-fonts>' + js + '</script>'


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or ('image/svg+xml' if path.endswith('.svg') else 'application/octet-stream')
    return 'data:%s;base64,%s' % (mime, base64.b64encode(read(path, 'rb')).decode('ascii'))


PINS = json.load(open(os.path.join(BRAND, 'PINS.json'), encoding='utf-8'))


def pinned(name):
    """Path + bytes of an official file, refusing anything that is not byte-identical to the original."""
    if name == 'logo':
        p, want = os.path.join(BRAND, 'logo.svg'), PINS['logo.svg']
    elif name.startswith('avatar-') and name[7:] in PINS['avatars']:
        p, want = os.path.join(BRAND, 'avatars', name[7:] + '.svg'), PINS['avatars'][name[7:]]
    else:
        die('unknown brand mark "%s" (logo | avatar-<%s>)' % (name, '|'.join(PINS['avatars'])))
    data = read(p, 'rb')
    if hashlib.sha256(data).hexdigest() != want:
        die('%s does not match PINS.json — regenerate it with scripts/trim_logo.py from assets/brand/official/' % p)
    return data


def logo_img(m):
    tag, name = m.group(0), m.group(1)
    uri = 'data:image/svg+xml;base64,' + base64.b64encode(pinned(name)).decode('ascii')
    svg = pinned(name).decode('utf-8')
    w, h = re.search(r'<svg[^>]*\swidth="([\d.]+)"', svg).group(1), re.search(r'<svg[^>]*\sheight="([\d.]+)"', svg).group(1)
    tag = re.sub(r'\s(src|width|height)="[^"]*"', '', tag)
    if ' alt=' not in tag:
        tag = tag[:4] + ' alt="Shift Labs"' + tag[4:]
    return tag[:4] + ' src="%s" width="%s" height="%s" decoding="sync"' % (uri, w, h) + tag[4:]


def favicon():
    return '<link rel="icon" href="data:image/svg+xml;base64,%s">' % base64.b64encode(pinned('logo')).decode('ascii')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        die(__doc__)
    src = os.path.abspath(args[0])
    out = os.path.abspath(args[1]) if len(args) > 1 else re.sub(r'(\.src)?\.html$', '', src) + '.html'
    if out == src:
        die('OUT would overwrite SRC; name the source *.src.html or pass OUT')
    html = read(src)
    base = os.path.dirname(src)
    for kit in (KIT_CSS, KIT_JS):
        if re.search(r'</(script|style)', read(kit), re.I):
            die('%s contains a literal closing script/style tag — it would end the inlined element early' % kit)
    if '<!-- shift:head -->' not in html or '<!-- shift:js -->' not in html:
        die('source needs both <!-- shift:head --> and <!-- shift:js --> markers')
    head = fonts_block() + '\n<style data-shift-kit>\n' + read(KIT_CSS) + '\n</style>'
    if 'rel="icon"' not in html:
        head = favicon() + '\n' + head
    html = html.replace('<!-- shift:head -->', head, 1)
    html = html.replace('<!-- shift:js -->', '<script data-shift-kit>\n' + read(KIT_JS) + '\n</script>', 1)

    used = []
    if re.search(r'<svg\b[^>]*\bdata-brand=', html):
        die('the logo is never inline SVG — use <img data-brand="logo" class="s-logo" alt="Shift Labs"> (the original file, as it is)')

    def brand(m):
        used.append(m.group(1))
        return logo_img(m)
    html = re.sub(r'<img\b[^>]*?\bdata-brand="([\w-]+)"[^>]*>', brand, html)

    def src_brand(m):
        p = os.path.join(BRAND, m.group(2))
        if not os.path.exists(p):
            die('unknown brand file "%s"' % m.group(2))
        used.append(m.group(2))
        if m.group(2) == 'logo.png' and hashlib.sha256(read(p, 'rb')).hexdigest() != PINS['logo.png']:
            die('logo.png does not match PINS.json')
        return '%s="%s"' % (m.group(1), data_uri(p))
    html = re.sub(r'\b(src|href)="brand:([\w.\-]+)"', src_brand, html)

    def src_local(m):
        ref = m.group(2)
        if re.match(r'^(data:|https?:|mailto:|tel:|#|/)', ref):
            return m.group(0)
        p = os.path.normpath(os.path.join(base, ref))
        if not os.path.exists(p):
            die('missing local file "%s"' % ref)
        return '%s="%s"' % (m.group(1), data_uri(p))
    html = re.sub(r'<(?:img|source)\b[^>]*>', lambda t: re.sub(r'\b(src)="([^"]+)"', src_local, t.group(0)), html)

    left = re.findall(r'<!-- shift:[^>]*-->|(?:src|href)="brand:[\w.\-]+', html)
    if left:
        die('unresolved: %s' % ', '.join(sorted(set(left))[:5]))
    warn = []
    if re.search(r'<script\b[^>]*\bsrc="https?:', html):
        warn.append('external <script src> — the file will not work offline')
    if re.search(r'<link\b[^>]*rel="stylesheet"[^>]*href="https?:', html):
        warn.append('external stylesheet — use the kit tokens instead')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    size = os.path.getsize(out)
    if size > 3_000_000:
        warn.append('output is %.1f MB — compress or drop images' % (size / 1e6))
    print(json.dumps({'out': out, 'bytes': size, 'brand_assets': sorted(set(used)), 'warnings': warn}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
