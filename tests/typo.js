// Typography check: buttons wrapping onto 2 lines, clipped text, short words hanging at line ends, one-word last lines in headings.
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8772';
const LANGS = (process.argv[3] || 'ru,en,fr,vi').split(',');
const WIDTHS = [320, 375, 414, 768, 1024, 1280];
(async () => {
  const b = await chromium.launch(); const report = {};
  for (const lang of LANGS) for (const w of WIDTHS) {
    const c = await b.newContext({ viewport: { width: w, height: 900 }, isMobile: w < 700, hasTouch: w < 700, deviceScaleFactor: 1 });
    const p = await c.newPage(); await p.route('**/*', r => /google|gtm/.test(r.request().url()) ? r.abort() : r.continue());
    await p.goto(`${BASE}/${lang}/`, { waitUntil: 'load' });
    await p.evaluate(() => { document.documentElement.style.scrollBehavior = 'auto'; document.querySelectorAll('.reveal').forEach(e => e.classList.add('in')); });
    await p.waitForTimeout(300);
    const res = await p.evaluate(() => {
      const out = { btn: [], clip: [], hang: [], orphan: [] };
      const vis = e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && !e.closest('[hidden],#det,#quick,#esim-modal,.marquee,[aria-hidden="true"]'); };
      document.querySelectorAll('.btn, button, .chip b, .tag, .ts-facts li, .lang button').forEach(e => {
        if (!vis(e)) return; const lh = parseFloat(getComputedStyle(e).lineHeight) || parseFloat(getComputedStyle(e).fontSize) * 1.3;
        const range = document.createRange(); range.selectNodeContents(e); const lines = new Set([...range.getClientRects()].map(r => Math.round(r.top))).size;
        if (lines > 1 && e.textContent.trim()) out.btn.push(e.textContent.trim().slice(0, 40));
      });
      document.querySelectorAll('h1,h2,h3,p,li,a,span,b,small,label,summary').forEach(e => {
        if (!vis(e) || !e.textContent.trim()) return; const cs = getComputedStyle(e);
        if (e.scrollWidth > e.clientWidth + 2 && cs.overflowX !== 'visible' && cs.display !== 'inline' && !e.closest('.rev-row,.ts-track') && !e.classList.contains('card-img')) out.clip.push(e.tagName + ':' + e.textContent.trim().slice(0, 40));
      });
      const short = { ru: /^(в|во|и|а|с|со|к|ко|у|о|об|по|до|на|за|от|из|не|ни|но|для|при|без|над|под|про|или)$/i, fr: /^(à|a|y|et|de|du|des|le|la|les|un|une|en)$/i, en: /^(the|of|to|in|on|at|by|for|and|or|a|an)$/i, vi: /^$/ }[document.documentElement.lang];
      document.querySelectorAll('h1,h2,h3,p,li,.sub,.lead,small,.meta span,summary').forEach(e => {
        if (!vis(e) || e.children.length > 3) return;
        const tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); const words = [];
        while (tw.nextNode()) { const n = tw.currentNode; const re = /\S+/g; let m; while ((m = re.exec(n.data))) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); const rc = r.getClientRects()[0]; if (rc) words.push({ t: m[0], top: Math.round(rc.top) }); } }
        if (words.length < 3) return;
        const tops = [...new Set(words.map(x => x.top))];
        if (tops.length < 2) return;
        for (let i = 0; i < words.length - 1; i++) if (words[i].top !== words[i + 1].top && short.test(words[i].t)) out.hang.push(`"${words[i].t}" ⏎ in ${e.tagName}: ${e.textContent.trim().slice(0, 60)}`);
        if (/^H[123]$/.test(e.tagName)) { const last = words.filter(x => x.top === tops[tops.length - 1]); if (last.length === 1 && last[0].t.length < 8) out.orphan.push(`${e.tagName}: …${last[0].t} (${e.textContent.trim().slice(0, 50)})`); }
      });
      return out;
    });
    for (const k of Object.keys(res)) for (const v of res[k]) { const key = `${k} | ${v}`; (report[key] = report[key] || []).push(`${lang}@${w}`); }
    await c.close();
  }
  const keys = Object.keys(report).sort();
  for (const k of keys) console.log(k, ' ←', report[k].join(' '));
  console.log(keys.length ? `${keys.length} typography issues` : 'no typography issues');
  await b.close();
})();
