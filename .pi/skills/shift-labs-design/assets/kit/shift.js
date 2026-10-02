/* shift.js — Shift Labs design kit runtime (skill shift-labs-design). window.SL
 * theme (light paper / dark charcoal) · deck frame (fit, nav, running footer) · JS highlighting ·
 * shapes rendered from <figure class="s-shape" data-shape="…"><script type="application/json">{…}
 * Status for verification: window.__shift = { ready, errors, shapes, drawn }. No dependencies. */
(function () {
  'use strict';
  var ST = window.__shift = { ready: false, errors: [], shapes: 0, drawn: 0, theme: null };
  var doc = document, root = doc.documentElement;
  var qs = function (s, r) { return (r || doc).querySelector(s); };
  var qsa = function (s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); };
  var NS = 'http://www.w3.org/2000/svg';
  var params = new URLSearchParams(location.search);

  /* ---------- theme ---------- */
  var KEY = 'shift-theme';
  function getStored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function setTheme(t, persist) {
    t = t === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-theme', t); ST.theme = t;
    if (persist) { try { localStorage.setItem(KEY, t); } catch (e) { /* private mode */ } }
    qsa('.s-theme-toggle').forEach(function (b) { b.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'); b.setAttribute('aria-pressed', String(t === 'dark')); });
  }
  var initial = params.get('theme') || getStored() || root.getAttribute('data-theme') || 'light';
  setTheme(initial, false);

  function el(tag, attrs, kids) {
    var e = doc.createElement(tag);
    if (attrs) for (var k in attrs) { if (attrs[k] == null) continue; if (k === 'text') e.textContent = attrs[k]; else if (k === 'html') e.innerHTML = attrs[k]; else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === 'string' ? doc.createTextNode(c) : c); });
    return e;
  }
  function sv(tag, attrs, parent) {
    var e = doc.createElementNS(NS, tag);
    for (var k in attrs) { if (attrs[k] == null) continue; if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); }
    if (parent) parent.appendChild(e);
    return e;
  }
  var r2 = function (v) { return Math.round(v * 100) / 100; };

  function themeToggle() {
    var b = el('button', { type: 'button', class: 's-theme-toggle', 'aria-pressed': 'false' });
    b.innerHTML = '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 2.8a7.2 7.2 0 0 1 0 14.4z" fill="currentColor"/></svg>';
    b.addEventListener('click', function () { setTheme(ST.theme === 'dark' ? 'light' : 'dark', true); SL.redraw(); });
    return b;
  }

  /* ---------- units ---------- */
  function uPx(node) {
    var p = el('span', { style: 'position:absolute;visibility:hidden;width:calc(100 * var(--u));height:0' });
    node.appendChild(p); var w = p.offsetWidth / 100; node.removeChild(p);
    return w || 1.333;
  }
  function floors(node) {
    var cs = getComputedStyle(node);
    var f = function (n) { return parseFloat(cs.getPropertyValue(n)) || 0; };
    return { label: f('--s-min-label'), small: f('--s-min-small'), code: f('--s-min-code') };
  }

  /* ---------- code highlighting (JS / TS sketches) ---------- */
  var KW = /^(const|let|var|if|else|return|await|async|for|of|in|new|function|true|false|null|undefined|continue|break|throw|try|catch|finally|typeof|while|do|switch|case|default|export|import|from|class|this|yield)$/;
  function esc(s) { return s.replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }
  function span(c, s) { return '<span class="t-' + c + '">' + esc(s) + '</span>'; }
  function hl(src) {
    var out = '', i = 0, n = src.length, m;
    var re = {
      com: /^(\/\/[^\n]*|\/\*[\s\S]*?\*\/|#[^\n]*(?=\n|$))/,
      str: /^('(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*")/,
      num: /^(\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?)/i,
      id: /^([A-Za-z_$][\w$]*)/,
      op: /^(=>|===|!==|==|!=|\?\?|\?\.|\|\||&&|<=|>=|[=!<>+\-*\/%])/,
      pun: /^([{}()\[\],.;:?])/
    };
    while (i < n) {
      var s = src.slice(i);
      if (s[0] === '`') { // template string: string parts coloured, ${…} highlighted as code
        var j = 1, buf = '`', depth;
        while (j < s.length && s[j] !== '`') {
          if (s[j] === '\\') { buf += s.substr(j, 2); j += 2; continue; }
          if (s[j] === '$' && s[j + 1] === '{') {
            out += span('str', buf); buf = ''; depth = 1; var k = j + 2;
            while (k < s.length && depth) { if (s[k] === '{') depth++; else if (s[k] === '}') depth--; k++; }
            out += span('pun', '${') + hl(s.slice(j + 2, k - 1)) + span('pun', '}'); j = k; continue;
          }
          buf += s[j]; j++;
        }
        out += span('str', buf + (s[j] === '`' ? '`' : '')); i += j + 1; continue;
      }
      if ((m = re.com.exec(s)) && !(s[0] === '#' && /[\w$]/.test(src[i - 1] || ''))) { out += span('com', m[0]); i += m[0].length; continue; }
      if ((m = re.str.exec(s))) { out += span('str', m[0]); i += m[0].length; continue; }
      if ((m = re.num.exec(s)) && !/[\w$]/.test(src[i - 1] || '')) { out += span('num', m[0]); i += m[0].length; continue; }
      if ((m = re.id.exec(s))) { out += KW.test(m[0]) ? span('kw', m[0]) : span('id', m[0]); i += m[0].length; continue; }
      if ((m = re.op.exec(s))) { out += span('op', m[0]); i += m[0].length; continue; }
      if ((m = re.pun.exec(s))) { out += span('pun', m[0]); i += m[0].length; continue; }
      out += esc(s[0]); i++;
    }
    return out;
  }
  function highlightAll() {
    qsa('pre.s-code[data-spec-of]').forEach(function (pre) { // print a shape's own JSON spec (docs, brand book)
      if (pre.__spec) return; pre.__spec = true;
      var src = qs('#' + pre.getAttribute('data-spec-of') + ' script[type="application/json"]');
      if (src) { try { pre.textContent = JSON.stringify(JSON.parse(src.textContent)).replace(/,"/g, ', "').replace(/\],\[/g, '], ['); } catch (e) { ST.errors.push('spec-of: ' + e.message); } }
    });
    qsa('pre.s-code:not([data-lang="text"])').forEach(function (pre) {
      if (pre.__hl) return; pre.__hl = true;
      var src = pre.textContent.replace(/^\n/, '').replace(/\s+$/, '');
      pre.innerHTML = '<code>' + hl(src) + '</code>';
    });
  }

  /* ---------- shape helpers ---------- */
  function spec(fig) {
    var s = qs('script[type="application/json"]', fig);
    try { return s ? JSON.parse(s.textContent) : {}; } catch (e) { ST.errors.push('bad JSON in ' + (fig.getAttribute('data-shape') || 'shape') + ': ' + e.message); return null; }
  }
  function svgFor(fig, Wu, Hu) {
    var old = qs(':scope > svg.s-shape__svg', fig); if (old) old.remove();
    var s = sv('svg', { class: 's-shape__svg', viewBox: '0 0 ' + r2(Wu) + ' ' + r2(Hu), role: 'img' });
    fig.appendChild(s); return s;
  }
  function label(parent, x, y, text, cls, size, anchor, Wu) {
    var lines = String(text).split('\n');
    var t = sv('text', { x: r2(x), y: r2(y), class: cls, 'font-size': r2(size), 'text-anchor': anchor || 'middle' }, parent);
    lines.forEach(function (ln, i) { sv('tspan', { x: r2(x), dy: i ? r2(size * 1.25) : 0, text: ln }, t); });
    if (Wu) { // keep inside the frame
      try { var bb = t.getBBox(); if (bb.x < 0) t.setAttribute('transform', 'translate(' + r2(-bb.x) + ',0)'); else if (bb.x + bb.width > Wu) t.setAttribute('transform', 'translate(' + r2(Wu - bb.x - bb.width) + ',0)'); } catch (e) { /* not rendered */ }
    }
    return t;
  }
  function declutter(svg, texts, rowH) { // same-row labels that collide move down a row; returns extra height
    var placed = [], extra = 0;
    texts.forEach(function (t) {
      var b; try { b = t.getBBox(); } catch (e) { return; }
      var tr = t.getAttribute('transform') || '', dx = /translate\(([-\d.]+)/.exec(tr), ox = dx ? parseFloat(dx[1]) : 0;
      var box = { x0: b.x + ox - 2, x1: b.x + b.width + ox + 2 }, row = 0;
      while (placed.some(function (q) { return q.row === row && q.x0 < box.x1 && box.x0 < q.x1; })) row++;
      box.row = row; placed.push(box);
      if (row) { t.setAttribute('transform', (tr ? tr + ' ' : '') + 'translate(0,' + r2(row * rowH) + ')'); extra = Math.max(extra, row * rowH); }
    });
    if (extra) { var vb = svg.getAttribute('viewBox').split(' ').map(Number); vb[3] += extra; svg.setAttribute('viewBox', vb.join(' ')); }
    return extra;
  }
  function ring(g, x, y, r, tone) { // the "fired" mark: ring + dot
    if (tone === 'hollow') { sv('circle', { cx: r2(x), cy: r2(y), r: r2(r), class: 'k-ink k-fill-bg', 'stroke-width': 1.2 }, g); return; }
    sv('circle', { cx: r2(x), cy: r2(y), r: r2(r), class: 'k-sig k-fill-bg', 'stroke-width': 1 }, g);
    sv('circle', { cx: r2(x), cy: r2(y), r: r2(r * 0.42), class: 'k-fill-sig' }, g);
  }
  function check(g, x, y, s, cls) { sv('path', { d: 'M' + r2(x - s * .5) + ' ' + r2(y) + 'l' + r2(s * .33) + ' ' + r2(s * .34) + 'l' + r2(s * .67) + ' ' + r2(-s * .72), class: cls || 'k-ink2', 'stroke-width': r2(s * .13), 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g); }
  function cross(g, x, y, s) { var h = s * .42; sv('path', { d: 'M' + r2(x - h) + ' ' + r2(y - h) + 'L' + r2(x + h) + ' ' + r2(y + h) + 'M' + r2(x + h) + ' ' + r2(y - h) + 'L' + r2(x - h) + ' ' + r2(y + h), class: 'k-sig', 'stroke-width': r2(s * .15), 'stroke-linecap': 'round' }, g); }
  function arrowSvg(sig) {
    return '<svg viewBox="0 0 40 8" preserveAspectRatio="xMaxYMid meet" aria-hidden="true"><path d="M0 4H34" stroke="currentColor" stroke-width="1" fill="none"/><path d="M33 1.2L39 4L33 6.8z" fill="currentColor"/></svg>';
  }
  function frame(fig) { var W = fig.clientWidth; var u = uPx(fig); return { W: W, u: u, Wu: W / u, fl: floors(fig) }; }
  function fsz(n, F, kind) { return Math.max(n, (F.fl[kind || 'label'] || 0) / F.u); }

  var SHAPES = {};

  /* ticks — one mark per run; fired runs ringed. style "check": ✓ ok / ✗ failed */
  SHAPES.ticks = function (fig, S) {
    var F = frame(fig); if (!F.W) return false;
    var runs = S.runs || (function () { var a = []; for (var i = 0; i < (S.n || 48); i++) a.push((S.fired || []).indexOf(i) >= 0 ? '1' : '.'); return a.join(''); })();
    var n = runs.length, pad = S.pad != null ? S.pad : 6, check_ = S.style === 'check';
    var notes = S.notes || [];
    var lab = fsz(6.2, F), top = check_ ? 12 : 14, rows = Math.max.apply(null, [0].concat(notes.map(function (x) { return x.row || 0; }))) + 1;
    var lines = Math.max.apply(null, [1].concat(notes.map(function (x) { return String(x.text).split('\n').length; })));
    var noteH = notes.length ? 12 + rows * (lab * 1.25 * lines + 3) + 2 : 0;
    var Hu = top + (check_ ? 10 : 11) + noteH;
    var svg = svgFor(fig, F.Wu, Hu), g = sv('g', {}, svg);
    var X = function (i) { return pad + (n === 1 ? 0 : i * (F.Wu - 2 * pad) / (n - 1)); };
    for (var i = 0; i < n; i++) {
      var on = runs[i] !== '.' && runs[i] !== ' ', x = X(i);
      if (check_) { if (on) cross(g, x, top, 7.5); else check(g, x, top + 1, 7.5); }
      else {
        sv('line', { x1: r2(x), x2: r2(x), y1: top, y2: top + 9, class: on ? 'k-sig' : 'k-line', 'stroke-width': on ? 1.1 : 0.9 }, g);
        if (on) ring(g, x, top - 8, 3.4);
      }
    }
    var noteTexts = [];
    notes.forEach(function (nt) {
      var x = X(nt.at), y = top + (check_ ? 13 : 18), dy = (nt.row || 0) * (lab * 1.25 * lines + 3);
      if (nt.mark) ring(g, x, y, 3.4, nt.mark === 'hollow' ? 'hollow' : 'sig');
      var t = label(g, x, y + 7 + lab + dy, nt.text, 'k-t-cap ' + (nt.tone === 'ink' || nt.mark === 'hollow' ? 'is-ink' : nt.tone === 'muted' ? '' : 'is-sig'), lab, 'middle', F.Wu);
      if (!nt.row) noteTexts.push(t);
    });
    declutter(svg, noteTexts, lab * 1.25 * lines + 3);
    svg.setAttribute('aria-label', S.alt || (check_ ? 'Checks: ' + runs.replace(/\./g, 'ok ').replace(/1/g, 'fail ') : n + ' runs, ' + runs.replace(/\./g, '').length + ' fired'));
    return true;
  };

  /* axis — points on a line: reminders, deadlines, a day */
  SHAPES.axis = function (fig, S) {
    var F = frame(fig); if (!F.W) return false;
    var pts = S.points || [], lab = fsz(6.2, F), pad = S.pad != null ? S.pad : 14;
    var dom = S.domain || [0, Math.max(1, pts.length - 1)];
    var X = function (v, i) {
      if (S.scale === 'linear' || v != null) return pad + (v - dom[0]) / (dom[1] - dom[0]) * (F.Wu - 2 * pad);
      return pad + (pts.length < 2 ? 0 : i * (F.Wu - 2 * pad) / (pts.length - 1));
    };
    var hasAbove = pts.some(function (p) { return p.above; }) || (S.spans || []).some(function (s) { return s.label; }) || (S.lines || []).length;
    var Y = hasAbove ? 30 : 12, Hu = Y + 12 + lab * 2.6 + ((S.ticks || []).length ? lab + 6 : 0);
    var svg = svgFor(fig, F.Wu, Hu), g = sv('g', {}, svg);
    (S.spans || []).forEach(function (s) {
      var a = X(s.from), b = X(s.to);
      sv('rect', { x: r2(a), y: Y - 10, width: r2(b - a), height: 18, rx: 2, class: 'k-fill-tint k-sig', 'fill-opacity': .6, 'stroke-width': .8, 'stroke-dasharray': '3 3' }, g);
      if (s.label) label(g, a + 2, Y - 14, s.label, 'k-t-cap is-sig', lab, 'start');
    });
    var x0 = pad * .3, x1 = F.Wu - pad * .3;
    if (S.dotted) { var dA = X(S.dotted[0]), dB = X(S.dotted[1]); sv('line', { x1: r2(dA), x2: r2(dB), y1: Y, y2: Y, class: 'k-line', 'stroke-width': .9, 'stroke-dasharray': '.5 2.4', 'stroke-linecap': 'round' }, g); sv('line', { x1: r2(dB), x2: r2(x1), y1: Y, y2: Y, class: 'k-line', 'stroke-width': .9 }, g); if (dA > x0) sv('line', { x1: x0, x2: r2(dA), y1: Y, y2: Y, class: 'k-line', 'stroke-width': .9 }, g); }
    else sv('line', { x1: r2(x0), x2: r2(x1), y1: Y, y2: Y, class: 'k-line', 'stroke-width': .9 }, g);
    var tickTexts = [];
    (S.ticks || []).forEach(function (t) { var x = X(t.at); sv('line', { x1: r2(x), x2: r2(x), y1: Y - 3, y2: Y + 3, class: 'k-line', 'stroke-width': .8 }, g); tickTexts.push(label(g, x, Y + 10 + lab, t.label, 'k-t', lab, 'middle', F.Wu)); });
    var thin = tickTexts.length > 1 && (function () { try { var a = tickTexts[0].getBBox(), b = tickTexts[1].getBBox(); return a.x + a.width + 3 > b.x; } catch (e) { return false; } })();
    if (thin) tickTexts.forEach(function (t, i) { if (i % 2) t.remove(); });
    (S.lines || []).forEach(function (l) { var x = X(l.at); sv('line', { x1: r2(x), x2: r2(x), y1: Y - 16, y2: Y + 6, class: l.tone === 'signal' ? 'k-sig' : 'k-ink', 'stroke-width': 1.1 }, g); if (l.label) label(g, x, Y - 19, l.label, 'k-t-cap ' + (l.tone === 'signal' ? 'is-sig' : 'is-ink'), lab, 'middle', F.Wu); });
    var below = [], above = [];
    pts.forEach(function (p, i) {
      var x = X(p.at, i), k = p.kind || 'ring', r = 3.2 + (p.size || 0) * 1.1, cls = 'k-t-cap is-sig';
      if (k === 'start' || k === 'now') { sv('circle', { cx: r2(x), cy: Y, r: k === 'start' ? 3.8 : 2.8, class: 'k-fill-ink' }, g); cls = 'k-t-cap is-ink'; }
      else if (k === 'hollow') { ring(g, x, Y, 3.8, 'hollow'); cls = 'k-t-cap is-ink'; }
      else if (k === 'dot') { sv('circle', { cx: r2(x), cy: Y, r: 2, class: 'k-fill-sig' }, g); }
      else if (k === 'cross') { cross(g, x, Y, 7); }
      else ring(g, x, Y, r);
      if (p.above) above.push(label(g, x, Y - r - 6, p.above, 'k-t-cap' + (p.aboveTone === 'signal' ? ' is-sig' : ''), lab, 'middle', F.Wu));
      if (p.label) below.push(label(g, x, Y + 8 + lab, p.label, cls, lab, 'middle', F.Wu));
    });
    declutter(svg, below, lab * 1.3);
    above.forEach(function (t, i) { if (i && above[i - 1].parentNode) { try { var a = above[i - 1].getBBox(), b = t.getBBox(); if (a.x + a.width + 2 > b.x) t.remove(); } catch (e) { /* hidden */ } } });
    svg.setAttribute('aria-label', S.alt || pts.map(function (p) { return p.label; }).filter(Boolean).join(', '));
    return true;
  };

  /* line — a value over time; with a band it becomes "a number out of range" */
  SHAPES.line = function (fig, S) {
    var F = frame(fig); if (!F.W) return false;
    if (S.series) return lineSeries(fig, S, F);
    var v = S.values || [], lab = fsz(6.2, F), n = v.length; if (n < 2) { ST.errors.push('line needs 2+ values'); return false; }
    var band = S.band, lo = Math.min.apply(null, v.concat(band || [])), hi = Math.max.apply(null, v.concat(band || []));
    if (S.axis) lo = Math.min(lo, S.zero === false ? lo : 0);
    var span = (hi - lo) || 1; lo -= span * .12; hi += span * .12;
    var padL = S.axis ? 26 : 6, padR = 6, top = S.labels === false ? 8 : 8 + lab * 1.4, H = S.height || 70, bot = top + H;
    var Hu = bot + (S.x ? lab + 10 : 4) + (band ? lab + 4 : 0);
    var svg = svgFor(fig, F.Wu, Hu), g = sv('g', {}, svg);
    var X = function (i) { return padL + i * (F.Wu - padL - padR) / (n - 1); }, Y = function (y) { return bot - (y - lo) / (hi - lo) * H; };
    if (S.axis) { [0, .5, 1].forEach(function (f) { var val = lo + (hi - lo) * f, y = Y(val); sv('line', { x1: padL, x2: r2(F.Wu - padR), y1: r2(y), y2: r2(y), class: 'k-hair', 'stroke-width': .6 }, g); label(g, padL - 4, y + lab * .35, (S.fmt ? SL.fmt(val, S.fmt) : Math.round(val)) + (S.unit || ''), 'k-t', lab, 'end'); }); }
    if (band) {
      sv('rect', { x: padL, y: r2(Y(band[1])), width: r2(F.Wu - padL - padR), height: r2(Y(band[0]) - Y(band[1])), class: 'k-fill-calm' }, g);
      [band[0], band[1]].forEach(function (b) { sv('line', { x1: padL, x2: r2(F.Wu - padR), y1: r2(Y(b)), y2: r2(Y(b)), class: 'k-line', 'stroke-width': .7, 'stroke-dasharray': '3 3' }, g); });
      if (S.bandLabel !== false) label(g, padL + 2, Y(band[0]) + lab + 3, S.bandLabel || 'NORMAL RANGE', 'k-t-cap', lab, 'start');
    }
    var out = function (y) { return band ? (y > band[1] ? 1 : y < band[0] ? -1 : 0) : 0; };
    var events = [];
    for (var i = 0; i < n - 1; i++) {
      var a = v[i], b = v[i + 1], oa = out(a), ob = out(b);
      var segs = [[i, a, i + 1, b]];
      if (band && oa !== ob) { // split at the crossing(s)
        var cuts = [];
        [band[0], band[1]].forEach(function (lim) { if ((a - lim) * (b - lim) < 0) cuts.push(i + (lim - a) / (b - a)); });
        cuts.sort(); var pts = [[i, a]].concat(cuts.map(function (c) { return [c, a + (b - a) * (c - i)]; })).concat([[i + 1, b]]);
        segs = []; for (var k = 0; k < pts.length - 1; k++) segs.push([pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]]);
        cuts.forEach(function (c) { var y = a + (b - a) * (c - i); events.push({ at: c, y: y, leave: oa === 0 || (ob !== 0 && Math.abs(c - i) < 1e-9) ? true : false }); });
      }
      segs.forEach(function (s) {
        var mid = (s[1] + s[3]) / 2, o = out(mid);
        sv('line', { x1: r2(X(s[0])), y1: r2(Y(s[1])), x2: r2(X(s[2])), y2: r2(Y(s[3])), class: o ? 'k-sig' : 'k-ink2', 'stroke-width': o ? 1.6 : 1.1, 'stroke-linecap': 'round' }, g);
      });
    }
    if (band && S.labels !== false) {
      var state = out(v[0]) !== 0, firstLeave = null, firstReturn = null;
      events.forEach(function (e) { var isLeave = !state; state = !state; if (isLeave && !firstLeave) firstLeave = e; else if (!isLeave && firstLeave && !firstReturn) firstReturn = e; });
      var both = firstLeave && firstReturn, tl = null, tr = null;
      if (firstLeave) { ring(g, X(firstLeave.at), Y(firstLeave.y), 3.4); tl = label(g, X(firstLeave.at) + (both ? -4 : 0), top - lab * .6, S.leaveLabel || 'Leaves the range: fires', 'k-t-cap is-sig', lab, both ? 'end' : 'middle', F.Wu); }
      if (firstReturn) { ring(g, X(firstReturn.at), Y(firstReturn.y), 3.4, 'hollow'); tr = label(g, X(firstReturn.at) + (both ? 4 : 0), top - lab * .6, S.returnLabel || 'Returns: fires once', 'k-t-cap is-ink', lab, both ? 'start' : 'middle', F.Wu); }
      if (tl && tr) { try { // no room side by side: lift the leave label a row
        var a = tl.getBBox(), b = tr.getBBox(), sa = (/translate\(([-\d.]+)/.exec(tl.getAttribute('transform') || '') || [0, 0])[1] * 1, sb = (/translate\(([-\d.]+)/.exec(tr.getAttribute('transform') || '') || [0, 0])[1] * 1;
        if (a.x + sa + a.width + 3 > b.x + sb) { var rh = lab * 1.3; tl.setAttribute('transform', (tl.getAttribute('transform') || '') + ' translate(0,' + r2(-rh) + ')'); var vb = svg.getAttribute('viewBox').split(' ').map(Number); vb[1] -= rh; vb[3] += rh; svg.setAttribute('viewBox', vb.join(' ')); }
      } catch (e) { /* not rendered */ } }
    }
    if (S.points) v.forEach(function (y, i) { if (i !== S.key) sv('circle', { cx: r2(X(i)), cy: r2(Y(y)), r: 1.7, class: out(y) ? 'k-fill-sig' : 'k-fill-ink2' }, g); });
    if (S.key != null) { ring(g, X(S.key), Y(v[S.key]), 3.4); }
    if (S.x) S.x.forEach(function (t, i) { if (t) label(g, X(i), bot + lab + 6, t, 'k-t', lab, 'middle', F.Wu); });
    svg.setAttribute('aria-label', S.alt || ('Values: ' + v.join(', ') + (band ? '; normal range ' + band[0] + '–' + band[1] : '')));
    return true;
  };

  /* line with series — trends of a few related series; straight segments, visible observations, labels at the
     line ends (nudged apart, never overlapping). tone: key (orange) · ink · context (grey) */
  function lineSeries(fig, S, F) {
    var ser = S.series.filter(function (s) { return (s.values || []).length > 1; }), lab = fsz(6.2, F);
    if (!ser.length) { ST.errors.push('line series need 2+ values'); return false; }
    var n = Math.max.apply(null, ser.map(function (s) { return s.values.length; })), all = [].concat.apply([], ser.map(function (s) { return s.values; })).filter(function (v) { return v != null; });
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    if (S.zero !== false) lo = Math.min(lo, 0);
    var step = niceStep((hi - lo) || 1, 3); hi = Math.ceil(hi / step) * step; lo = Math.floor(lo / step) * step; if (hi === lo) hi = lo + step;
    var svg = svgFor(fig, F.Wu, 10), g = sv('g', {}, svg), padR = 0;
    var probe = ser.map(function (s) { return label(g, 0, 0, s.name || '', 'k-t-cap', lab, 'start'); });
    probe.forEach(function (t) { try { padR = Math.max(padR, t.getBBox().width); } catch (e) { padR = 60; } t.remove(); });
    padR += 10;
    var padL = S.axis === false ? 4 : 30, top = 6, H = S.height || 80, bot = top + H, Hu = bot + (S.x ? lab + 10 : 4);
    svg.setAttribute('viewBox', '0 0 ' + r2(F.Wu) + ' ' + r2(Hu));
    var X = function (i) { return padL + i * (F.Wu - padL - padR) / (n - 1); }, Y = function (y) { return bot - (y - lo) / (hi - lo) * H; };
    if (S.axis !== false) for (var tv = lo; tv <= hi + step * 1e-6; tv += step) (function (val) { var y = Y(val); sv('line', { x1: padL, x2: r2(F.Wu - padR), y1: r2(y), y2: r2(y), class: val === lo ? 'k-line' : 'k-hair', 'stroke-width': .6 }, g); label(g, padL - 4, y + lab * .35, SL.fmt(val, S.fmt) + (S.unit || ''), 'k-t', lab, 'end'); })(tv);
    var order = ser.map(function (s, i) { return i; }).sort(function (a, b) { var r = function (s) { return s.tone === 'key' ? 2 : s.tone === 'ink' ? 1 : 0; }; return r(ser[a]) - r(ser[b]); });
    var ends = [];
    order.forEach(function (k) {
      var s = ser[k], tone = s.tone || 'context', cls = tone === 'key' ? 'k-sig' : tone === 'ink' ? 'k-ink2' : 'k-line', fill = tone === 'key' ? 'k-fill-sig' : tone === 'ink' ? 'k-fill-ink2' : 'k-fill-rule';
      var d = '', last = null;
      s.values.forEach(function (v, i) { if (v == null) { last = null; return; } d += (last == null ? 'M' : 'L') + r2(X(i)) + ' ' + r2(Y(v)); last = i; });
      sv('path', { d: d, class: cls, 'stroke-width': tone === 'context' ? 1 : 1.4, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', fill: 'none' }, g);
      if (S.points !== false) s.values.forEach(function (v, i) { if (v != null) sv('circle', { cx: r2(X(i)), cy: r2(Y(v)), r: tone === 'context' ? 1.4 : 1.8, class: fill }, g); });
      var li = s.values.length - 1; while (li > 0 && s.values[li] == null) li--;
      ends.push({ y: Y(s.values[li]), x: X(li), name: s.name || '', cls: tone === 'key' ? 'k-t-cap is-sig' : tone === 'ink' ? 'k-t-cap is-ink' : 'k-t-cap' });
    });
    ends.sort(function (a, b) { return a.y - b.y; });
    var minGap = lab * 1.25; for (var i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < minGap) ends[i].y = ends[i - 1].y + minGap;
    ends.forEach(function (e) { label(g, e.x + 5, e.y + lab * .35, e.name, e.cls, lab, 'start'); });
    if (S.x) { var xs = []; S.x.forEach(function (t, i) { if (t) xs.push(label(g, X(i), bot + lab + 6, t, 'k-t', lab, 'middle', F.Wu)); }); thin(xs); }
    svg.setAttribute('aria-label', S.alt || ser.map(function (s) { return (s.name || 'series') + ': ' + s.values.join(', '); }).join('; '));
    return true;
  }

  /* shares — ranked shares with one key bar; null = too few to show */
  SHAPES.shares = function (fig, S) {
    var rows = S.rows || [], max = S.max || Math.max.apply(null, rows.map(function (r) { return r[1] || 0; }).concat([1]));
    var key = S.key == null ? 0 : S.key, unit = S.unit == null ? '%' : S.unit;
    var box = qs(':scope > .s-shares', fig); if (box) box.remove();
    box = el('div', { class: 's-shares', role: 'table', 'aria-label': S.alt || 'Shares' });
    rows.forEach(function (r, i) {
      var na = r[1] == null;
      box.appendChild(el('span', { class: 's-shares__l', role: 'cell', title: r[0], text: r[0] }));
      var t = el('span', { class: 's-shares__t' + (na ? ' is-na' : ''), 'aria-hidden': 'true' });
      if (!na) t.appendChild(el('i', { class: 's-shares__b' + (i === key ? ' is-key' : ''), style: 'width:' + r2(r[1] / max * 100) + '%' }));
      box.appendChild(t);
      box.appendChild(el('span', { class: 's-shares__v' + (na ? ' is-na' : ''), role: 'cell', text: na ? (S.na || 'n/a') : SL.fmt(r[1], S.fmt) + unit }));
    });
    fig.appendChild(box); return true;
  };

  /* flow — sources → code → store → event → agent → outcome.
     One grid, three rows (label · body · note); every body and every arrow sits on the body row's centre line. */
  function flowArrow() {
    var a = el('span', { class: 's-flow__arrow', 'aria-hidden': 'true' });
    a.appendChild(el('i')); a.insertAdjacentHTML('beforeend', '<svg viewBox="0 0 6 6"><path d="M0 0.4L6 3L0 5.6z" fill="currentColor"/></svg>');
    return a;
  }
  SHAPES.flow = function (fig, S) {
    var old = qs(':scope > .s-flow', fig); if (old) old.remove();
    var steps = S.steps || [];
    var hasHead = steps.some(function (st) { return st.label && st.kind !== 'agent'; });
    var hasFoot = steps.some(function (st) { return st.note || st.else || st.kind === 'agent'; });
    var rH = hasHead ? 1 : 0, rB = rH + 1, rF = rB + 1, rows = hasFoot ? rF : rB;
    var row = el('div', { class: 's-flow', style: 'grid-template-rows:repeat(' + rows + ',auto)' }), cols = [];
    steps.forEach(function (st, i) {
      if (i) {
        var prev = steps[i - 1], sig = st.kind === 'agent' || st.kind === 'chip' || prev.kind === 'event' || prev.kind === 'agent';
        var a = flowArrow(); a.style.color = 'var(' + (sig ? '--s-signal' : '--s-bar') + ')'; a.style.gridColumn = cols.length + 1; a.style.gridRow = rB;
        row.appendChild(a); cols.push('calc(34 * var(--u))');
      }
      var box = el('div', { class: 's-flow__step is-' + (st.kind || 'box'), style: 'grid-column:' + (cols.length + 1) + ';grid-row:1 / span ' + rows });
      cols.push(st.grow ? 'minmax(min-content, 1fr)' : 'auto');
      var head = null, body = el('div', { class: 's-flow__body' + (st.grow ? ' is-grow' : '') }), foot = null;
      if (hasHead) { head = el('div', { class: 's-flow__head' }); if (st.label && st.kind !== 'agent') head.appendChild(el('span', { class: 's-label', text: st.label })); }
      if (st.kind === 'list') { var items = st.items || [], l = el('div', { class: 's-flow__list' + (items.length > 1 ? ' is-multi' : '') }); items.forEach(function (t) { l.appendChild(el('span', { class: 's-flow__item', text: t })); }); body.appendChild(l); }
      else if (st.kind === 'code') { var pre = el('pre', { class: 's-code' }); pre.textContent = st.code || ''; body.appendChild(pre); }
      else if (st.kind === 'store') { body.appendChild(el('div', { class: 's-flow__store', 'aria-hidden': 'true', html: '<i></i><i></i>' })); }
      else if (st.kind === 'event') { var ev = el('div', { class: 's-flow__event' }); ev.appendChild(el('span', { class: 's-mono', text: st.text || '' })); if (st.tag) ev.appendChild(el('span', { class: 's-tag', text: st.tag })); body.appendChild(ev); }
      else if (st.kind === 'agent') { body.appendChild(el('i', { class: 's-flow__node', 'aria-hidden': 'true' })); }
      else if (st.kind === 'chip') { var c = el('span', { class: 's-flow__chip' + (st.tone === 'plain' ? ' is-plain' : ''), text: st.text || '' }); if (st.check) c.insertAdjacentHTML('beforeend', '<svg class="s-tick-mark" viewBox="0 0 10 10" aria-label="done"><path d="M1.5 5.2l2.4 2.4 4.6-5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'); body.appendChild(c); }
      else { body.appendChild(el('span', { class: 's-flow__item', text: st.text || '' })); }
      if (hasFoot) {
        foot = el('div', { class: 's-flow__foot' });
        if (st.kind === 'agent') foot.appendChild(el('span', { class: 's-label s-flow__nodelabel', text: st.label || 'AGENT' }));
        if (st.else) { var e2 = el('div', { class: 's-flow__else' }); e2.appendChild(el('span', { class: 's-mono', text: st.else.text || '' })); if (st.else.note) e2.appendChild(el('p', { class: 's-note', text: st.else.note })); foot.appendChild(e2); }
        if (st.note) foot.appendChild(el('p', { class: 's-note', text: st.note }));
      }
      [head, body, foot].forEach(function (n, k) { if (n) { n.style.gridRow = [rH, rB, rF][k]; box.appendChild(n); } });
      row.appendChild(box);
    });
    if (!steps.some(function (st) { return st.grow; })) row.style.justifyContent = 'start';
    row.style.gridTemplateColumns = cols.join(' ');
    fig.appendChild(row); highlightAll();
    row.classList.remove('is-stacked');
    var spill = [].slice.call(row.querySelectorAll(':scope > .s-flow__step')).some(function (st) {
      var r = st.getBoundingClientRect(); return [].slice.call(st.querySelectorAll(':scope > * > *')).some(function (c) { var q = c.getBoundingClientRect(); return q.right > r.right + 1 || q.left < r.left - 1; });
    });
    if (spill || row.scrollWidth > fig.clientWidth + 1) row.classList.add('is-stacked'); // does not fit: read top to bottom
    wireFlow(row);
    return true;
  };
  /* arrows run from box edge to box edge: absorb the empty track space a wide label or note leaves beside a body */
  function wireFlow(row) {
    var kids = [].slice.call(row.children), stacked = row.classList.contains('is-stacked');
    kids.forEach(function (a, i) {
      if (!a.classList.contains('s-flow__arrow')) return;
      a.style.marginLeft = a.style.marginRight = '';
      if (stacked) return;
      var A = kids[i - 1], B = kids[i + 1]; if (!A || !B) return;
      var ab = qs(':scope > .s-flow__body > *', A), bb = qs(':scope > .s-flow__body > *', B); if (!ab || !bb) return;
      var k = row.getBoundingClientRect().width / row.offsetWidth || 1;
      var gapL = (A.getBoundingClientRect().right - ab.getBoundingClientRect().right) / k, gapR = (bb.getBoundingClientRect().left - B.getBoundingClientRect().left) / k;
      if (gapL > 0.5) a.style.marginLeft = -gapL + 'px';
      if (gapR > 0.5) a.style.marginRight = -gapR + 'px';
    });
  }

  /* queue — a list with a cursor; items after it fire */
  SHAPES.queue = function (fig, S) {
    var old = qs(':scope > .s-queue', fig); if (old) old.remove();
    var q = el('div', { class: 's-queue' }), list = el('div', { class: 's-queue__list', 'aria-hidden': 'true' });
    var widths = [0.86, 0.66, 0.95, 0.76, 0.9, 0.7];
    for (var i = 0; i < (S.seen || 4); i++) list.appendChild(el('i', { class: 's-queue__row', style: 'width:' + widths[i % widths.length] * 100 + '%' }));
    var cur = el('div', { class: 's-queue__cursor' }); cur.appendChild(el('span', { class: 's-label', style: 'color:var(--s-ink)', text: S.cursor || 'CURSOR' })); list.appendChild(cur);
    for (var j = 0; j < (S.fresh || 2); j++) list.appendChild(el('i', { class: 's-queue__row is-new', style: 'width:' + (j % 2 ? 72 : 92) + '%' }));
    q.appendChild(list);
    var side = el('div', { class: 's-queue__side' });
    if (S.note) side.appendChild(el('p', { class: 's-note', text: S.note }));
    if (S.result) { var o = el('div', { class: 's-queue__out' }); o.appendChild(el('span', { class: 's-label', text: S.resultLabel || 'AFTER THE CURSOR' })); o.insertAdjacentHTML('beforeend', '<span style="color:var(--s-signal);display:flex">' + arrowSvg() + '</span>'); var ev = el('div', { class: 's-flow__event' }); ev.appendChild(el('span', { class: 's-mono', text: S.result })); o.appendChild(ev); side.appendChild(o); }
    q.appendChild(side); fig.appendChild(q); return true;
  };

  /* diff — the fields you track, last look vs this look. One grid: labels row, cards row; ≠ sits on the cards' centre. */
  SHAPES.diff = function (fig, S) {
    var old = qs(':scope > .s-diff', fig); if (old) old.remove();
    var a = S.before || {}, b = S.after || {}, prev = {}, changed = false;
    (a.rows || []).forEach(function (r) { prev[r[0]] = r[1]; });
    function card(side, isAfter) {
      var dl = el('dl'), ch = false;
      (side.rows || []).forEach(function (r) { var c = isAfter && prev[r[0]] !== r[1]; if (c) ch = true; dl.appendChild(el('dt', { text: r[0] })); dl.appendChild(el('dd', { class: c ? 'is-changed' : null, text: r[1] })); });
      var c = el('div', { class: 's-diff__card' + (ch ? ' is-changed' : '') }); c.appendChild(dl); return { node: c, changed: ch };
    }
    var d = el('div', { class: 's-diff' }), A = card(a, false), B = card(b, true);
    changed = B.changed;
    var la = el('span', { class: 's-label s-diff__la', text: a.label || '' }), lb = el('span', { class: 's-label s-diff__lb' + (changed ? ' is-changed-label' : ''), text: b.label || '' });
    A.node.classList.add('s-diff__a'); B.node.classList.add('s-diff__b');
    var ne = el('span', { class: 's-diff__ne', 'aria-label': changed ? 'changed' : 'unchanged', text: changed ? '\u2260' : '=' });
    [la, lb, A.node, ne, B.node].forEach(function (n) { d.appendChild(n); });
    fig.appendChild(d); return true;
  };

  /* match — two systems that should agree; each missing record fires once. One grid: every record is one row,
     so the two cells and their link share a centre line. */
  SHAPES.match = function (fig, S) {
    var old = qs(':scope > .s-match', fig); if (old) old.remove();
    var L = S.left || {}, R = S.right || {}, n = Math.max((L.rows || []).length, (R.rows || []).length);
    var m = el('div', { class: 's-match', style: 'grid-template-rows:auto calc(6 * var(--u)) repeat(' + n + ', calc(17 * var(--u))) calc(6 * var(--u))' });
    function put(node, r, c, extra) { node.style.gridRow = r; node.style.gridColumn = c; if (extra) node.className += ' ' + extra; m.appendChild(node); return node; }
    put(el('span', { class: 's-label', text: L.label || '' }), 1, 1);
    put(el('span', { class: 's-label', text: R.label || '' }), 1, 3);
    put(el('span', { class: 's-match__col', 'aria-hidden': 'true' }), '2 / span ' + (n + 2), 1);
    put(el('span', { class: 's-match__col', 'aria-hidden': 'true' }), '2 / span ' + (n + 2), 3);
    for (var i = 0; i < n; i++) {
      var lv = (L.rows || [])[i], rv = (R.rows || [])[i], ok = lv != null && rv != null && String(lv) === String(rv);
      put(el('div', { class: 's-match__row' + (lv == null ? ' is-missing' : ''), text: lv == null ? '\u2014' : lv }), i + 3, 1);
      put(el('div', { class: 's-match__row' + (rv == null ? ' is-missing' : ''), text: rv == null ? '\u2014' : rv }), i + 3, 3);
      put(el('div', { class: 's-match__link', 'aria-hidden': 'true', html: ok ? '<svg viewBox="0 0 70 10" preserveAspectRatio="none"><line x1="0" y1="5" x2="70" y2="5" stroke="var(--s-line)" stroke-width="1" vector-effect="non-scaling-stroke"/></svg>'
        : '<svg viewBox="0 0 70 10" preserveAspectRatio="xMinYMid meet"><line x1="0" y1="5" x2="44" y2="5" stroke="var(--s-signal)" stroke-width="1" stroke-dasharray="3 3"/><text x="48" y="8.5" font-size="9" font-weight="700" fill="var(--s-signal)" font-family="var(--s-f-sans)">?</text><circle cx="62" cy="5" r="3.4" fill="var(--s-card)" stroke="var(--s-signal)"/><circle cx="62" cy="5" r="1.4" fill="var(--s-signal)"/></svg>' }), i + 3, 2);
    }
    fig.appendChild(m); return true;
  };

  /* stairs — stages that take on more autonomy */
  SHAPES.stairs = function (fig, S) {
    var old = qs(':scope > .s-stairs', fig); if (old) old.remove();
    var steps = S.steps || [], n = steps.length, act = S.active;
    var w = el('div', { class: 's-stairs', 'data-rise': S.rise || 22 }), grid = el('div', { class: 's-stairs__grid', style: '--n:' + n });
    steps.forEach(function (s, i) { var b = el('div', { class: 's-stairs__step' + (i === act ? ' is-active' : ''), style: '--i:' + i }); b.appendChild(el('b', { text: s[0] })); if (s[1]) b.appendChild(el('span', { text: s[1] })); grid.appendChild(b); });
    w.appendChild(grid); fig.appendChild(w); wireStairs(w);
    return true;
  };
  function wireStairs(w) {
    var old = qs(':scope > svg', w); if (old) old.remove();
    var grid = qs('.s-stairs__grid', w), boxes = qsa('.s-stairs__step', w); if (!boxes.length || !w.clientWidth) return;
    var n = boxes.length, u = uPx(w), W = w.clientWidth, gap = 7 * u, rise = parseFloat(w.getAttribute('data-rise')) * u;
    var static_ = getComputedStyle(boxes[0]).position === 'static';
    if (static_) { grid.style.height = ''; boxes.forEach(function (b) { b.style.left = b.style.top = b.style.width = ''; }); return; }
    var bw = Math.min((W - gap * (n - 1)) / n, 150 * u), step = n > 1 ? (W - bw) / (n - 1) : 0, bh = 0;
    boxes.forEach(function (b) { b.style.width = bw + 'px'; bh = Math.max(bh, b.offsetHeight); });
    grid.style.height = (bh + rise * (n - 1)) + 'px';
    boxes.forEach(function (b, i) { b.style.left = (i * step) + 'px'; b.style.top = ((n - 1 - i) * rise + (bh - b.offsetHeight)) + 'px'; });
    var s = sv('svg', { 'aria-hidden': 'true', viewBox: '0 0 ' + W + ' ' + grid.offsetHeight, preserveAspectRatio: 'none' }); w.appendChild(s);
    for (var i = 0; i < n - 1; i++) {
      var a = boxes[i], b = boxes[i + 1];
      var x1 = a.offsetLeft + a.offsetWidth, y1 = a.offsetTop + 6 * u, x2 = b.offsetLeft, y2 = b.offsetTop + b.offsetHeight - 6 * u;
      if (x2 <= x1) { x1 = a.offsetLeft + a.offsetWidth * .7; y1 = a.offsetTop; x2 = x1; y2 = b.offsetTop + b.offsetHeight; }
      sv('path', { d: 'M' + r2(x1) + ' ' + r2(y1) + 'L' + r2(x2) + ' ' + r2(y2), fill: 'none', stroke: 'var(--s-rule)', 'stroke-width': 1 }, s);
    }
  }

  /* fanout — one thing split into stages, or copied per group */
  SHAPES.fanout = function (fig, S) {
    var old = qs(':scope > .s-fanout', fig); if (old) old.remove();
    var f = el('div', { class: 's-fanout' + (S.tone === 'signal' ? ' is-signal' : '') });
    f.appendChild(el('span', { class: 's-fanout__from', text: S.from || '' }));
    var wire = el('div', { class: 's-fanout__wire', 'aria-hidden': 'true' }); f.appendChild(wire);
    var cols = S.cols || 1; if (fig.clientWidth && fig.clientWidth / uPx(fig) < 300) cols = Math.min(cols, 2);
    var to = el('div', { class: 's-fanout__to', style: '--cols:' + cols }); (S.to || []).forEach(function (t) { to.appendChild(el('span', { text: t, title: t })); }); f.appendChild(to);
    fig.appendChild(f); requestAnimationFrame(function () { wireFan(f); }); return true;
  };
  function wireFan(f) {
    var wire = qs('.s-fanout__wire', f), from = qs('.s-fanout__from', f), kids = qsa('.s-fanout__to > span', f); if (!wire || !wire.clientWidth) return;
    wire.innerHTML = ''; var o = wire.getBoundingClientRect(), sc = o.width / wire.offsetWidth || 1, W = wire.offsetWidth, H = wire.offsetHeight;
    var s = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, preserveAspectRatio: 'none' }); wire.appendChild(s);
    var fr = from.getBoundingClientRect(), y0 = (fr.top + fr.height / 2 - o.top) / sc;
    var rowsY = []; kids.forEach(function (k) { var r = k.getBoundingClientRect(), y = (r.top + r.height / 2 - o.top) / sc; if (rowsY.every(function (v) { return Math.abs(v - y) > 1; })) rowsY.push(y); });
    var stroke = f.classList.contains('is-signal') ? 'var(--s-signal)' : 'var(--s-rule)';
    sv('path', { d: 'M0 ' + r2(y0) + 'H' + r2(W / 2), fill: 'none', stroke: stroke, 'stroke-width': 1 }, s);
    if (rowsY.length) sv('path', { d: 'M' + r2(W / 2) + ' ' + r2(Math.min.apply(null, rowsY.concat([y0]))) + 'V' + r2(Math.max.apply(null, rowsY.concat([y0]))), fill: 'none', stroke: stroke, 'stroke-width': 1 }, s);
    rowsY.forEach(function (y) { sv('path', { d: 'M' + r2(W / 2) + ' ' + r2(y) + 'H' + W, fill: 'none', stroke: stroke, 'stroke-width': 1 }, s); });
  }

  /* ---------- decision-ready shapes (method: references/decision-method.md) ----------
     columns · variance · tablegraph · bullet · heatmap. Bars start at zero; orange marks the key bar or what
     missed its target; grey is context; the outlined bar is the comparison period. */
  function sgn(v, f) { if (v == null || isNaN(v)) return 'n/a'; return (v > 0 ? '+' : v < 0 ? '\u2212' : '') + SL.fmt(Math.abs(v), f); }
  function pct(v, d) { if (v == null || !isFinite(v)) return 'n/a'; return Math.abs(v) < 1e-12 ? (0).toFixed(d) + '%' : v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }) + '%'; }
  function spct(v, d) { if (v == null || !isFinite(v)) return 'n/a'; return (v > 0 ? '+' : v < 0 ? '\u2212' : '') + pct(Math.abs(v), d); }
  function niceStep(span, n) { var raw = span / (n || 3), p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), m = raw / p; return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p; }
  function overlapsX(a, b) { try { var p = a.getBBox(), q = b.getBBox(); return p.x + p.width + 2 > q.x && q.x + q.width + 2 > p.x; } catch (e) { return false; } }
  function thin(texts) { // crowded axis labels: keep every other one
    for (var i = 1; i < texts.length; i++) if (overlapsX(texts[i - 1], texts[i])) { texts.forEach(function (t, k) { if (k % 2) t.remove(); }); return; }
  }
  function legend(g, items, lab, x0, y) { // [[kind, text]] kind: bar | prior | sig
    var x = x0;
    items.forEach(function (it) {
      var s = lab * .95;
      sv('rect', { x: r2(x), y: r2(y - s + 1), width: r2(s), height: r2(s), rx: .6, class: it[0] === 'prior' ? 'k-line k-fill-bg' : it[0] === 'sig' ? 'k-fill-sig' : 'k-fill-bar', 'stroke-width': .8 }, g);
      var t = label(g, x + s + 3, y, it[1], 'k-t', lab, 'start');
      var w = 40; try { w = t.getBBox().width; } catch (e) { /* hidden */ }
      x += s + 3 + w + 10;
    });
  }

  /* columns — a few periods, zero-based, current beside its matched prior */
  SHAPES.columns = function (fig, S) {
    var F = frame(fig); if (!F.W) return false;
    var ser = S.series || [{ name: S.name || '', values: S.values || [] }], cur = null, pri = null;
    ser.forEach(function (s) { if (s.role === 'prior') pri = pri || s; else cur = cur || s; });
    if (!cur || !(cur.values || []).length) { ST.errors.push('columns needs a series with values'); return false; }
    var x = S.x || [], n = cur.values.length, lab = fsz(6.2, F), unit = S.unit || '';
    var all = cur.values.concat(pri ? pri.values : []).filter(function (v) { return v != null; });
    if (Math.min.apply(null, all.concat([0])) < 0) { ST.errors.push('columns are zero-based amounts; use variance for signed changes'); return false; }
    var max = (Math.max.apply(null, all.concat([0])) || 1) * 1.04, step = niceStep(max / 1.04, 2);
    if (S.axis) max = Math.max(max, Math.ceil(max / 1.04 / step) * step);
    var legH = pri ? lab * 1.3 + 8 : 0, valH = S.labels === false ? 3 : lab + 6, H = S.height || 90;
    var padL = S.axis ? 30 : 2, padR = 2, top = legH + valH, bot = top + H, Hu = bot + lab + 9;
    var svg = svgFor(fig, F.Wu, Hu), g = sv('g', {}, svg);
    var gw = (F.Wu - padL - padR) / n, bw = Math.min(gw * (pri ? .36 : .58), pri ? 22 : 30), gap = pri ? Math.min(2.4, gw * .06) : 0;
    var Y = function (v) { return bot - v / max * H; };
    if (S.axis) for (var tv = step; tv <= max + 1e-9; tv += step) (function (v) { var y = Y(v); sv('line', { x1: padL, x2: r2(F.Wu - padR), y1: r2(y), y2: r2(y), class: 'k-hair', 'stroke-width': .6 }, g); label(g, padL - 4, y + lab * .35, SL.fmt(v, S.fmt) + unit, 'k-t', lab, 'end'); })(tv);
    var key = S.key, vals = [], xs = [];
    for (var i = 0; i < n; i++) {
      var cx = padL + gw * (i + .5), v = cur.values[i], p = pri ? pri.values[i] : null;
      var xc = pri ? cx + gap / 2 : cx - bw / 2, xp = cx - gap / 2 - bw;
      if (p != null) sv('rect', { x: r2(xp), y: r2(Y(p)), width: r2(bw), height: r2(bot - Y(p)), class: 'k-line k-fill-bg', 'stroke-width': .8 }, g);
      if (v != null) sv('rect', { x: r2(xc), y: r2(Y(v)), width: r2(bw), height: r2(bot - Y(v)), class: i === key ? 'k-fill-sig' : 'k-fill-bar' }, g);
      if (v != null && S.labels !== false) vals.push({ t: label(g, xc + bw / 2, Math.min(Y(v), p != null ? Y(p) : Y(v)) - 3, SL.fmt(v, S.fmt) + unit, i === key ? 'k-t-cap is-sig' : 'k-t k-t-ink', lab, 'middle', F.Wu), key: i === key });
      if (x[i]) xs.push(label(g, cx, bot + lab + 5, x[i], 'k-t', lab, 'middle', F.Wu));
    }
    sv('line', { x1: padL, x2: r2(F.Wu - padR), y1: bot, y2: bot, class: 'k-ink2', 'stroke-width': .8 }, g); // the zero line
    for (var j = 1; j < vals.length; j++) if (overlapsX(vals[j - 1].t, vals[j].t)) { vals.forEach(function (o) { if (!o.key) o.t.remove(); }); break; }
    thin(xs);
    if (pri) legend(g, [['bar', cur.name || 'Current'], ['prior', pri.name || 'Prior']], lab, padL, lab);
    svg.setAttribute('aria-label', S.alt || ((cur.name || 'Values') + ': ' + cur.values.map(function (v, i) { return (x[i] ? x[i] + ' ' : '') + v; }).join(', ') + (pri ? '; ' + (pri.name || 'prior') + ': ' + pri.values.join(', ') : '')));
    return true;
  };

  /* variance — contribution to a change: zero line, one bar per component, parts reconcile to the total */
  SHAPES.variance = function (fig, S) {
    var old = qs(':scope > .s-var', fig); if (old) old.remove();
    var rows = (S.rows || []).map(function (r) { return r.length > 2 ? { l: r[0], d: r[2] - r[1] } : { l: r[0], d: r[1] }; });
    if (!rows.length) return false;
    var ds = rows.map(function (r) { return r.d; }), sum = ds.reduce(function (a, b) { return a + b; }, 0);
    var total = S.total != null ? S.total : sum, unit = S.unit || '', dg = S.digits == null ? 1 : S.digits;
    var lo = Math.min(0, Math.min.apply(null, ds)), hi = Math.max(0, Math.max.apply(null, ds)), span = (hi - lo) || 1, z = -lo / span * 100;
    var same = ds.every(function (d) { return d >= 0; }) || ds.every(function (d) { return d <= 0; });
    var key = S.key; if (key == null) { var m = -1; ds.forEach(function (d, i) { if (Math.abs(d) > m) { m = Math.abs(d); key = i; } }); }
    var box = el('div', { class: 's-var', role: 'table', 'aria-label': S.alt || ('Change by component, total ' + sgn(total, S.fmt) + unit) });
    rows.forEach(function (r, i) {
      box.appendChild(el('span', { class: 's-var__l', role: 'cell', title: r.l, text: r.l }));
      var t = el('span', { class: 's-var__t', style: '--z:' + r2(z) + '%', 'aria-hidden': 'true' });
      t.appendChild(el('i', { class: 's-var__b' + (i === key ? ' is-key' : '') + (r.d < 0 ? ' is-neg' : ''), style: 'left:' + r2(r.d < 0 ? z + r.d / span * 100 : z) + '%;width:' + r2(Math.abs(r.d) / span * 100) + '%' }));
      box.appendChild(t);
      box.appendChild(el('span', { class: 's-var__v', role: 'cell', text: sgn(r.d, S.fmt) + unit + (same && S.share !== false && total ? ' \u00b7 ' + pct(r.d / total * 100, dg) : '') }));
    });
    box.appendChild(el('span', { class: 's-var__l is-total', role: 'cell', text: S.totalLabel || 'Total change' }));
    box.appendChild(el('span', { class: 's-var__t is-total', style: '--z:' + r2(z) + '%', 'aria-hidden': 'true' }));
    box.appendChild(el('span', { class: 's-var__v is-total', role: 'cell', text: sgn(total, S.fmt) + unit + (same && S.share !== false ? ' \u00b7 100%' : '') }));
    fig.appendChild(box); return true;
  };

  /* tablegraph — exact breakdown with movement: value (with bar) · share · prior · change · change % · contribution */
  SHAPES.tablegraph = function (fig, S) {
    var old = qs(':scope > .s-table', fig); if (old) old.remove();
    var rows = S.rows || [], f = S.fmt, unit = S.unit || '', dg = S.digits == null ? 1 : S.digits, key = S.key == null ? 0 : S.key;
    var tot = 0, totP = 0, hasP = rows.every(function (r) { return r[2] != null; });
    rows.forEach(function (r) { tot += r[1] || 0; totP += r[2] || 0; });
    var dTot = tot - totP, max = Math.max.apply(null, rows.map(function (r) { return r[1] || 0; }).concat([1]));
    var ds = rows.map(function (r) { return r[2] == null ? null : r[1] - r[2]; });
    var same = hasP && (ds.every(function (d) { return d >= 0; }) || ds.every(function (d) { return d <= 0; }));
    var wrap = el('div', { class: 's-table' }), t = el('table', { class: 's-tab s-tablegraph' });
    if (S.alt) t.setAttribute('aria-label', S.alt);
    var head = el('tr'); [S.labelHead || '', S.valueLabel || 'Value', 'Share', S.priorLabel || 'Prior', 'Change', 'Change %', 'Contribution'].forEach(function (h, i) { head.appendChild(el('th', { scope: 'col', class: i ? 'is-num' : null, text: h })); });
    var th = el('thead'); th.appendChild(head); t.appendChild(th);
    var tb = el('tbody');
    function row(lbl, v, p, isKey, isTot) {
      var tr = el('tr', { class: isTot ? 'is-total' : null }), d = p == null ? null : v - p;
      tr.appendChild(el('th', { scope: 'row', text: lbl }));
      var vc = el('td', { class: 'is-num s-tablegraph__v' }), vw = el('div'); vc.appendChild(vw);
      if (!isTot) { var bar = el('span', { class: 's-tablegraph__t', 'aria-hidden': 'true' }); bar.appendChild(el('i', { class: 's-tablegraph__b' + (isKey ? ' is-key' : ''), style: 'width:' + r2(v / max * 100) + '%' })); vw.appendChild(bar); }
      vw.appendChild(el('span', { text: SL.fmt(v, f) + unit })); tr.appendChild(vc);
      tr.appendChild(el('td', { class: 'is-num', text: pct(tot ? v / tot * 100 : null, dg) }));
      tr.appendChild(el('td', { class: 'is-num', text: p == null ? 'n/a' : SL.fmt(p, f) + unit }));
      tr.appendChild(el('td', { class: 'is-num', text: d == null ? 'n/a' : sgn(d, f) + unit }));
      tr.appendChild(el('td', { class: 'is-num', text: d == null || !p ? 'n/a' : spct(d / p * 100, dg) }));
      tr.appendChild(el('td', { class: 'is-num', text: !same || d == null || !dTot ? '\u2014' : pct(isTot ? 100 : d / dTot * 100, dg) }));
      tb.appendChild(tr);
    }
    rows.forEach(function (r, i) { row(r[0], r[1], r[2], i === key, false); });
    if (S.total !== false) row(S.totalLabel || 'Total', tot, hasP ? totP : null, false, true);
    t.appendChild(tb); wrap.appendChild(t); fig.appendChild(wrap); return true;
  };

  /* bullet — actual against target: calm band = normal range, ink tick = target, bar orange when it misses */
  SHAPES.bullet = function (fig, S) {
    var old = qs(':scope > .s-bullet', fig); if (old) old.remove();
    var box = el('div', { class: 's-bullet', role: 'table', 'aria-label': S.alt || 'Actual against target' });
    (S.rows || []).forEach(function (r) {
      var f = r.fmt || S.fmt, unit = r.unit != null ? r.unit : (S.unit || ''), band = r.band || null;
      var max = r.max || S.max || Math.max(r.value || 0, r.target || 0, band ? band[1] : 0) * 1.2 || 1;
      var miss = r.target != null && (r.better === 'lower' ? r.value > r.target : r.value < r.target);
      box.appendChild(el('span', { class: 's-bullet__l', role: 'cell', text: r.label }));
      var t = el('span', { class: 's-bullet__t', 'aria-hidden': 'true' });
      if (band) t.appendChild(el('i', { class: 's-bullet__band', style: 'left:' + r2(band[0] / max * 100) + '%;width:' + r2((band[1] - band[0]) / max * 100) + '%' }));
      t.appendChild(el('i', { class: 's-bullet__b' + (miss ? ' is-miss' : ''), style: 'width:' + r2(Math.min(1, (r.value || 0) / max) * 100) + '%' }));
      if (r.target != null) t.appendChild(el('i', { class: 's-bullet__target', style: 'left:' + r2(r.target / max * 100) + '%' }));
      box.appendChild(t);
      box.appendChild(el('span', { class: 's-bullet__v' + (miss ? ' is-miss' : ''), role: 'cell', text: SL.fmt(r.value, f) + unit + (r.target != null ? ' \u00b7 target ' + SL.fmt(r.target, f) + unit : '') }));
    });
    fig.appendChild(box); return true;
  };

  /* heatmap — two ordered dimensions (day × hour); grey by intensity, orange at or over the threshold */
  SHAPES.heatmap = function (fig, S) {
    var F = frame(fig); if (!F.W) return false;
    var rows = S.rows || [], cols = S.cols || [], V = S.values || [], lab = fsz(6.2, F), nr = rows.length, nc = cols.length;
    if (!nr || !nc) return false;
    var flat = [].concat.apply([], V).filter(function (v) { return v != null; }), max = Math.max.apply(null, flat.concat([1])), thr = S.threshold;
    var svg = svgFor(fig, F.Wu, 10), g = sv('g', {}, svg), padL = 0;
    var rl = rows.map(function (r) { return label(g, 0, 0, r, 'k-t', lab, 'end'); });
    rl.forEach(function (t) { try { padL = Math.max(padL, t.getBBox().width); } catch (e) { padL = Math.max(padL, 24); } });
    padL += 6;
    var top = lab + 6, cw = (F.Wu - padL) / nc, ch = S.rowHeight || Math.max(lab * 1.5, Math.min(cw, 14)), gp = Math.min(.8, cw * .08);
    var hot = null;
    for (var i = 0; i < nr; i++) {
      var y = top + i * ch; rl[i].setAttribute('x', r2(padL - 6)); rl[i].setAttribute('y', r2(y + ch / 2 + lab * .35)); qsa('tspan', rl[i]).forEach(function (s) { s.setAttribute('x', r2(padL - 6)); });
      for (var j = 0; j < nc; j++) {
        var v = (V[i] || [])[j]; if (v == null) { sv('rect', { x: r2(padL + j * cw + gp / 2), y: r2(y + gp / 2), width: r2(cw - gp), height: r2(ch - gp), class: 'k-hair k-fill-bg', 'stroke-width': .5 }, g); continue; }
        var over = thr != null && v >= thr;
        sv('rect', { x: r2(padL + j * cw + gp / 2), y: r2(y + gp / 2), width: r2(cw - gp), height: r2(ch - gp), rx: .6, class: over ? 'k-fill-sig' : 'k-fill-bar', 'fill-opacity': over ? r2(.55 + .45 * v / max) : r2(.06 + .74 * v / max) }, g);
        if (!hot || v > hot.v) hot = { v: v, r: rows[i], c: cols[j] };
      }
    }
    var cl = []; cols.forEach(function (c, j) { if (c !== '' && c != null) cl.push(label(g, padL + (j + .5) * cw, lab + 1, c, 'k-t', lab, 'middle', F.Wu)); }); thin(cl);
    var ly = top + nr * ch + lab + 8, lx = padL;
    label(g, lx, ly, S.lowLabel || 'Low', 'k-t', lab, 'start'); lx += lab * 2.2;
    for (var k = 0; k < 5; k++) sv('rect', { x: r2(lx + k * (lab * 1.3)), y: r2(ly - lab + 1), width: r2(lab * 1.2), height: r2(lab), class: 'k-fill-bar', 'fill-opacity': r2(.06 + .74 * (k + 1) / 5) }, g);
    lx += 5 * lab * 1.3 + 3; label(g, lx, ly, S.highLabel || 'High', 'k-t', lab, 'start');
    if (thr != null) { lx += lab * 3.4; sv('rect', { x: r2(lx), y: r2(ly - lab + 1), width: r2(lab * 1.2), height: r2(lab), class: 'k-fill-sig' }, g); label(g, lx + lab * 1.6, ly, S.thresholdLabel || ('At or over ' + SL.fmt(thr, S.fmt)), 'k-t', lab, 'start', F.Wu); }
    svg.setAttribute('viewBox', '0 0 ' + r2(F.Wu) + ' ' + r2(ly + 4));
    svg.setAttribute('aria-label', S.alt || (nr + ' by ' + nc + ' grid' + (hot ? '; highest ' + hot.v + ' at ' + hot.r + ' ' + hot.c : '')));
    return true;
  };

  /* the evidence ladder, decision kinds and trust gaps (page components) */
  var LEVELS = { confirmed: [4, 'Confirmed', 'Direct evidence connects the population, the timing and the mechanism'], likely: [3, 'Likely', 'Strong support; causality not proven'],
    suspected: [2, 'Suspected', 'A pattern worth investigating'], correlated: [1, 'Correlated, not causal', 'Two movements overlap with no proven mechanism'], unknown: [0, 'Unknown', 'The available source cannot answer it'] };
  var KINDS = { approve: 'Approve', investigate: 'Investigate', defer: 'Defer', reject: 'Reject', act: 'Act' };
  function evidence() {
    qsa('.s-claim[data-evidence]').forEach(function (c) {
      if (qs(':scope > .s-claim__pips', c)) return;
      var L = LEVELS[c.getAttribute('data-evidence')]; if (!L) { ST.errors.push('unknown evidence level "' + c.getAttribute('data-evidence') + '"'); return; }
      if (!c.textContent.trim()) c.textContent = L[1];
      var p = el('span', { class: 's-claim__pips', 'aria-hidden': 'true' }); for (var i = 0; i < 4; i++) p.appendChild(el('i', { class: i < L[0] ? 'is-on' : null }));
      c.insertBefore(p, c.firstChild); c.setAttribute('title', L[2]);
    });
    qsa('.s-decision[data-kind]').forEach(function (d) {
      if (qs(':scope > .s-decision__kind', d)) return;
      var k = KINDS[d.getAttribute('data-kind')]; if (!k) { ST.errors.push('unknown decision kind'); return; }
      d.insertBefore(el('span', { class: 's-decision__kind', text: k }), d.firstChild);
    });
    qsa('.s-trust dd, .s-method dd, .s-decision dd, .s-contract td').forEach(function (n) { if (/^\s*(not captured|not set)\b/i.test(n.textContent)) n.classList.add('is-gap'); });
  }

  function drawAll() {
    var figs = qsa('.s-shape[data-shape]'); ST.shapes = figs.length; ST.drawn = 0;
    figs.forEach(function (fig) {
      var name = fig.getAttribute('data-shape'), fn = SHAPES[name];
      if (!fn) { ST.errors.push('unknown shape "' + name + '"'); return; }
      var S = fig.__spec || (fig.__spec = spec(fig)); if (!S) return;
      try { if (fn(fig, S) !== false) { ST.drawn++; fig.setAttribute('data-drawn', ''); } }
      catch (e) { ST.errors.push(name + ': ' + e.message); }
    });
  }

  /* ---------- deck frame ---------- */
  function deck() {
    var d = qs('.s-deck'); if (!d) return;
    var foot = d.getAttribute('data-runfoot'), mode = root.getAttribute('data-mode');
    var modeTxt = (root.getAttribute('data-doc') === 'report' ? { published: 'Published figures', snapshot: 'Snapshot', live: 'Live data', sample: 'Sample data', synthetic: 'Synthetic data' } : { sample: 'Sample data', synthetic: 'Synthetic data' })[mode];
    qsa('.s-slide', d).forEach(function (s, i) {
      if (foot && !s.classList.contains('is-cover') && !s.hasAttribute('data-no-foot') && !qs(':scope > .s-runfoot', s))
        s.appendChild(el('div', { class: 's-runfoot', 'data-decor': '', html: '<span></span>' })).firstChild.textContent = foot + (modeTxt ? ' \u00b7 ' + modeTxt : '');
      if (!s.parentNode.classList.contains('s-slide-frame')) { var f = el('div', { class: 's-slide-frame' }); s.parentNode.insertBefore(f, s); f.appendChild(s); }
      s.setAttribute('data-n', i + 1);
    });
    var nav = el('nav', { class: 's-deck-nav s-noprint', 'aria-label': 'Deck' });
    var count = el('span', { class: 's-count', 'aria-live': 'polite' }); nav.appendChild(count); nav.appendChild(themeToggle()); doc.body.appendChild(nav);
    function fit() {
      var k = Math.min(1.6, (window.innerWidth - (window.innerWidth < 700 ? 16 : 64)) / 1280);
      qsa('.s-slide-frame', d).forEach(function (f) { f.style.width = 1280 * k + 'px'; f.style.height = 720 * k + 'px'; f.firstChild.style.transform = 'scale(' + k + ')'; });
    }
    fit(); window.addEventListener('resize', fit);
    var frames = qsa('.s-slide-frame', d);
    function current() { var c = 0, mid = window.innerHeight / 2; frames.forEach(function (f, i) { if (f.getBoundingClientRect().top < mid) c = i; }); return c; }
    function show() { count.textContent = (current() + 1) + ' / ' + frames.length; }
    window.addEventListener('scroll', show, { passive: true }); show();
    doc.addEventListener('keydown', function (e) {
      if (e.target.closest && e.target.closest('input,textarea,[contenteditable]')) return;
      var c = current(), t = null;
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].indexOf(e.key) >= 0) t = Math.min(frames.length - 1, c + 1);
      if (['ArrowLeft', 'ArrowUp', 'PageUp'].indexOf(e.key) >= 0) t = Math.max(0, c - 1);
      if (t != null) { e.preventDefault(); frames[t].scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }
    });
    var go = parseInt(params.get('slide'), 10); if (go && frames[go - 1]) frames[go - 1].scrollIntoView({ block: 'center' });
  }

  /* ---------- slides embedded in a page: .s-embed > .s-slide, scaled to the container ---------- */
  function embeds() {
    qsa('.s-embed').forEach(function (e) {
      var sl = qs(':scope > .s-slide', e); if (!sl) return;
      var k = e.clientWidth / 1280; e.style.height = (720 * k) + 'px'; sl.style.transform = 'scale(' + k + ')';
    });
  }

  /* ---------- page chrome ---------- */
  function chrome() {
    qsa('[data-theme-toggle]').forEach(function (h) { if (!qs('.s-theme-toggle', h)) h.appendChild(themeToggle()); });
    var mode = root.getAttribute('data-mode');
    var txt = { live: 'Live data', snapshot: 'Snapshot', sample: 'Sample data', synthetic: 'Synthetic data', published: 'Published figures' }[mode];
    qsa('.s-mode').forEach(function (b) { if (!b.textContent.trim() && txt) b.textContent = txt + (mode === 'snapshot' && root.getAttribute('data-cutoff') ? ' \u00b7 ' + root.getAttribute('data-cutoff') : ''); b.setAttribute('data-mode', mode || ''); });
    qsa('ol.s-examples[start]').forEach(function (o) { o.style.counterReset = 'ex ' + (parseInt(o.getAttribute('start'), 10) - 1); });
    evidence();
    setTheme(ST.theme, false);
  }

  var SL = window.SL = {
    setTheme: function (t) { setTheme(t, true); SL.redraw(); },
    theme: function () { return ST.theme; },
    fmt: function (v, f) {
      if (v == null || isNaN(v)) return 'n/a';
      if (f === 'int' || f == null) return Number.isInteger(v) ? v.toLocaleString('en-US') : v.toLocaleString('en-US', { maximumFractionDigits: 1 });
      if (f === 'pct1') return v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
      if (f === 'usd') return '$' + v.toLocaleString('en-US', { maximumFractionDigits: 2 });
      return String(v);
    },
    highlight: hl,
    shapes: SHAPES,
    redraw: function () { embeds(); drawAll(); qsa('.s-stairs').forEach(wireStairs); qsa('.s-fanout').forEach(wireFan); }
  };

  function boot() {
    try {
      highlightAll(); deck(); chrome(); embeds();
      var go = function () { drawAll(); ST.ready = true; root.classList.add('s-ready'); };
      if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(go, go); else go();
      var t; window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(SL.redraw, 120); });
      window.addEventListener('beforeprint', SL.redraw);
    } catch (e) { ST.errors.push('boot: ' + e.message); ST.ready = true; }
  }
  window.addEventListener('error', function (e) { ST.errors.push(String(e.message)); });
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', boot); else boot();
})();
