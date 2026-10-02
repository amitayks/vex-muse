#!/usr/bin/env node
/*
 * shoot.mjs — visual acceptance for a built Shift Labs document, in headless Chrome.
 *
 *   node shoot.mjs DOC.html [--out DIR] [--pdf] [--pdf-dark] [--figures] [--puppeteer /abs/node_modules/puppeteer-core]
 *
 * Deck (body.s-deck): every slide in LIGHT and DARK at 1920x1080 → DIR/{light,dark}-NN.png + {light,dark}-sheet.jpg.
 *   Checks per slide: content stays inside the slide and above the "How we counted" rule, no clipped text,
 *   no overlapping text, every shape drawn, text contrast (fail < 3:1, warn < 4.5:1 for small text).
 *   --pdf writes DIR/<name>.pdf (light, one 960x540 pt page per slide) and checks the page count; --pdf-dark too.
 * Page (anything else): phone 390x844 and desktop 1440x900 in light and dark → viewport slices.
 *   Checks: no horizontal overflow, fonts loaded, shapes drawn, contrast, no text under 12 px, no errors.
 *   Reports (data-doc="report"): the first-screen brief (.s-brief) must start inside the first desktop screen.
 * Every doc: a reduced-motion pass (prefers-reduced-motion: reduce) must show no running animation or transition.
 * <details> are opened before the audit so the detail layer is checked too.
 * --figures: every [data-figure] element → DIR/figure-<id>-{light,dark}.png (for posts and docs).
 * Writes DIR/report.json; exit 1 on any failure. LOOK at the sheets and slices — this script cannot judge taste.
 * Needs puppeteer-core resolvable (cwd, --puppeteer or $PUPPETEER_MODULE) and Chrome at $CHROME_PATH.
 */
import { createRequire } from 'module';
import path from 'path';
import fs from 'fs';
import { pathToFileURL } from 'url';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const flag = k => argv.includes(k);
const doc = argv.find((a, i) => !a.startsWith('--') && !['--out', '--puppeteer'].includes(argv[i - 1]));
if (!doc) { console.error('usage: node shoot.mjs DOC.html [--out DIR] [--pdf] [--pdf-dark] [--figures]'); process.exit(2); }
const base = path.basename(doc, '.html');
const out = path.resolve(opt('--out', path.join(path.dirname(path.resolve(doc)), base + '.shots')));
fs.mkdirSync(out, { recursive: true });

async function loadPuppeteer() {
  const cands = [opt('--puppeteer'), process.env.PUPPETEER_MODULE, 'puppeteer-core', 'puppeteer'].filter(Boolean);
  const req = createRequire(path.join(process.cwd(), 'x.js'));
  for (const c of cands) {
    try { const p = c.startsWith('/') ? (fs.statSync(c).isDirectory() ? req.resolve(c) : c) : req.resolve(c); const m = await import(pathToFileURL(p).href); return m.default || m; } catch (e) { /* next */ }
  }
  console.error('puppeteer not found: run from a dir with node_modules/puppeteer-core, or pass --puppeteer'); process.exit(2);
}
const puppeteer = await loadPuppeteer();
const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files', '--hide-scrollbars', '--font-render-hinting=none'] });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const fileUrl = (q) => pathToFileURL(path.resolve(doc)).href + q;
const report = { doc: path.resolve(doc), out, pass: true, runs: {} };

