#!/usr/bin/env python3
"""lint.py — brand, data and voice rules for a BUILT Shift Labs document (deck or page).

usage:  python3 lint.py DOC.html [--json]

Errors (exit 1): kit missing · raw colours or fonts outside the kit · <html> without lang/data-theme, or with
numbers but no data-mode · deck slide without exactly one .s-title (cover: h1; close: lockup) · numbers without a
"How we counted" note (.s-counted on that slide; on a page, .s-counted or .s-method) · glyphs the embedded fonts
lack (emoji included) · unknown shape / bad JSON / impossible shares · data-calc that does not recompute to the
shown value · a logo that is not the pinned file (official artwork, no white background, own border) byte for byte, sits on a white
background, is drawn inline, or is cropped/rounded/filtered/stretched ·
<img> without alt · more than one signal stat per slide.
Method (references/decision-method.md), every doc: no <!-- job: --> comment · pie/donut/stacked/area charts ·
causal, attribution, profitability or record language outside a data-evidence element (method notes and
data-example exempt) · unknown evidence level · a shape with "reconcile" that does not sum to its data-total ·
variance parts that do not reconcile to the total · columns below zero or with series/labels of different lengths ·
bullet without a target · heatmap values not rows x cols · decision rows without kind, title or all six fields ·
act/approve while evidence is missing · a dead link (href="#") · a disabled button without its reason.
Decision-ready report (<html data-doc="report">) adds: header data-mode badge · first-screen brief with six
answers · every KPI with a benchmark (.s-vs) and a metric contract row · complete contract rows · a trust panel
with nine fields · a decision queue · a claims ledger · a variance or tablegraph · drivers, decisions and
evidence sections.
Warnings: hype words, exclamation marks, sentences over 30 words, long titles / ledes / rules, missing eyebrows,
chart titles that read like conclusions, "Not captured" / "Not set" gaps, unsorted drivers, a single period
without its matched prior, sections out of the decision order, tables outside .s-table, unwired buttons.
Stdlib only. Fix every error; justify every warning in the delivery note.
"""
import base64, hashlib, json, os, re, sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
COV = os.path.normpath(os.path.join(HERE, '..', 'assets', 'fonts', 'coverage.json'))
PINS_PATH = os.path.normpath(os.path.join(HERE, '..', 'assets', 'brand', 'PINS.json'))
LOGO_SHA = 'bae4d33ad8c94c66'  # prefix of the trimmed logo.svg hash; the full pins live in assets/brand/PINS.json
KEYCAP_PATHS = ('m150.8 21.71h-112.1', 'm165.8 27.89c-3.52', 'M64.38 97.93 94.38 62.94')  # the logo's own geometry
LOGO_TOUCH = r'clip-path|object-fit|object-position|border-radius|transform|filter|mask|opacity|mix-blend|aspect-ratio|rotate|scale|background'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
SHAPES = {'ticks', 'axis', 'line', 'shares', 'flow', 'queue', 'diff', 'match', 'stairs', 'fanout',
          'columns', 'variance', 'tablegraph', 'bullet', 'heatmap'}
NUMERIC_SHAPES = {'shares', 'line', 'columns', 'variance', 'tablegraph', 'bullet', 'heatmap'}
BANNED = {'pie', 'donut', 'doughnut', 'stacked', 'stackedbar', 'area', 'stackedarea', 'radar', 'gauge', '3d', 'bar3d'}
LEVELS = {'confirmed', 'likely', 'suspected', 'correlated', 'unknown'}
KINDS = {'approve', 'investigate', 'defer', 'reject', 'act'}
FIELDS = ['evidence', 'missing', 'owner', 'review', 'status', 'source']
TRUST = ['mode', 'source', 'generated', 'period', 'cutoff', 'qa', 'definitions', 'scope', 'caveats']
BRIEF = ['changed', 'material', 'drivers', 'risk', 'decision', 'missing']
PARTS = ['movement', 'drivers', 'exposure', 'claims', 'decisions', 'evidence']
CAUSAL = re.compile(r'\b(because|due to|caus(?:e|es|ed|ing)\b|drove|drives?\b|driven by|driving|led to|leads? to|result(?:s|ed)? in|'
                    r'as a result|thanks to|accounts? for|accounted for|attribut(?:able|ed) to|contribut(?:ed|es|ing)|explains|explained by|is why|the reason (?:for|why)|'
                    r'(?:increase|rise|growth|drop|fall|decline|gain|change)s? (?:came|comes|come) from|boost(?:ed|s)\b|fuell?(?:ed|s)\b|'
                    r'profitab\w*)', re.I)
