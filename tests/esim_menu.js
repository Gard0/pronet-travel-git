// eSIM shop opens inside the page (iframe), Back closes it; opening booking from the mobile menu closes the menu.
const { chromium, devices } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8772';
(async () => {
  const b = await chromium.launch(); let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } };
  for (const [name, o] of [['iphone', devices['iPhone 13']], ['desktop', { viewport: { width: 1280, height: 860 } }]]) {
    const c = await b.newContext(o), p = await c.newPage(), errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.route('**/*', r => { const u = r.request().url(); if (/pronetservicesvn\.com\/(vi\/)?esim/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html', body: '<h1>eSIM shop stub</h1>' }); if (/google|gtm/.test(u)) return r.abort(); return r.continue(); });
    await p.goto(BASE + '/ru/'); await p.waitForTimeout(400);
    await p.evaluate(() => document.documentElement.style.scrollBehavior = 'auto');
    await p.$eval('#esim-link', e => e.scrollIntoView({ block: 'center' })); await p.waitForTimeout(200);
    const y0 = await p.evaluate(() => scrollY);
    await p.click('#esim-link'); await p.waitForTimeout(700);
    const st = await p.evaluate(() => ({ open: !document.getElementById('esim-modal').hidden, hash: location.hash, src: (document.querySelector('#es-body iframe') || {}).src, wait: document.getElementById('es-wait').hidden,
      frame: (() => { const r = document.querySelector('#es-body iframe').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })() }));
    ok(st.open && st.hash === '#esim' && /esim$/.test(st.src) && st.wait && st.frame[1] > 300, `${name} esim open ${JSON.stringify(st)}`);
    const fr = p.frames().find(f => f !== p.mainFrame() && /esim/.test(f.url())); const html = fr ? await fr.content() : 'no frame ' + p.frames().map(f => f.url()); ok(/stub/.test(html), `${name} iframe content ${html.slice(0, 120)}`);
    await p.screenshot({ path: `/tmp/esim_${name}.png` });
    await p.goBack(); await p.waitForTimeout(400);
    const af = await p.evaluate(() => ({ open: !document.getElementById('esim-modal').hidden, y: scrollY, hash: location.hash }));
    ok(!af.open && af.hash === '' && Math.abs(af.y - y0) < 4, `${name} back closes esim ${JSON.stringify(af)} y0=${y0}`);
    if (name === 'iphone') {   // menu + booking
      await p.click('#burger'); await p.waitForTimeout(300);
      ok(await p.$eval('#menu', m => m.classList.contains('open')), 'menu opens');
      await p.click('#top-bar [data-quick], #top-bar .btn'); await p.waitForTimeout(400);
      const m = await p.evaluate(() => ({ menu: document.getElementById('menu').classList.contains('open'), quick: !document.getElementById('quick').hidden }));
      ok(!m.menu && m.quick, `booking closes menu ${JSON.stringify(m)}`);
      await p.keyboard.press('Escape'); await p.waitForTimeout(200);
      await p.click('#burger'); await p.waitForTimeout(300);
      await p.mouse.click(200, 700); await p.waitForTimeout(300);
      ok(!(await p.$eval('#menu', m => m.classList.contains('open'))), 'tap outside closes menu');
    }
    ok(!errs.length, `${name} errors ${errs}`);
    await c.close();
  }
  console.log(fail ? `${fail} checks failed` : 'all esim/menu checks passed'); await b.close(); process.exit(fail ? 1 : 0);
})();