/* in-page audit: contrast, clipping, overlaps, shapes, fonts */
const AUDIT = (scopeSel) => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const L = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const blend = (fg, bg) => [0, 1, 2].map(i => fg[i] * fg[3] + bg[i] * (1 - fg[3]));
  const bgOf = e => { const stack = []; for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c[3] > 0) { stack.push(c); if (c[3] >= 0.99) break; } } let bg = [255, 255, 255]; for (let i = stack.length - 1; i >= 0; i--) bg = blend(stack[i], bg); return bg; };
  const scopes = scopeSel ? [...document.querySelectorAll(scopeSel)] : [document.body];
  const res = [];
  for (const sc of scopes) {
    const r = { contrastFail: [], contrastWarn: [], clipped: [], outside: [], overlaps: [], tiny: [] };
    const srect = sc.getBoundingClientRect();
    const scale = sc.offsetWidth ? srect.width / sc.offsetWidth : 1;
    const counted = sc.querySelector(':scope > .s-counted');
    const limitY = counted ? counted.getBoundingClientRect().top : null;
    const leaves = [];
    const all = sc.querySelectorAll('*');
    for (const e of all) {
      if (e.closest('[data-decor],[aria-hidden="true"],.s-noprint,script,style,#s-sprite')) continue;
      const cs = getComputedStyle(e);
      if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) continue;
      if (e instanceof SVGTSpanElement) continue; // measured through its <text>
      const isSvgText = e instanceof SVGTextElement;
      const own = isSvgText ? e.textContent.trim() : [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
      const b = e.getBoundingClientRect();
      if (!b.width || !b.height) continue;
      if (own) {
        const fg = parse(isSvgText ? cs.fill : cs.color); if (fg) {
          const bg = bgOf(e); const c = blend(fg, bg); const l1 = L(c), l2 = L(bg); const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
          let px = parseFloat(cs.fontSize); if (isSvgText) { const ctm = e.getScreenCTM(); px = px * (ctm ? ctm.a : 1) / scale; }
          const large = px >= 24 || (px >= 18.66 && (parseInt(cs.fontWeight, 10) >= 700));
          const tag = (e.tagName.toLowerCase() + '.' + String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className).split(' ')[0]).slice(0, 40) + ' "' + own.slice(0, 28) + '" ' + ratio.toFixed(2);
          const capsLabel = cs.textTransform === 'uppercase' && parseInt(cs.fontWeight, 10) >= 700; // kit rule: bold caps labels may sit at 3:1
          if (ratio < 3) r.contrastFail.push(tag); else if (ratio < 4.5 && !large && !capsLabel) r.contrastWarn.push(tag);
          if (!scopeSel && px < 11.5 && !e.closest('.s-embed')) r.tiny.push(tag.replace(/ [\d.]+$/, '') + ' ' + px.toFixed(1) + 'px');
        }
        if (!isSvgText && (cs.overflow.includes('hidden') || cs.textOverflow === 'ellipsis') && (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 2)) r.clipped.push(e.className + ' "' + own.slice(0, 30) + '"');
        // what the reader sees: clip each line box to every scrolling/clipping ancestor (a table scrolled inside its own box does not collide)
        let rs = [...e.getClientRects()].map(q => ({ left: q.left, right: q.right, top: q.top, bottom: q.bottom }));
        for (let a = e.parentElement; a && a !== sc.parentElement; a = a.parentElement) {
          const acs = getComputedStyle(a); if (acs.overflowX === 'visible' && acs.overflowY === 'visible') continue;
          const c = a.getBoundingClientRect(); rs = rs.map(q => ({ left: Math.max(q.left, c.left), right: Math.min(q.right, c.right), top: Math.max(q.top, c.top), bottom: Math.min(q.bottom, c.bottom) }));
        }
        rs = rs.map(q => ({ ...q, width: q.right - q.left, height: q.bottom - q.top })).filter(q => q.width > 1 && q.height > 1);
        leaves.push({ e, rs, t: own.slice(0, 24) });
      }
      if (scopeSel && !e.closest('.s-runfoot, .s-counted')) {
        const tol = 1.5;
        if (b.left < srect.left - tol || b.right > srect.right + tol || b.top < srect.top - tol || b.bottom > srect.bottom + tol) r.outside.push((e.className.baseVal ?? e.className) + ' ' + (own ? '"' + own.slice(0, 24) + '"' : e.tagName));
        else if (limitY != null && own && b.bottom > limitY + tol) r.outside.push('below counted rule: "' + own.slice(0, 30) + '"');
      }
    }
    for (let i = 0; i < leaves.length; i++) for (let j = i + 1; j < leaves.length; j++) {
      const a = leaves[i], c = leaves[j];
      if (a.e.contains(c.e) || c.e.contains(a.e)) continue;
      let hit = false;
      for (const p1 of a.rs) { for (const p2 of c.rs) {
        const w = Math.min(p1.right, p2.right) - Math.max(p1.left, p2.left), h = Math.min(p1.bottom, p2.bottom) - Math.max(p1.top, p2.top);
        if (w > 2 && h > 2 && w * h > 0.12 * Math.min(p1.width * p1.height, p2.width * p2.height)) { hit = true; break; } } if (hit) break; }
      if (hit) r.overlaps.push('"' + a.t + '" × "' + c.t + '"');
    }
    const shapes = [...sc.querySelectorAll('.s-shape[data-shape]')];
    r.shapes = shapes.length; r.undrawn = shapes.filter(s => !s.hasAttribute('data-drawn')).map(s => s.getAttribute('data-shape'));
    res.push(r);
  }
  const logos = [];
  for (const img of document.querySelectorAll('img[data-brand]')) {
    if (!img.offsetParent && getComputedStyle(img).position !== 'fixed') continue;
    const cs = getComputedStyle(img), b = img.getBoundingClientRect(), name = img.getAttribute('data-brand') + ' "' + (img.alt || '').slice(0, 24) + '"';
    if (!img.complete || !img.naturalWidth) { logos.push(name + ' did not load'); continue; }
    const nat = img.naturalWidth / img.naturalHeight, got = b.width / b.height;
    if (Math.abs(got - nat) > 0.01 * nat) logos.push(name + ' stretched ' + b.width.toFixed(1) + '×' + b.height.toFixed(1) + ' (file ' + nat.toFixed(3) + ')');
    const bk = bgOf(img); if (bk.every(v => v >= 254)) logos.push(name + ' sits on a white background');
    for (const [k, ok] of [['borderRadius', '0px'], ['clipPath', 'none'], ['transform', 'none'], ['filter', 'none'], ['opacity', '1'], ['maskImage', 'none'], ['objectFit', 'fill'], ['backgroundColor', 'rgba(0, 0, 0, 0)']])
      if (cs[k] !== undefined && cs[k] !== ok && !(k === 'maskImage' && cs[k] === '')) logos.push(name + ' ' + k + ': ' + cs[k]);
    if (img.offsetHeight < 16) logos.push(name + ' smaller than 16 px');
    for (let a = img.parentElement; a && a !== document.documentElement; a = a.parentElement) {
      const acs = getComputedStyle(a); if (acs.overflow === 'visible' && acs.clipPath === 'none') continue;
      const r = a.getBoundingClientRect();
      if (b.left < r.left - 0.5 || b.right > r.right + 0.5 || b.top < r.top - 0.5 || b.bottom > r.bottom + 0.5) { logos.push(name + ' is cut by ' + a.tagName.toLowerCase() + '.' + String(a.className).split(' ')[0]); break; }
    }
  }
  // centre lines: connected parts of a shape must share one axis (1 px tolerance)
  const cy = e => { const r = e.getBoundingClientRect(); return r.top + r.height / 2; };
  const spread = a => a.length ? Math.max(...a) - Math.min(...a) : 0;
  const misaligned = [];
  document.querySelectorAll('.s-flow:not(.is-stacked)').forEach(f => { if (!f.offsetParent) return; const d = spread([...f.querySelectorAll(':scope > .s-flow__step > .s-flow__body > *:first-child, :scope > .s-flow__arrow')].map(cy)); if (d > 1) misaligned.push('flow ' + d.toFixed(1) + 'px'); });
  document.querySelectorAll('.s-flow:not(.is-stacked)').forEach(f => { if (!f.offsetParent) return; const k = [...f.children], g = [];
    k.forEach((a, i) => { if (!a.classList.contains('s-flow__arrow') || !k[i - 1] || !k[i + 1]) return; const ab = k[i - 1].querySelector('.s-flow__body > *'), bb = k[i + 1].querySelector('.s-flow__body > *'); if (!ab || !bb) return;
      g.push(a.querySelector('i').getBoundingClientRect().left - ab.getBoundingClientRect().right, bb.getBoundingClientRect().left - a.querySelector('svg').getBoundingClientRect().right); });
    const d = spread(g); if (d > 1.5) misaligned.push('flow arrow gaps differ by ' + d.toFixed(1) + 'px'); });
  document.querySelectorAll('.s-diff').forEach(dd => { if (!dd.offsetParent || getComputedStyle(dd).gridTemplateColumns.split(' ').length < 3) return; const d = spread([...dd.querySelectorAll('.s-diff__card, .s-diff__ne')].map(cy)); if (d > 1) misaligned.push('diff ' + d.toFixed(1) + 'px'); });
  document.querySelectorAll('.s-match').forEach(m => { if (!m.offsetParent) return; const rows = [...m.querySelectorAll('.s-match__row')], K = [...m.querySelectorAll('.s-match__link')];
    K.forEach((k, i) => { const d = spread([cy(rows[2 * i]), cy(rows[2 * i + 1]), cy(k)]); if (d > 1) misaligned.push('match row ' + (i + 1) + ' ' + d.toFixed(1) + 'px'); }); });
  document.querySelectorAll('.s-queue__out').forEach(q => { if (!q.offsetParent) return; const d = spread([...q.children].map(cy)); if (d > 1) misaligned.push('queue ' + d.toFixed(1) + 'px'); });
  const st = window.__shift || {};
  const bf = document.querySelector('.s-brief'), br = bf && bf.getBoundingClientRect();
  const spill = []; // boxes whose own text overflows them (bare text nodes never show up in an element scan)
  if (!scopeSel) for (const e of document.body.querySelectorAll('*')) { const cs = getComputedStyle(e); if (cs.overflowX !== 'visible' || !e.clientWidth || e instanceof SVGElement) continue; if (e.scrollWidth > e.clientWidth + 1 && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) spill.push(e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]); }
  return { spill: spill.slice(0, 4), report: document.documentElement.getAttribute('data-doc') === 'report', brief: br ? { top: br.top + scrollY, bottom: br.bottom + scrollY } : null, misaligned, logos, slides: res, ready: !!st.ready, errors: st.errors || [], fonts: [...new Set([...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/"/g, '')))], overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth };
};

async function open(vp, theme, media) {
  const p = await browser.newPage();
  await p.setViewport(vp);
  const errs = [];
  p.on('pageerror', e => errs.push(String(e.message || e)));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text().slice(0, 160)); });
  if (media) await p.emulateMediaFeatures(media);
  await p.goto(fileUrl('?theme=' + theme), { waitUntil: 'load', timeout: 60000 });
  await p.evaluate(() => document.fonts && document.fonts.ready);
  await p.waitForFunction(() => window.__shift && window.__shift.ready, { timeout: 15000 }).catch(() => errs.push('runtime never ready'));
  await p.addStyleTag({ content: '.s-deck-nav{display:none!important}' });
  await p.evaluate(() => { document.querySelectorAll('details').forEach(d => { d.open = true; }); window.SL && SL.redraw(); });
  await sleep(500);
  return { p, errs };
}
const FONTS = ['Shift Sans', 'Shift Display', 'Shift Mono'];

