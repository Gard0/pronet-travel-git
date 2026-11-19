// Finds words broken across two lines on narrow phones (4 languages, 320 and 375 px).
// finds words split across lines (letters on both sides of a line break inside one word)
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();let n=0;
for (const L of ['ru','en','fr','vi']) for (const w of [320,375]){const p=await b.newPage({viewport:{width:w,height:800},isMobile:true});
await p.route('**/*', r => /google|gtm/.test(r.request().url()) ? r.abort() : r.continue());
await p.goto(`http://localhost:8772/${L}/`);await p.waitForTimeout(300);
const r=await p.evaluate(()=>{const out=[];const tw=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);while(tw.nextNode()){const t=tw.currentNode;if(!t.parentElement||t.parentElement.closest('[hidden],script,style,#det,#quick,#esim-modal,.hp,[aria-hidden="true"]') || getComputedStyle(t.parentElement).position==='absolute' && t.parentElement.getBoundingClientRect().width<5)continue;const re=/[^\s ]{4,}/g;let m;while((m=re.exec(t.data))){const rg=document.createRange();rg.setStart(t,m.index);rg.setEnd(t,m.index+m[0].length);const tops=new Set([...rg.getClientRects()].filter(x=>x.width>1).map(x=>Math.round(x.top)));if(tops.size>1&&!/[-–—/]/.test(m[0]))out.push(m[0])}}return out});
if(r.length){n+=r.length;console.log(L,w,r.slice(0,10))}await p.close()}
console.log(n?n+' split words':'no split words');await b.close()})();