RECORD = re.compile(r'\b(all[- ]time (?:high|low|record|best)|a (?:new )?record\b|new record|record[- ](?:high|low|breaking|week|month|day|year|quarter)|'
                    r'best[- ]ever|highest ever|lowest ever|biggest ever|strongest ever|ever recorded)', re.I)
VERDICT = re.compile(r'\d|\b(record|best|worst|beats?|leads?|led|wins?|won|surg\w*|soar\w*|jump\w*|plung\w*|slump\w*|rose|rises|fell|falls|'
                     r'doubled|tripled|strong|weak|drove|drives)\b', re.I)
UNSET = re.compile(r'^\s*(not captured|not set)\b', re.I)
NONE = re.compile(r'^\s*(none|nothing missing|nothing)\.?\s*$', re.I)
BLOCKS = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'dd', 'dt', 'td', 'th', 'figcaption', 'blockquote', 'summary', 'caption'}
EXEMPT = {'s-counted', 's-method', 's-trust', 's-contract', 's-code', 's-log'}
WAYS = {'original', 'midnight', 'eggplant', 'ocean', 'ocean-dark', 'emerald', 'amber', 'coral', 'slate', 'lavender', 'mint', 'rose', 'white', 'charcoal', 'sky', 'peach'}
MODES = {'published', 'snapshot', 'live', 'sample', 'synthetic'}
HYPE = r'\b(revolutionar\w*|game[- ]chang\w*|seamless\w*|cutting[- ]edge|unlock\w*|supercharg\w*|leverag\w*|empower\w*|delve\w*|best[- ]in[- ]class|world[- ]class|next[- ]gen\w*|groundbreaking|magic(al)?)\b'
COLOR = re.compile(r'#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\boklch\(|\blab\(')


