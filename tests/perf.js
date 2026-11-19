// Usage: node tests/perf.js http://localhost:8772/ru/  -> FCP, LCP, CLS, bytes (mobile, 4x CPU slowdown, fast 4G)
const { chromium, devices } = require('playwright');
(async () => {
  const url = process.argv[2] || 'http://localhost:8772/ru/';
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'] });
  const p = await ctx.newPage();
  const cdp = await ctx.newCDPSession(p);
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 1.6e6 / 8 * 4, uploadThroughput: 750e3 / 8 });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  let bytes = 0; p.on('response', async r => { try { const h = await r.allHeaders(); bytes += +(h['content-length'] || (await r.body()).length); } catch (e) {} });
  await p.addInitScript(() => {
    window.__lcp = 0; window.__cls = 0;
    new PerformanceObserver(l => l.getEntries().forEach(e => window.__lcp = e.startTime)).observe({ type: 'largest-contentful-paint', buffered: true });
    new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) window.__cls += e.value; })).observe({ type: 'layout-shift', buffered: true });
  });
  await p.goto(url, { waitUntil: 'load' }); await p.waitForTimeout(2500);
  const m = await p.evaluate(() => ({ fcp: (performance.getEntriesByName('first-contentful-paint')[0] || {}).startTime, lcp: window.__lcp, cls: window.__cls }));
  console.log(JSON.stringify({ url, fcp: Math.round(m.fcp), lcp: Math.round(m.lcp), cls: +m.cls.toFixed(3), kb: Math.round(bytes / 1024) }));
  await b.close();
})();
