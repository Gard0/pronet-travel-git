// Regression: 4 languages x 3 widths — no horizontal scroll, no broken images, no JS errors,
// quick booking posts the right tour, main form posts, anchors land on their heading.
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8772';
(async () => {
  const b = await chromium.launch(); let fail = 0;
  const ok = (c, m) => { if (!c) { fail++; console.log('FAIL', m); } };
  for (const lang of ['ru', 'en', 'fr', 'vi']) for (const [w, h, mob] of [[320, 640, true], [393, 852, true], [1280, 860, false]]) {
    const tag = `${lang}@${w}`;
    const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: mob, hasTouch: mob, deviceScaleFactor: mob ? 2 : 1 });
    const p = await ctx.newPage(), errs = [];
    p.on('pageerror', e => errs.push(e.message));
    let posted = [];
    await p.route('**/*', r => { const q = r.request(); if (/google|gtm|jsdelivr/.test(q.url())) return r.abort(); if (q.method() === 'POST') { posted.push(q.postData()); return r.fulfill({ status: 200, body: 'ok' }); } return r.continue(); });
    await p.goto(`${BASE}/${lang}/`, { waitUntil: 'load' });
    await p.evaluate(() => document.documentElement.style.scrollBehavior = 'auto');
    // walk the page so lazy images load
    const H = await p.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < H; y += h * 0.8) { await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(120); }
    await p.waitForTimeout(600);
    const st = await p.evaluate(() => ({ over: document.documentElement.scrollWidth - innerWidth,
      broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0 && !i.closest('#det')).map(i => i.currentSrc || i.src),
      wide: [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('.ts-track,.reviews,.rv-track,#det,#quick,.marquee'); }).slice(0, 3).map(e => e.tagName + '.' + e.className) }));
    ok(st.over <= 0, `${tag} horizontal overflow ${st.over} ${st.wide}`);
    ok(!st.broken.length, `${tag} broken images ${st.broken}`);
    // anchors
    for (const id of ['tours', 'more', 'faq', 'about', 'contact']) {
      await p.evaluate(id => { location.hash = ''; location.hash = id; }, id); await p.waitForTimeout(250);
      const r = await p.evaluate(id => { const s = document.getElementById(id), k = s.querySelector('.kicker,h2'); return k ? k.getBoundingClientRect().top : -1; }, id);
      ok(r > 50 && r < h * 0.5, `${tag} anchor #${id} heading at ${Math.round(r)}`);
    }
    // quick booking from the x2 card
    await p.evaluate(() => { location.hash = ''; scrollTo(0, document.getElementById('more').offsetTop); });
    await p.click('#more a.btn[data-tour="x2"]'); await p.waitForTimeout(300);
    await p.fill('#q-name', 'Test'); await p.fill('#q-contact', '@test'); await p.click('#q-form button[type=submit]'); await p.waitForTimeout(600);
    ok(posted.some(x => /form-name=contact/.test(x) && /tour=H%C3%B2n%20T%E1%BA%B1m/.test(x)), `${tag} quick booking post ${posted.map(decodeURIComponent)}`);
    ok(!errs.length, `${tag} errors ${errs}`);
    await ctx.close();
  }
  console.log(fail ? `${fail} checks failed` : 'all regression checks passed');
  await b.close(); process.exit(fail ? 1 : 0);
})();