class N:
    __slots__ = ('tag', 'attrs', 'kids', 'parent', 'text')

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent, self.text = tag, attrs, [], parent, ''

    def cls(self):
        return self.attrs.get('class', '').split()

    def has(self, c):
        return c in self.cls()

    def walk(self):
        yield self
        for k in self.kids:
            if isinstance(k, N):
                yield from k.walk()

    def find(self, pred):
        return [n for n in self.walk() if pred(n)]

    def txt(self, skip=('script', 'style')):
        out = []
        for k in self.kids:
            if isinstance(k, N):
                if k.tag not in skip:
                    out.append(k.txt(skip))
            else:
                out.append(k)
        return ''.join(out)


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = N('#root', {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = N(tag, {k: (v or '') for k, v in attrs}, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(N(tag, {k: (v or '') for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, d):
        self.cur.kids.append(d)


def num_value(s):
    m = re.search(r'-?\d[\d,]*(?:\.\d+)?', s.replace('\u2212', '-'))
    if not m:
        return None, 0
    t = m.group(0).replace(',', '')
    return float(t), (len(t.split('.')[1]) if '.' in t else 0)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    path = args[0]
    html = open(path, encoding='utf-8').read()
    E, W = [], []
    if 'data-shift-kit' not in html or 'data-shift-fonts' not in html:
        E.append('kit not inlined — lint the BUILT file (python3 build.py SRC.src.html)')
    p = P()
    p.feed(html)
    root = p.root
    htmls = root.find(lambda n: n.tag == 'html')
    h = htmls[0] if htmls else N('html', {}, None)
    body = (root.find(lambda n: n.tag == 'body') or [root])[0]
    is_deck = body.has('s-deck')

    # --- document frame
    if not h.attrs.get('lang'):
        E.append('<html> needs lang')
    if h.attrs.get('data-theme') not in ('light', 'dark'):
        E.append('<html data-theme> must be light or dark (the reader can toggle)')
    mode = h.attrs.get('data-mode')
    numeric = lambda scope: bool(scope.find(lambda n: n.has('s-stat') or 'data-total' in n.attrs or n.has('s-card__meta') and n.txt().strip() not in ('n/a', '—') or (n.has('s-shape') and n.attrs.get('data-shape') in NUMERIC_SHAPES)))
    doc_kind = h.attrs.get('data-doc', '')
    report = doc_kind == 'report'
    if doc_kind and doc_kind not in ('report', 'research'):
        E.append('unknown data-doc "%s" (report | research)' % doc_kind)
    job = re.search(r'<!--\s*job:\s*(.*?)-->', html, re.S)
    if not job:
        E.append('no <!-- job: reader, decision --> under <title> \u2014 write the job before any chart')
    elif report and len(job.group(1).split()) < 8:
        E.append('report job "%s" is too thin \u2014 name the reader, the decision and what changes it' % job.group(1).strip()[:60])
    if numeric(body) and mode not in MODES:
        E.append('document shows numbers: set <html data-mode="published|snapshot|live|sample|synthetic">')
    elif mode and mode not in MODES:
        E.append('unknown data-mode "%s"' % mode)

    # --- author CSS: tokens only
    author_css = [n.txt(skip=()) for n in root.find(lambda n: n.tag == 'style' and 'data-shift-kit' not in n.attrs)]
    def in_sprite(n):
        while n is not None:
            if n.attrs.get('id') == 's-sprite':
                return True
            n = n.parent
        return False
    for n in root.find(lambda n: 'style' in n.attrs):
        if not in_sprite(n):
            author_css.append(n.attrs['style'])
    for css in author_css:
        for m in COLOR.finditer(css):
            E.append('raw colour "%s" outside the kit — use var(--s-*) tokens' % css[max(0, m.start() - 20):m.end() + 12].strip())
        for m in re.finditer(r'font-family\s*:\s*([^;}"]+)', css):
            if 'var(--s-f-' not in m.group(1):
                E.append('font-family "%s" — use var(--s-f-sans|display|mono)' % m.group(1).strip()[:40])

    # --- the logo: the original file, as it is
    pins = json.load(open(PINS_PATH)) if os.path.exists(PINS_PATH) else {'avatars': {}}
    ok_logo = {pins['logo.svg']} if 'logo.svg' in pins else set()
    ok_avatar = set(pins.get('avatars', {}).values())
    logos = 0
    for n in root.find(lambda n: n.tag == 'img' and ('data-brand' in n.attrs or 'image/svg+xml' in n.attrs.get('src', ''))):
        src = n.attrs.get('src', '')
        m = re.match(r'data:image/svg\+xml;base64,(.+)$', src)
        raw = base64.b64decode(m.group(1)) if m else b''
        sha = hashlib.sha256(raw).hexdigest() if raw else ''
        brand = n.attrs.get('data-brand', '')
        if raw and re.search(rb'<rect[^>]*fill="#(?:fff|ffffff|FFF|FFFFFF)"', raw):
            E.append('%s has a white background — the logo is used without it (assets/brand/logo.svg)' % (brand or 'logo image'))
        if brand == 'logo':
            logos += 1
            if sha not in ok_logo:
                E.append('logo is not the pinned file byte for byte — use <img data-brand="logo"> and build.py')
        elif brand.startswith('avatar-'):
            if sha not in ok_avatar:
                E.append('%s is not the official avatar file byte for byte' % brand)
        elif raw and any(k.encode() in raw for k in KEYCAP_PATHS):
            E.append('an edited copy of the logo is embedded as an image — use the original via data-brand="logo"')
        st = n.attrs.get('style', '')
        if re.search(LOGO_TOUCH, st, re.I):
            E.append('%s is styled with "%s" — the logo is used as it is (size only)' % (brand or 'logo', st[:60]))
        w, h = re.search(r'(?<![-\w])width\s*:\s*([^;]+)', st), re.search(r'(?<![-\w])height\s*:\s*([^;]+)', st)
        if w and h:
            E.append('%s sets both width and height (%s × %s) — size the logo by height only, never stretch it' % (brand or 'logo', w.group(1).strip(), h.group(1).strip()))
    if logos == 0:
        W.append('no logo — a Shift Labs document carries the original logo (page header/footer, deck cover/close)')
    for n in root.find(lambda n: n.tag in ('svg', 'symbol', 'path') and n.attrs.get('id') != 's-sprite'):
        d = n.attrs.get('d', '') + ' ' + n.txt(skip=())
        if any(k in d for k in KEYCAP_PATHS):
            E.append('the logo is redrawn as inline SVG — use <img data-brand="logo"> (the original file, never cut or redrawn)')
            break
    for css in author_css:
        for m2 in re.finditer(r'([^{}]*\.s-logo[^{}]*)\{([^}]*)\}', css):
            if re.search(r'(?<![-\w])(' + LOGO_TOUCH + r')\s*:', m2.group(2), re.I):
                E.append('CSS "%s" touches the logo beyond size — the logo is used as it is' % m2.group(0).strip()[:80])
    for n in root.find(lambda n: n.tag == 'img' and 'alt' not in n.attrs):
        E.append('<img> without alt: %s' % n.attrs.get('src', '')[:40])

    # --- shapes
    specs = []
    for n in root.find(lambda n: n.has('s-shape')):
        name = n.attrs.get('data-shape')
        if name in BANNED or re.search(r'pie|donut|doughnut|stack|area', name or '', re.I):
            E.append('chart "%s" is banned by the method \u2014 composition is shares or tablegraph, change is variance' % name)
            continue
        if name not in SHAPES:
            E.append('unknown shape "%s" (known: %s)' % (name, ', '.join(sorted(SHAPES))))
            continue
        js = [k for k in n.kids if isinstance(k, N) and k.tag == 'script']
        try:
            spec = json.loads(js[0].txt(skip=())) if js else {}
        except Exception as e:
            E.append('shape %s: bad JSON (%s)' % (name, e))
            continue
        if name == 'shares':
            rows = spec.get('rows', [])
            vals = [r[1] for r in rows if r[1] is not None]
            if spec.get('unit', '%') == '%' and any(v < 0 or v > 100 for v in vals):
                E.append('shares: a percentage outside 0–100')
            if 'total' in spec and vals and abs(sum(vals) - spec['total']) > 0.5 * len(vals):
                E.append('shares: rows sum to %s, not the stated total %s (beyond rounding)' % (sum(vals), spec['total']))
            if len(rows) > 10:
                W.append('shares with %d rows — keep the top 9 and fold the rest into "Other"' % len(rows))
            if vals and any(vals[i] < vals[i + 1] for i in range(len(vals) - 1)):
                W.append('shares not sorted high → low (%s)' % rows[0][0])
        specs.append((name, spec, n))
        if name == 'line':
            if 'series' in spec:
                for s in spec['series']:
                    if len(s.get('values', [])) < 2:
                        E.append('line series "%s" needs 2+ values' % s.get('name', ''))
                    if spec.get('x') and len(s.get('values', [])) != len(spec['x']):
                        E.append('line series "%s": %d values for %d x labels' % (s.get('name', ''), len(s.get('values', [])), len(spec['x'])))
            elif len(spec.get('values', [])) < 2:
                E.append('line needs 2+ values')
            if spec.get('smooth'):
                E.append('smoothed lines are banned \u2014 straight segments between observations')

    # --- method: reconciliation, decomposition, chart jobs
    def decs(*xs):
        return max([len(repr(float(x)).split('.')[1].rstrip('0')) for x in xs if isinstance(x, (int, float))] + [0])
    totals = {}
    for n in root.find(lambda n: 'data-total' in n.attrs):
        v = n.attrs.get('data-v')
        val = float(v) if v not in (None, '') and re.fullmatch(r'-?[\d.]+', v) else num_value(n.txt())[0]
        if val is None:
            E.append('data-total="%s" has no number (add data-v)' % n.attrs['data-total'])
        else:
            totals[n.attrs['data-total']] = val
    for name, spec, node in specs:
        vals = None
        if name == 'variance':
            rows = spec.get('rows', [])
            ds = [(r[2] - r[1]) if len(r) > 2 else r[1] for r in rows]
            if 'total' not in spec:
                E.append('variance needs "total" \u2014 the headline change its parts must reconcile to')
            elif ds and abs(sum(ds) - spec['total']) > 0.5 * 10 ** -decs(spec['total'], *ds) + 1e-9:
                E.append('variance does not reconcile: parts sum to %s, total is %s' % (round(sum(ds), 6), spec['total']))
            if any(abs(ds[i]) < abs(ds[i + 1]) for i in range(len(ds) - 1)):
                W.append('variance rows not ranked by size of contribution (largest |change| first)')
            vals = [spec['total']] if 'total' in spec else ds
        elif name == 'columns':
            ser = spec.get('series') or [{'values': spec.get('values', [])}]
            cur = [s for s in ser if s.get('role') != 'prior']
            if any(v is not None and v < 0 for s in ser for v in s.get('values', [])):
                E.append('columns are zero-based amounts \u2014 use variance for signed changes')
            if spec.get('x') and any(len(s.get('values', [])) != len(spec['x']) for s in ser):
                E.append('columns: every series needs one value per x label')
            if not any(s.get('role') == 'prior' for s in ser):
                W.append('columns without a matched prior ("role":"prior") \u2014 one period cannot say whether it is good')
            vals = cur[0].get('values', []) if cur else []
        elif name == 'tablegraph':
            rows = spec.get('rows', [])
            vals = [r[1] for r in rows]
            if any(vals[i] < vals[i + 1] for i in range(len(vals) - 1)):
                W.append('tablegraph rows not sorted high \u2192 low')
        elif name == 'shares':
            vals = [r[1] for r in spec.get('rows', []) if r[1] is not None]
        elif name == 'bullet':
            for r in spec.get('rows', []):
                if r.get('target') is None or r.get('value') is None:
                    E.append('bullet "%s" needs a value and a target (no target: use shares)' % r.get('label', ''))
        elif name == 'heatmap':
            V, nr, nc = spec.get('values', []), len(spec.get('rows', [])), len(spec.get('cols', []))
            if len(V) != nr or any(len(r) != nc for r in V):
                E.append('heatmap values must be %d rows x %d cols' % (nr, nc))
            vals = [v for r in V for v in r if v is not None]
        key = spec.get('reconcile')
        if key:
            if key not in totals:
                E.append('%s reconciles to "%s" but no element has data-total="%s"' % (name, key, key))
            elif vals is not None:
                s = sum(v for v in vals if v is not None)
                if abs(s - totals[key]) > 0.5 * 10 ** -decs(totals[key], *[v for v in vals if v is not None]) + 1e-9:
                    E.append('%s sums to %s but data-total="%s" is %s' % (name, round(s, 6), key, totals[key]))
    for n in root.find(lambda n: n.tag == 'canvas' or re.search(r'\b(pie|donut|doughnut)\b', n.attrs.get('class', ''))):
        E.append('pie/donut or canvas chart \u2014 the kit draws charts from JSON shapes only')
    for n in root.find(lambda n: n.has('s-fig-head') or n.has('s-shares-head')):
        for t in n.find(lambda k: k.tag in ('h3', 'h4')):
            if VERDICT.search(t.txt()):
                W.append('chart title "%s" reads like a conclusion \u2014 name the metric; the reading goes in the subtitle' % t.txt().strip()[:50])

    # --- method: the evidence ladder (claims need a level)
    for n in root.find(lambda n: 'data-evidence' in n.attrs):
        if n.attrs['data-evidence'] not in LEVELS:
            E.append('data-evidence "%s" (levels: %s)' % (n.attrs['data-evidence'], ', '.join(sorted(LEVELS))))
    def exempt(n):
        while n is not None:
            if n.tag in ('script', 'style', 'pre', 'code', 'svg', 'head') or 'data-evidence' in n.attrs or 'data-example' in n.attrs or set(n.cls()) & EXEMPT:
                return True
            n = n.parent
        return False
    groups = {}
    for n in body.walk():
        own = ''.join(k for k in n.kids if isinstance(k, str))
        if not own.strip() or exempt(n):
            continue
        b = n
        while b is not None and b.tag not in BLOCKS and b is not body:
            b = b.parent
        b = b or n
        groups.setdefault(id(b), [b, []])[1].append(own)
    for b, parts in groups.values():
        if b.find(lambda k: 'data-evidence' in k.attrs):
            continue
        t = re.sub(r'\s+', ' ', ' '.join(parts))
        for rx, what in ((CAUSAL, 'causal or attribution'), (RECORD, 'record')):
            m = rx.search(t)
            if m:
                E.append('%s claim without an evidence level: "\u2026%s\u2026" \u2014 add a .s-claim chip or data-evidence' % (what, t[max(0, m.start() - 30):m.end() + 25].strip()))

    # --- method: action gates (any doc that has them)
    decisions = root.find(lambda n: n.has('s-decision'))
    for d in decisions:
        kind = d.attrs.get('data-kind', '')
        title = (d.find(lambda k: k.has('s-decision__title')) or [None])[0]
        tt = title.txt().strip()[:40] if title else '?'
        if kind not in KINDS:
            E.append('decision "%s": data-kind must be %s' % (tt, ' | '.join(sorted(KINDS))))
        if not title:
            E.append('decision without .s-decision__title (the decision requested)')
        got = {f.attrs['data-field']: f for f in d.find(lambda k: 'data-field' in k.attrs)}
        dd = lambda f: (got[f].find(lambda k: k.tag == 'dd') or [got[f]])[0].txt().strip() if f in got else ''
        miss = [f for f in FIELDS if not dd(f)]
        if miss:
            E.append('decision "%s" missing fields: %s' % (tt, ', '.join(miss)))
        if kind in ('act', 'approve') and dd('missing') and not NONE.match(dd('missing')):
            E.append('"%s" decision "%s" while evidence is missing \u2014 downgrade it to investigate (learning before intervention)' % (kind, tt))
        for f in ('owner', 'review'):
            if UNSET.match(dd(f)):
                W.append('decision "%s": %s not set \u2014 a decision needs a named owner and a review point' % (tt, f))
    for n in root.find(lambda n: n.tag == 'a' and 'href' in n.attrs and n.attrs['href'].strip() in ('#', '', 'javascript:void(0)')):
        E.append('dead link "%s" \u2014 point it somewhere real or remove it' % n.txt().strip()[:30])
    for n in root.find(lambda n: n.tag == 'button' and 'disabled' not in n.attrs and 'data-wired' not in n.attrs and not any(a.startswith('on') for a in n.attrs)):
        W.append('button "%s" is not wired \u2014 wire it (data-wired), or disable it with the reason in title' % n.txt().strip()[:30])
    for n in root.find(lambda n: n.tag == 'button' and 'disabled' in n.attrs and not (n.attrs.get('title') or n.attrs.get('aria-describedby'))):
        E.append('disabled button "%s" without its reason (title or aria-describedby)' % n.txt().strip()[:30])
    def inside(n, c):
        while n is not None:
            if n.has(c):
                return True
            n = n.parent
        return False
    for n in root.find(lambda n: n.tag == 'table' and not n.has('s-ledger') and 'data-reflow' not in n.attrs and not inside(n, 's-table')):
        W.append('table outside .s-table \u2014 wide tables scroll inside their own box (or reflow with data-reflow)')

    # --- method: the decision-ready report contract
    if report:
        if is_deck:
            if not body.attrs.get('data-runfoot'):
                E.append('report deck needs data-runfoot (the data mode rides in the running footer)')
        elif not root.find(lambda n: n.has('s-mode') and inside(n, 's-head')):
            E.append('report needs the persistent data-mode badge (.s-mode in header.s-head)')
        briefs = root.find(lambda n: n.has('s-brief'))
        if not briefs:
            E.append('report needs the first-screen brief (dl.s-brief: %s)' % ', '.join(BRIEF))
        else:
            qs_ = {q.attrs['data-q']: q.txt().strip() for q in briefs[0].find(lambda k: 'data-q' in k.attrs)}
            miss = [q for q in BRIEF if not qs_.get(q)]
            if miss:
                E.append('brief does not answer: %s' % ', '.join(miss))
        contract = {}
        for r in root.find(lambda n: n.tag == 'tr' and 'data-metric' in n.attrs):
            cells = [c for c in r.kids if isinstance(c, N) and c.tag in ('td', 'th')]
            contract[r.attrs['data-metric']] = cells
            if len(cells) < 9 or any(not c.txt().strip() for c in cells):
                E.append('metric contract "%s" needs nine cells: metric, meaning, source, grain, calculation, exclusions, comparison, owner, action' % r.attrs['data-metric'])
            elif any(UNSET.match(c.txt()) for c in cells):
                W.append('metric contract "%s" has a field not set' % r.attrs['data-metric'])
        if not contract:
            E.append('report needs metric contracts (table.s-contract, one tr[data-metric] per KPI)')
        for s in root.find(lambda n: n.has('s-stat')):
            nm = (s.find(lambda k: k.tag == 'b') or [s])[0].txt().strip()[:20]
            if not s.find(lambda k: k.has('s-vs')):
                E.append('KPI %s has no benchmark (.s-vs: the matched period, plan or target)' % nm)
            m = s.attrs.get('data-metric')
            if not m:
                E.append('KPI %s has no data-metric (link it to its contract row)' % nm)
            elif m not in contract:
                E.append('KPI %s: no contract row tr[data-metric="%s"]' % (nm, m))
        got = {}
        for p_ in root.find(lambda n: n.has('s-trust')):
            for f in p_.find(lambda k: 'data-trust' in k.attrs):
                got[f.attrs['data-trust']] = (f.find(lambda k: k.tag == 'dd') or [f])[0].txt().strip()
        miss = [k for k in TRUST if not got.get(k)]
        if miss:
            E.append('trust panel (.s-trust) missing: %s \u2014 write "Not captured" when a field was not captured' % ', '.join(miss))
        gaps = [k for k in TRUST if UNSET.match(got.get(k, 'x'))]
        if gaps:
            W.append('trust fields not captured: %s \u2014 say what it would take to capture them' % ', '.join(gaps))
        if not decisions:
            E.append('report needs a decision queue (.s-decisions > article.s-decision)')
        ledgers = root.find(lambda n: n.has('s-ledger'))
        if not ledgers:
            E.append('report needs a claims ledger (table.s-ledger: claim, level, what would settle it, source)')
        for lg in ledgers:
            for r in lg.find(lambda n: n.tag == 'tr' and n.parent is not None and n.parent.tag == 'tbody'):
                if r.attrs.get('data-evidence') not in LEVELS:
                    E.append('ledger row "%s" needs data-evidence' % r.txt().strip()[:40])
        if not any(nm in ('variance', 'tablegraph') for nm, _, _ in specs):
            E.append('report has no decomposition \u2014 add a variance or tablegraph (what moved the headline)')
        parts = [n.attrs['data-part'] for n in root.find(lambda n: 'data-part' in n.attrs)]
        for need in ('drivers', 'decisions', 'evidence'):
            if need not in parts:
                E.append('report has no data-part="%s" section' % need)
        known = [p_ for p_ in parts if p_ in PARTS]
        if known != sorted(known, key=PARTS.index):
            W.append('sections out of the decision order (%s): %s' % (' \u2192 '.join(PARTS), ' \u2192 '.join(known)))

    # --- recomputable numbers
    for n in root.find(lambda n: 'data-calc' in n.attrs):
        expr = n.attrs['data-calc']
        if not re.fullmatch(r'[\d\s.+\-*/()]+', expr):
            E.append('data-calc "%s" may contain only numbers and + - * / ( )' % expr)
            continue
        try:
            val = eval(expr, {'__builtins__': {}}, {})
        except Exception:
            E.append('data-calc "%s" does not evaluate' % expr)
            continue
        shown, dec = num_value(n.txt())
        if shown is None or abs(round(val, dec) - shown) > 10 ** (-dec) / 2 + 1e-9:
            E.append('data-calc %s = %s but the text shows "%s"' % (expr, round(val, dec + 2), n.txt().strip()[:20]))

    # --- per slide / page structure
    scopes = body.find(lambda n: n.has('s-slide')) if is_deck else [body]
    for i, s in enumerate(scopes, 1):
        tag = ('slide %d: ' % i) if is_deck else ''
        titles = s.find(lambda n: n.has('s-title'))
        if is_deck:
            if s.has('is-close'):
                pass
            elif len(titles) != 1:
                E.append(tag + '%d .s-title (need exactly 1)' % len(titles))
            if not s.has('is-cover') and not s.has('is-close') and not s.find(lambda n: n.has('s-eyebrow')):
                W.append(tag + 'no .s-eyebrow (section kicker)')
            if titles and len(titles[0].txt().strip()) > 48:
                W.append(tag + 'title over 48 characters — a slide title names one thing')
            for l in s.find(lambda n: n.has('s-lede') and not n.has('is-cover')):
                if len(l.txt().strip()) > 220:
                    W.append(tag + 'lede over 220 characters')
            if numeric(s) and not s.find(lambda n: n.has('s-counted')):
                E.append(tag + 'shows numbers but has no .s-counted ("How we counted.")')
            if len(s.find(lambda n: n.has('s-stat') and n.has('is-signal'))) > 1:
                E.append(tag + 'more than one signal (orange) stat — orange marks the one thing that fired')
        else:
            h1 = s.find(lambda n: n.tag == 'h1')
            if len(h1) != 1:
                E.append('page needs exactly one <h1> (found %d)' % len(h1))
            if numeric(s) and not s.find(lambda n: n.has('s-counted') or n.has('s-method') or n.has('s-trust')):
                E.append('page shows numbers but has no method note (.s-counted, .s-method or .s-trust)')
        for r in s.find(lambda n: n.has('s-rule')):
            if len(r.txt().strip()) > 160:
                W.append(tag + '.s-rule over 160 characters — a rule is one instruction')

    # --- glyphs + voice (visible text only)
    cov = set()
    if os.path.exists(COV):
        d = json.load(open(COV))
        cov = set(d.get('sans', [])) | set(d.get('mono', []))
    text = body.txt(skip=('script', 'style', 'svg')) + ' ' + ' '.join(n.attrs.get('aria-label', '') for n in body.walk())
    bad = sorted({c for c in text if cov and ord(c) not in cov and not c.isspace()})
    if bad:
        E.append('glyphs the embedded fonts lack (draw them or reword): %s' % ' '.join('%s U+%04X' % (c, ord(c)) for c in bad[:12]))
    prose = re.sub(r'\s+', ' ', ' \u2016 '.join(n.txt() for n in body.find(lambda n: n.tag in ('p', 'li', 'h1', 'h2', 'h3', 'dd', 'figcaption') and not n.find(lambda k: k.has('s-code')))))
    for m in set(x.group(0).lower() for x in re.finditer(HYPE, prose, re.I)):
        W.append('hype word "%s" — state the fact instead' % m)
    if '!' in prose.replace('!=', '').replace('!cursor', ''):
        W.append('exclamation mark in prose')
    for sent in re.split(r'(?<=[.?])\s+|\s*\u2016\s*', prose):
        if len(sent.split()) > 30:
            W.append('sentence over 30 words: "%s…"' % sent[:60])

    res = {'doc': os.path.abspath(path), 'kind': 'deck' if is_deck else 'page', 'errors': E, 'warnings': sorted(set(W))}
    if '--json' in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print('%s (%s): %d errors, %d warnings' % (path, res['kind'], len(E), len(res['warnings'])))
        for e in E:
            print('  E ' + e)
        for w in res['warnings']:
            print('  W ' + w)
    sys.exit(1 if E else 0)


if __name__ == '__main__':
    main()