async function sheet(files, dest, cols) {
  const p = await browser.newPage();
  const imgs = files.map(f => `<img src="${path.basename(f)}">`).join('');
  const tmp = path.join(path.dirname(files[0]), '_sheet.html');
  fs.writeFileSync(tmp, `<html><body style="margin:0;background:#888;display:grid;grid-template-columns:repeat(${cols},1fr);gap:8px;padding:8px">${imgs}<style>img{width:100%;display:block}</style></body></html>`);
  await p.setViewport({ width: 1600, height: 900 });
  await p.goto(pathToFileURL(tmp).href, { waitUntil: 'load' });
  await sleep(300);
  await p.screenshot({ path: dest, type: 'jpeg', quality: 82, fullPage: true }); await p.close(); fs.unlinkSync(tmp);
}

const isDeck = fs.readFileSync(doc, 'utf8').includes('class="s-deck');
if (isDeck) {
  for (const theme of ['light', 'dark']) {
    const { p, errs } = await open({ width: 1920, height: 1080, deviceScaleFactor: 1 }, theme);
    const a = await p.evaluate(AUDIT, '.s-slide');
    const frames = await p.$$('.s-slide-frame'); const shots = [];
    for (let i = 0; i < frames.length; i++) { const f = path.join(out, `${theme}-${String(i + 1).padStart(2, '0')}.png`); await frames[i].screenshot({ path: f }); shots.push(f); }
    await sheet(shots, path.join(out, `${theme}-sheet.jpg`), 3);
    const problems = [], warnings = [];
    if (!a.ready) problems.push('runtime not ready');
    if (errs.length || a.errors.length) problems.push('errors: ' + [...errs, ...a.errors].slice(0, 4).join(' | '));
    for (const f of FONTS) if (!a.fonts.includes(f)) problems.push('font not loaded: ' + f);
    if (a.logos.length) problems.push('logo not as it is: ' + a.logos.slice(0, 4).join(', '));
    if (a.misaligned.length) problems.push('off the centre line: ' + a.misaligned.slice(0, 4).join(', '));
    a.slides.forEach((s, i) => {
      const n = 'slide ' + (i + 1) + ': ';
      if (s.outside.length) problems.push(n + 'outside frame/rule: ' + s.outside.slice(0, 3).join(', '));
      if (s.clipped.length) problems.push(n + 'clipped: ' + s.clipped.slice(0, 3).join(', '));
      if (s.overlaps.length) problems.push(n + 'overlap: ' + s.overlaps.slice(0, 3).join(', '));
      if (s.undrawn.length) problems.push(n + 'shapes not drawn: ' + s.undrawn.join(', '));
      if (s.contrastFail.length) problems.push(n + 'contrast < 3: ' + s.contrastFail.slice(0, 3).join(', '));
      if (s.contrastWarn.length) warnings.push(n + 'contrast < 4.5 (small text): ' + s.contrastWarn.slice(0, 3).join(', '));
    });
    report.runs[theme] = { slides: a.slides.length, fonts: a.fonts, problems, warnings, sheet: path.join(out, `${theme}-sheet.jpg`) };
    if (problems.length) report.pass = false;
    for (const [flagName, th] of [['--pdf', 'light'], ['--pdf-dark', 'dark']]) {
      if (theme !== th || !flag(flagName)) continue;
      const pdf = path.join(out, `${base}${th === 'dark' ? '-dark' : ''}.pdf`);
      await p.evaluate(() => window.SL && SL.redraw()); await sleep(300);
      await p.pdf({ path: pdf, preferCSSPageSize: true, printBackground: true });
      const bytes = fs.readFileSync(pdf); const pages = (bytes.toString('latin1').match(/\/Type\s*\/Page(?!s)/g) || []).length;
      report.runs[theme].pdf = { path: pdf, pages, bytes: bytes.length };
      if (pages !== a.slides.length) { report.pass = false; report.runs[theme].problems.push(`pdf has ${pages} pages for ${a.slides.length} slides`); }
    }
    await p.close();
  }
} else {
  for (const theme of ['light', 'dark']) for (const [name, vp] of [['phone', { width: 390, height: 844, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }], ['desktop', { width: 1440, height: 900, deviceScaleFactor: 1 }]]) {
    const { p, errs } = await open(vp, theme);
    const a = await p.evaluate(AUDIT, null); const s = a.slides[0];
    const H = await p.evaluate(() => document.documentElement.scrollHeight); const shots = [];
    for (let y = 0, i = 0; y < H && i < 30; y += vp.height, i++) { await p.evaluate(y => scrollTo(0, y), y); await sleep(150); const f = path.join(out, `${theme}-${name}-${String(i).padStart(2, '0')}.jpg`); await p.screenshot({ path: f, type: 'jpeg', quality: 80 }); shots.push(f); }
    const problems = [], warnings = [];
    if (!a.ready) problems.push('runtime not ready');
    if (errs.length || a.errors.length) problems.push('errors: ' + [...errs, ...a.errors].slice(0, 4).join(' | '));
    for (const f of FONTS) if (!a.fonts.includes(f)) problems.push('font not loaded: ' + f);
    if (a.overflowX > 1) problems.push('horizontal overflow ' + a.overflowX + 'px' + (a.spill.length ? ' (text spills from: ' + a.spill.join(', ') + ')' : ''));
    if (a.logos.length) problems.push('logo not as it is: ' + a.logos.slice(0, 4).join(', '));
    if (a.misaligned.length) problems.push('off the centre line: ' + a.misaligned.slice(0, 4).join(', '));
    if (s.undrawn.length) problems.push('shapes not drawn: ' + s.undrawn.join(', '));
    if (s.contrastFail.length) problems.push('contrast < 3: ' + s.contrastFail.slice(0, 4).join(', '));
    if (s.contrastWarn.length) warnings.push('contrast < 4.5 (small text): ' + s.contrastWarn.slice(0, 4).join(', '));
    if (s.clipped.length) warnings.push('clipped: ' + s.clipped.slice(0, 4).join(', '));
    if (s.overlaps.length) problems.push('overlap: ' + s.overlaps.slice(0, 4).join(', '));
    if (s.tiny.length) problems.push(s.tiny.length + ' text elements under 12px: ' + s.tiny.slice(0, 5).join(', '));
    if (a.report && name === 'desktop') {
      if (!a.brief) problems.push('report has no first-screen brief (.s-brief)');
      else if (a.brief.top > vp.height) problems.push('first-screen brief starts at ' + Math.round(a.brief.top) + 'px, below the first screen (' + vp.height + 'px)');
      else if (a.brief.bottom > vp.height) warnings.push('first-screen brief ends at ' + Math.round(a.brief.bottom) + 'px, past the first screen');
    }
    report.runs[`${theme}-${name}`] = { shapes: s.shapes, fonts: a.fonts, problems, warnings, shots: shots.length };
    if (problems.length) report.pass = false;
    if (name === 'desktop' && theme === 'light' && flag('--pdf')) { const pdf = path.join(out, base + '.pdf'); await p.pdf({ path: pdf, printBackground: true, format: 'A4' }); report.runs[`${theme}-${name}`].pdf = pdf; }
    await p.close();
  }
}
{ // reduced motion: nothing may move when the reader asks for stillness
  const { p, errs } = await open(isDeck ? { width: 1920, height: 1080 } : { width: 390, height: 844, isMobile: true, hasTouch: true }, 'light', [{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  const m = await p.evaluate(() => ({
    anims: document.getAnimations().filter(a => a.playState === 'running').length,
    moving: [...document.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); return [cs.transitionDuration, cs.animationDuration].some(v => v.split(',').some(x => parseFloat(x) > 0)); }).slice(0, 4).map(e => e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]),
  }));
  const problems = [];
  if (m.anims) problems.push(m.anims + ' animations still running under reduced motion');
  if (m.moving.length) problems.push('transitions under reduced motion: ' + m.moving.join(', '));
  if (errs.length) problems.push('errors: ' + errs.slice(0, 3).join(' | '));
  report.runs['reduced-motion'] = { problems, warnings: [] };
  if (problems.length) report.pass = false;
  await p.close();
}
if (flag('--figures')) {
  for (const theme of ['light', 'dark']) {
    const { p } = await open({ width: 1440, height: 900, deviceScaleFactor: 2 }, theme);
    const figs = await p.$$('[data-figure]');
    for (const f of figs) { const id = await f.evaluate(e => e.getAttribute('data-figure')); await f.screenshot({ path: path.join(out, `figure-${id}-${theme}.png`) }); }
    report.figures = (report.figures || 0) + figs.length; await p.close();
  }
}
await browser.close();
fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1));
console.log(JSON.stringify({ pass: report.pass, out, runs: Object.fromEntries(Object.entries(report.runs).map(([k, v]) => [k, { problems: v.problems, warnings: v.warnings.slice(0, 6), pdf: v.pdf }])) }, null, 1));
process.exit(report.pass ? 0 : 1);
