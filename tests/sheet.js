// Checks the tour sheet on desktop and phone: every card opens, gallery, Back closes, deep link, booking hand-off.
const { chromium, devices } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8772';
const IDS = ['sea', 'cove', 'honmun', 'x5', 'x6', 'x2', 'x1', 'x7', 'x3', 'x4'];
(async () => {
  const b = await chromium.launch(); let fail = 0;
  const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } };
  for (const [name, ctxOpt] of [['desktop', { viewport: { width: 1280, height: 860 } }], ['iphone', devices['iPhone 13']], ['android', devices['Pixel 7']]]) {
    const ctx = await b.newContext(ctxOpt), p = await ctx.newPage(), errs = [];
    p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error' && !/gtm|google|net::/i.test(m.text())) errs.push(m.text()); });
    await p.route('**/*', r => /google|gtm|jsdelivr/.test(r.request().url()) ? r.abort() : r.continue());
    await p.goto(BASE + '/ru/', { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(500);
    for (const id of IDS) {
      const y0 = await p.evaluate(() => scrollY);
      const btn = await p.$(`a.btn[data-det="${id}"], a.btn[data-det="${id}"]`);
      await btn.scrollIntoViewIfNeeded(); await p.waitForTimeout(150);
      const yBefore = await p.evaluate(() => scrollY);
      await btn.click(); await p.waitForTimeout(450);
      const st = await p.evaluate(() => ({ open: !document.getElementById('det').hidden, hash: location.hash, title: document.getElementById('d-title').textContent,
        imgs: document.querySelectorAll('#d-track img').length, prog: document.querySelectorAll('#d-prog li').length, incl: document.querySelectorAll('#d-incl li').length,
        price: document.getElementById('d-price').textContent, count: document.getElementById('d-count').textContent,
        over: document.documentElement.scrollWidth - innerWidth, bar: (() => { const r = document.querySelector('.ts-bar').getBoundingClientRect(); return r.bottom <= innerHeight + 1 && r.top < innerHeight; })() }));
      ok(st.open && st.hash === '#tour-' + id, `${name} ${id} open/hash ${JSON.stringify(st)}`);
      ok(st.title && st.prog >= 3 && st.incl >= 2 && /\d/.test(st.price), `${name} ${id} content ${JSON.stringify(st)}`);
      ok(st.bar, `${name} ${id} price bar visible`); ok(st.over <= 0, `${name} ${id} overflow ${st.over}`);
      if (id === 'sea') await p.screenshot({ path: `/tmp/sheet_${name}_sea.png` });
      if (id === 'x1') await p.screenshot({ path: `/tmp/sheet_${name}_x1.png` });
      if (st.imgs > 1) { // swipe/next
        await p.evaluate(() => { const t = document.getElementById('d-track'); t.scrollLeft = t.clientWidth; }); await p.waitForTimeout(300);
        const c = await p.$eval('#d-count', e => e.textContent); ok(c.startsWith('2 /'), `${name} ${id} gallery counter ${c}`);
      }
      // Back button closes and keeps the page where it was
      await p.goBack(); await p.waitForTimeout(350);
      const after = await p.evaluate(() => ({ open: !document.getElementById('det').hidden, y: scrollY, hash: location.hash, pos: document.body.style.position }));
      ok(!after.open && after.hash === '' && !after.pos, `${name} ${id} back closes ${JSON.stringify(after)}`);
      ok(Math.abs(after.y - yBefore) < 4, `${name} ${id} scroll kept ${yBefore}->${after.y}`);
    }
    // X button, ESC, booking hand-off
    await p.click('a.btn[data-det="x2"]'); await p.waitForTimeout(300);
    await p.click('#det .modal-x'); await p.waitForTimeout(300);
    ok(await p.$eval('#det', e => e.hidden), `${name} X closes`);
    await p.click('a.btn[data-det="x3"]'); await p.waitForTimeout(300);
    await p.click('#d-book'); await p.waitForTimeout(500);
    const q = await p.evaluate(() => ({ det: document.getElementById('det').hidden, quick: !document.getElementById('quick').hidden, tour: (document.querySelector('#q-form input[name=q-tour]:checked') || {}).value, hash: location.hash }));
    ok(q.det && q.quick && q.tour === 'x3' && q.hash === '', `${name} book hand-off ${JSON.stringify(q)}`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(200);
    // language switch while open
    if (name === 'desktop') {
      await p.click('a.btn[data-det="sea"]'); await p.waitForTimeout(300);
      await p.evaluate(() => document.querySelector('.lang button[data-lang="en"]').click()); await p.waitForTimeout(300);
      const t = await p.$eval('#d-title', e => e.textContent); ok(/Nha Trang/i.test(t), `lang switch title ${t}`);
      await p.keyboard.press('Escape'); await p.waitForTimeout(300);
      ok(await p.$eval('#det', e => e.hidden), 'ESC closes');
    }
    // deep link
    const p2 = await ctx.newPage(); await p2.route('**/*', r => /google|gtm/.test(r.request().url()) ? r.abort() : r.continue());
    await p2.goto(BASE + '/fr/#tour-honmun', { waitUntil: 'domcontentloaded' }); await p2.waitForTimeout(500);
    const d = await p2.evaluate(() => ({ open: !document.getElementById('det').hidden, t: document.getElementById('d-title').textContent }));
    ok(d.open && /Hon Mun/.test(d.t), `${name} deep link ${JSON.stringify(d)}`);
    await p2.click('#det .modal-x'); await p2.waitForTimeout(300);
    ok(await p2.evaluate(() => document.getElementById('det').hidden && location.hash === ''), `${name} deep link close`);
    ok(!errs.length, `${name} errors ${errs.join(' | ')}`);
    await ctx.close();
  }
  console.log(fail ? `${fail} checks failed` : 'all sheet checks passed');
  await b.close(); process.exit(fail ? 1 : 0);
})();
