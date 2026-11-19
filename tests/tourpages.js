// Every tour page in every language: loads without errors, no sideways scroll, images load, booking form posts the right tour.
const { chromium, devices } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8772';
(async () => {
  const pages = [];
  for (const l of ['ru', 'en', 'fr', 'vi']) for (const s of fs.readdirSync(path.join('build', l, 'tours'))) pages.push(`/${l}/tours/${s}/`);
  const b = await chromium.launch(); let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } };
  for (const [name, o] of [['iphone', devices['iPhone 13']], ['desktop', { viewport: { width: 1280, height: 860 } }]]) {
    const c = await b.newContext(o);
    for (const u of pages) {
      const p = await c.newPage(), errs = []; let posted = null;
      p.on('pageerror', e => errs.push(e.message));
      await p.route('**/*', r => { const q = r.request(); if (/google|gtm/.test(q.url())) return r.abort(); if (q.method() === 'POST') { posted = q.postData(); return r.fulfill({ status: 200, body: 'ok' }); } return r.continue(); });
      const resp = await p.goto(BASE + u, { waitUntil: 'load' });
      ok(resp.status() === 200, `${name} ${u} status ${resp.status()}`);
      await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 500) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); } });
      await p.waitForTimeout(400);
      const st = await p.evaluate(() => ({ over: document.documentElement.scrollWidth - innerWidth, h1: document.querySelector('h1').textContent, broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src), links: [...document.querySelectorAll('a[href^="/"]')].map(a => a.getAttribute('href')) }));
      ok(st.over <= 0, `${name} ${u} overflow ${st.over}`); ok(st.h1, `${name} ${u} h1`); ok(!st.broken.length, `${name} ${u} broken ${st.broken}`);
      if (name === 'iphone' && /hon-tam-mud-baths-day/.test(u)) await p.screenshot({ path: `/tmp/tp_${u.split('/')[1]}.png` });
      if (u === '/ru/tours/hon-mun-hon-tam-mud-baths/') {
        await p.screenshot({ path: `/tmp/tp_${name}.png` });
        await p.fill('#t-name', 'Test'); await p.fill('#t-contact', '@t'); await p.click('#book button[type=submit]'); await p.waitForTimeout(500);
        ok(posted && /tour=Hon%20Mun%2C%20fishing%20village%20%26%20Hon%20Tam/.test(posted) && /Tour%20page/.test(posted), `${name} form post ${posted}`);
        // every internal link resolves
        for (const h of [...new Set(st.links)].filter(h => !h.includes('#') || h.split('#')[0])) { const r = await p.request.get(BASE + h.split('#')[0]); ok(r.status() === 200, `${name} link ${h} ${r.status()}`); }
      }
      ok(!errs.length, `${name} ${u} errors ${errs}`);
      await p.close();
    }
    await c.close();
  }
  console.log(fail ? `${fail} checks failed` : `all ${pages.length} tour pages ok`); await b.close(); process.exit(fail ? 1 : 0);
})();
