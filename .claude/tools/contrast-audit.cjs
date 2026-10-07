// Rendered copper-text contrast audit for artisanitsolutions.com (Artisan Solutions Design System, rule 6).
//
//   npm --prefix .claude/tools install                       # once (installs playwright-core only)
//   node .claude/tools/contrast-audit.cjs                    # every page
//   node .claude/tools/contrast-audit.cjs yardi-foo.html     # one page
//
// Serves the repo locally, opens each page in your installed Google Chrome at desktop (1280px) and phone
// (375px) widths, finishes the entrance animations, and measures every visible copper text element
// against the background really behind it (solid colours and gradients). Fails on normal text under
// 4.5:1 or large text (24px+, or 18.66px+ bold) under 3:1. Wordmarks and faded decorative numerals are
// exempt. Exit code 1 when anything fails. Set CHROME_PATH to use a specific Chrome/Chromium binary.
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright-core');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2', '.json': 'application/json' };
const pages = process.argv.slice(2).length ? process.argv.slice(2) : fs.readdirSync(ROOT).filter(f => f.endsWith('.html')).sort();
const WIDTHS = [1280, 375];

function measure() {
  const parse = (s) => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const [r, g, b, a = 1] = m[1].split(',').map(Number); return { r, g, b, a }; };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const over = (t, b) => ({ r: t.r * t.a + b.r * (1 - t.a), g: t.g * t.a + b.g * (1 - t.a), b: t.b * t.a + b.b * (1 - t.a), a: 1 });
  const bgOf = (el) => {
    const layers = [];
    for (let n = el; n; n = n.parentElement) {
      const st = getComputedStyle(n);
      const c = parse(st.backgroundImage.startsWith('linear-gradient') ? (st.backgroundImage.match(/rgba?\([^)]+\)/) || [''])[0] : st.backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    return layers.reverse().reduce((acc, l) => over(l, acc), { r: 255, g: 255, b: 255, a: 1 });
  };
  const copperish = (c) => c && c.r > 150 && c.r - c.b > 80 && c.g > 60 && c.g < 190;
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const cs = getComputedStyle(el);
    const fg = parse(cs.color);
    if (!copperish(fg) || cs.display === 'none' || cs.visibility === 'hidden' || !el.getBoundingClientRect().width) continue;
    let op = 1; for (let n = el; n; n = n.parentElement) op *= Number(getComputedStyle(n).opacity);
    const bg = bgOf(el);
    const [hi, lo] = [lum(over({ ...fg, a: fg.a * op }, bg)), lum(bg)].sort((a, b) => b - a);
    const ratio = (hi + 0.05) / (lo + 0.05);
    const size = parseFloat(cs.fontSize);
    const need = size >= 24 || (size >= 18.66 && Number(cs.fontWeight) >= 700) ? 3 : 4.5;
    const exempt = fg.a * op < 0.35 || !!el.closest('[aria-hidden="true"],[class*="logo"],[class*="wm"]');
    const cls = typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).join('.') : '';
    if (!exempt && ratio < need) out.push({ el: el.tagName.toLowerCase() + cls, text: el.textContent.trim().slice(0, 40), size, ratio, need });
  }
  return out;
}

(async () => {
  const server = http.createServer((req, res) => {
    const file = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  }).listen(0, '127.0.0.1');
  await new Promise(r => server.once('listening', r));
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' });
  let failures = 0;
  for (const width of WIDTHS) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    for (const p of pages) {
      await page.goto(`${base}/${p}`, { waitUntil: 'networkidle' });
      await page.addStyleTag({ content: '*,*::before,*::after{transition:none!important}.reveal{opacity:1!important;transform:none!important}' });
      await page.evaluate(() => document.getAnimations().forEach(a => { try { a.finish(); } catch {} }));
      const seen = new Set();
      for (const f of await page.evaluate(measure)) {
        const key = `${f.el}|${f.ratio.toFixed(2)}`;
        if (seen.has(key)) continue;
        seen.add(key);
        failures++;
        console.log(`FAIL ${width}px ${p}  ${f.el}  ${f.size}px  ${f.ratio.toFixed(2)}:1 (needs ${f.need})  "${f.text}"`);
      }
    }
    await page.close();
  }
  await browser.close();
  server.close();
  console.log(`${failures ? failures + ' failing' : 'All'} copper text checks${failures ? '' : ' pass'}: ${pages.length} page(s) at ${WIDTHS.join(' and ')}px`);
  process.exit(failures ? 1 : 0);
})();
