# Static page for every tour in every language: /<lang>/tours/<slug>/
# Same data as the tour window on the main page (site2/index.html), so the two never disagree.
import re, json, html

SLUG = {
    'sea': 'nha-trang-bay-boat-tour', 'cove': 'ganh-nhay-secret-cove', 'honmun': 'hon-mun-fishing-village-bai-tranh',
    'x5': 'hon-mun-hon-tam-mud-baths', 'x6': 'hon-mun-mini-beach', 'x2': 'hon-tam-mud-baths-day', 'x1': 'bai-tranh-coral-bay',
    'x7': 'mini-beach-hon-tam-super-vip', 'x3': 'vinwonders-nha-trang', 'x4': 'thailand-bangkok-4-days',
}
LANGS = ['ru', 'en', 'fr', 'vi']
NB = ' '
WORDS = {
    'home': {'ru': 'Главная', 'en': 'Home', 'fr': 'Accueil', 'vi': 'Trang chủ'},
    'others': {'ru': 'Другие туры', 'en': 'Other tours', 'fr': 'Autres excursions', 'vi': 'Tour khác'},
    'suffix': {'ru': 'экскурсия в Нячанге', 'en': 'Nha Trang tour', 'fr': 'excursion à Nha Trang', 'vi': 'tour Nha Trang'},
    'write': {'ru': 'Или напишите нам напрямую:', 'en': 'Or message us directly:', 'fr': 'Ou écrivez-nous directement :', 'vi': 'Hoặc nhắn trực tiếp cho chúng tôi:'},
    'all': {'ru': 'Все туры', 'en': 'All tours', 'fr': 'Toutes les excursions', 'vi': 'Tất cả tour'},
}
SHORT = {
    'ru': r'(а|в|во|и|к|ко|о|об|обо|с|со|у|не|ни|на|по|до|за|из|от|для|без|при|про|над|под|но|или|что|как|же|ли|бы|её|их|его|это|все|всё)',
    'fr': r'(à|a|au|aux|de|du|des|le|la|les|l’|un|une|et|en|ou|par|pour|sur|sans|dans|ce|ces|se|ne|y|il|on|vos|nos|votre|notre)',
    'en': r'(a|an|the|to|of|in|on|at|by|for|and|or|our|your|with|from|is|are|be|we|you|it)',
}

def typo(t, lang):   # same rules as typo() in the page script
    if not isinstance(t, str): return t
    if lang in SHORT:
        w = t.split(' '); out = w[0]; rx = re.compile('^' + SHORT[lang] + '$', re.I)
        for i in range(1, len(w)):
            out += (NB if rx.match(re.sub(r'^[(«„"“]+', '', w[i - 1])) and w[i] else ' ') + w[i]
        t = out
    t = re.sub(r'\s+(—|–)\s', NB + r'\1 ', t)
    t = re.sub(r'(\s)(\S{1,10}) (\S{1,10}[.!?…]?)$', lambda m: m.group(1) + m.group(2) + NB + m.group(3) if len(m.group(2) + m.group(3)) <= 12 else m.group(0), t)
    t = re.sub(r'(\d) (?=\d{3}\b)', r'\1' + NB, t); t = re.sub(r'(\d) (?=\d{3}\b)', r'\1' + NB, t)
    t = re.sub(r'(\d)\s+(?=(км|km|м|m|ч|h|мин|min|часов|часа|мест|seats|places|chỗ|giờ|phút|₫|VND|%|человек)\b|₫)', r'\1' + NB, t)
    if lang == 'fr': t = re.sub(r'\s+([:;!?»])', NB + r'\1', t).replace('« ', '«' + NB)
    return t

def jsobj(src, name):
    m = re.search(r'\n  var %s = ([\[{].*?)\n  [\]}];' % name, src, re.S)
    blk = m.group(1) + ('\n]' if m.group(1).startswith('[') else '\n}')
    return json.loads(re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', blk))

def load(src):
    data = {n: jsobj(src, n) for n in ['PROGRAM', 'HM_PROGRAM', 'DOCLET_ROUTE', 'DOCLET_LIST', 'INCLUDED', 'HM_INC']}
    data['DET'] = json.loads(re.search(r'  var DET = (\{.*?\});\n', src).group(1))
    data['TS'] = jsobj(src, 'TS')
    data['PRICE'] = {k: int(v) for k, v in re.findall(r'(\w+): (\d+)', re.search(r'var PRICE = \{([^}]*)\}', src).group(1))}
    data['TOUR_EN'] = json.loads('{' + re.sub(r'(^|,\s*)(\w+):', r'\1"\2":', re.search(r'var TOUR_EN = \{(.*?)\};', src).group(1).strip()) + '}')
    return data

def content(data, tid, lang, d):   # mirrors tsContent() in the page script
    pk = lambda o: o.get(lang, o['ru'])
    tx = lambda k: d.get(k, '')
    if tid in data['DET']:
        x = data['DET'][tid].get(lang, data['DET'][tid]['ru'])
        sp = lambda s: [p.strip() for p in re.split(r',\s*|\.\s+', s.rstrip('.')) if p.strip()]
        return dict(prog=[(a, b) for a, b in x['prog']], incl=sp(x['incl']), extra=sp(x['extra']), note=x['note'], approx=tid != 'x4')
    if tid == 'sea':
        return dict(prog=[(s['time'], pk(s['title'])) for s in data['PROGRAM']], incl=pk(data['INCLUDED']), extra=[], note=tx('note.text'), approx=True)
    if tid == 'cove':
        prog = []
        for r in data['DOCLET_ROUTE']:
            v = pk(r['s']); m = re.search(r'~?\d{1,2}[:h]\d{2}', v)
            rest = re.sub(r'^[\s,]+|[\s,]+$', '', v.replace(m.group(0), '')) if m else v
            prog.append((m.group(0) if m else '', pk(r['t']) + (' · ' + rest if rest else '')))
        l = pk(data['DOCLET_LIST'])
        return dict(prog=prog, incl=re.sub(r'^[^:]*:\s*', '', l[-1]).split(', '), extra=[tx('promo.pickup')], note=tx('doclet.note'), approx=True)
    note = '%s %s: %s — %s; %s — %s; %s — %s.' % (tx('hm.menu.note'), tx('hm.kids.title'), tx('hm.kid1.h'), tx('hm.kid1.p'), tx('hm.kid2.h'), tx('hm.kid2.p'), tx('hm.kid3.h'), tx('hm.kid3.p'))
    return dict(prog=[(s['time'], pk(s['title'])) for s in data['HM_PROGRAM']], incl=pk(data['HM_INC']), extra=[re.sub(r'^[^:]*:\s*', '', tx('hm.notinc'))], note=note, approx=True)

ICO_T = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
ICO_P = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>'
ICO_TG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9.8 15.2l-.4 4.1c.6 0 .8-.3 1.1-.6l2.6-2.5 5.4 4c1 .5 1.7.3 2-.9l3.6-17c.3-1.5-.6-2.1-1.6-1.7L1.4 9.2c-1.4.6-1.4 1.4-.2 1.8l5.4 1.7L19 5c.6-.4 1.1-.2.7.2z"/></svg>'

PAGE_CSS = '''
  header.top{background:rgba(253,249,241,.97);color:var(--navy);box-shadow:0 2px 14px rgba(0,0,0,.08)}
  header.top .logo,header.top .menu a{color:var(--navy)}
  header.top .burger span{background:var(--navy)}
  .tp{padding:96px 0 40px}
  .crumbs{font-size:13.5px;color:var(--muted);margin-bottom:16px;display:flex;flex-wrap:wrap;gap:6px}
  .crumbs a{color:var(--sand-dark);font-weight:600}
  .tp-grid{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:36px;align-items:start}
  .tp-gal{position:relative;border-radius:22px;overflow:hidden;background:#e9e1d1;aspect-ratio:16/9}
  .tp-track{display:flex;height:100%;overflow-x:auto;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .tp-track::-webkit-scrollbar{display:none}
  .tp-track>*{flex:0 0 100%;width:100%;height:100%;scroll-snap-align:start;display:block}
  .tp-track>img{object-fit:cover}
  .tp-slide.fit{position:relative;overflow:hidden;background:#1e2a2c}
  .tp-slide.fit img{position:absolute;inset:0;width:100%;height:100%}
  .tp-slide.fit .bg{object-fit:cover;filter:blur(22px);transform:scale(1.2);opacity:.75}
  .tp-slide.fit .fg{object-fit:contain}
  .tp-hint{position:absolute;right:12px;bottom:12px;background:rgba(30,22,12,.62);color:#fff;font-size:12.5px;font-weight:700;border-radius:999px;padding:4px 10px}
  .tp h1{font-size:clamp(28px,4vw,42px);line-height:1.15;letter-spacing:-.6px;margin:22px 0 12px;text-align:left}
  .tp .tag{position:static;display:inline-block;margin-top:22px}
  .tp h2{font-size:13px;font-weight:800;letter-spacing:1.6px;text-transform:uppercase;color:var(--sand-dark);margin:30px 0 12px;text-align:left}
  .tp-lead{font-size:17px;line-height:1.6;color:var(--navy);margin:14px 0 0}
  .tp-box{position:sticky;top:92px;background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:22px;box-shadow:0 12px 30px rgba(0,0,0,.07)}
  .tp-box .ts-price b{font-size:28px}
  .tp-box .btn{display:flex;width:100%;margin-top:16px;min-height:50px}
  .tp-box .tp-write{font-size:13.5px;color:var(--muted);margin:14px 0 6px}
  .tp-msgs{display:flex;gap:8px;flex-wrap:wrap}
  .tp-msgs a{display:inline-flex;align-items:center;gap:6px;font-size:14px;font-weight:700;color:var(--navy);background:var(--cream);border-radius:999px;padding:8px 12px}
  .tp-msgs svg{width:16px;height:16px;color:var(--sand-dark)}
  .tp-form{background:var(--cream);border-radius:22px;padding:24px;margin-top:34px}
  .tp-form h2{margin-top:0}
  .tp-form p{margin:0 0 14px;color:var(--navy)}
  .tp-form .q-field{display:block;margin-bottom:12px}
  .tp-form .q-field span{display:block;font-size:13.5px;font-weight:700;margin-bottom:6px;color:var(--navy)}
  .tp-form input{width:100%;min-height:48px;border:1px solid var(--line);border-radius:12px;padding:10px 14px;font:inherit;font-size:16px;background:#fff;color:var(--ink)}
  .tp-form .btn{min-height:50px;width:100%}
  .tp-others{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin-top:6px}
  .tp-others a{display:flex;flex-direction:column;background:var(--paper);border-radius:16px;overflow:hidden;color:var(--navy);box-shadow:0 6px 16px rgba(0,0,0,.06)}
  .tp-others img{width:100%;aspect-ratio:16/9;object-fit:cover;background:#e9e1d1}
  .tp-others span{padding:10px 12px 2px;font-weight:700;font-size:15px;line-height:1.3}
  .tp-others small{padding:0 12px 12px;color:var(--sand-dark);font-weight:700}
  .tp-bar{display:none}
  .lang a{color:inherit;font-size:12.5px;font-weight:700;letter-spacing:.3px;padding:6px 8px;border-radius:999px;min-width:36px;min-height:36px;display:inline-flex;align-items:center;justify-content:center;opacity:.8}
  .lang a:hover{opacity:1}
  .lang a.on{opacity:1;background:var(--sand);color:var(--ink)}
  .tp h1{text-shadow:none;color:var(--ink)}
  .tp .ts-facts li,.tp .ts-note{background:var(--paper)}
  .tp-hp{position:absolute;left:-9999px}
  @media (max-width:900px){
    .tp-grid{grid-template-columns:1fr}
    .tp-box{position:static}
    .tp{padding:84px 0 96px}
    .tp-bar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:40;align-items:center;gap:12px;padding:10px 16px calc(10px + env(safe-area-inset-bottom));background:var(--paper);border-top:1px solid var(--line);box-shadow:0 -6px 18px rgba(0,0,0,.08)}
    .tp-bar .ts-price{flex:1}
    .tp-bar .btn{flex:none;min-height:48px;padding:12px 22px}
  }
  @media (max-width:600px){.tp-gal{aspect-ratio:16/10;border-radius:16px;margin:0 -4px}.tp-lead{font-size:16px}}
'''

def page(tid, lang, d, data, ctx):
    e = lambda t: html.escape(typo(t, lang), quote=False)
    ea = lambda t: html.escape(t, quote=True)
    base, url = ctx['BASE'], '%s/%s/tours/%s/' % (ctx['BASE'], lang, SLUG[tid])
    t = data['TS'][tid]; c = content(data, tid, lang, d)
    title = d[t['title']]; lead = d[t['lead']]
    head_title = '%s — %s | PRONET Travel' % (title, WORDS['suffix'][lang])
    desc = (lead[:150] + '…') if len(lead) > 155 else lead
    imgs = [p.replace('|fit', '') for p in t['img']]
    jpgs = [p for p in imgs if p.endswith('.jpg')]
    og = base + (jpgs[0].replace('.jpg', '.webp') if jpgs else '/img/hero.jpg')
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s/%s/tours/%s/">\n' % (l, base, l, SLUG[tid]) for l in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s/en/tours/%s/">\n' % (base, SLUG[tid])
    price, kid = d[t['price']], d[t['pp']]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'TouristTrip', 'name': title, 'description': lead, 'url': url, 'inLanguage': lang,
         **({'image': [base + p.replace('.jpg', '.webp') for p in jpgs[:4]]} if jpgs else {}),
         'itinerary': {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': '%s %s' % (a, b)} for i, (a, b) in enumerate(c['prog'])]},
         'provider': {'@id': base + '/#agency'},
         'offers': {'@type': 'Offer', 'price': data['PRICE'][tid], 'priceCurrency': 'VND', 'availability': 'https://schema.org/InStock', 'url': url}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': WORDS['home'][lang], 'item': '%s/%s/' % (base, lang)},
            {'@type': 'ListItem', 'position': 2, 'name': d['nav.tours'], 'item': '%s/%s/#tours' % (base, lang)},
            {'@type': 'ListItem', 'position': 3, 'name': title, 'item': url}]},
        {'@type': 'TravelAgency', '@id': base + '/#agency', 'name': 'PRONET Travel', 'url': base + '/', 'telephone': '+84389935306',
         'address': {'@type': 'PostalAddress', 'streetAddress': 'Lô 57, đường A3, KĐT VCN Phước Long 2', 'addressLocality': 'Nha Trang', 'addressRegion': 'Khánh Hòa', 'addressCountry': 'VN'}}]}
    ldj = json.dumps(ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    def imgtag(p, i, cls='', sizes='(max-width: 900px) 100vw, 760px'):
        ss = ctx['srcset'](re.sub(r'^/img/|\.jpg$', '', p)) if p.endswith('.jpg') else None
        src = p.replace('.jpg', '.webp')
        return '<img src="%s"%s alt="%s" %s%s>' % (src, (' srcset="%s" sizes="%s"' % (ss, sizes)) if ss else '', ea('%s — %d' % (title, i + 1)),
                                                 'fetchpriority="high"' if i == 0 and not cls else 'loading="lazy"', (' class="%s"' % cls) if cls else '')
    slides = ''
    for i, p in enumerate(t['img']):
        q = p.replace('|fit', '')
        slides += ('<div class="tp-slide fit">%s%s</div>' % (imgtag(q, i, 'bg').replace(' alt="', ' aria-hidden="true" alt="', 1), imgtag(q, i, 'fg'))) if p.endswith('|fit') else imgtag(q, i)
    facts = ''.join('<li>%s<span>%s</span></li>' % (ICO_T if i == 0 else ICO_P, e(d[k])) for i, k in enumerate(t['facts']))
    prog = ''.join('<li><b>%s</b><span>%s</span></li>' % (html.escape(re.sub(r'\s*[–-]\s*', '–', a, count=1)), e(b)) for a, b in c['prog'])
    cap = lambda x: x[:1].upper() + x[1:]
    incl = ''.join('<li>%s</li>' % e(cap(x)) for x in c['incl'] if x)
    extra = ''.join('<li>%s</li>' % e(cap(x)) for x in c['extra'] if x)
    others = ''
    for o in ['sea', 'cove', 'honmun', 'x5', 'x6', 'x2', 'x1', 'x7', 'x3', 'x4']:
        if o == tid: continue
        ot = data['TS'][o]; first = ot['img'][0].replace('|fit', '')
        src = first.replace('.jpg', '.webp'); ss = ctx['srcset'](re.sub(r'^/img/|\.jpg$', '', first)) if first.endswith('.jpg') else None
        others += '<a href="/%s/tours/%s/"><img src="%s"%s alt="" loading="lazy" decoding="async"><span>%s</span><small>%s</small></a>' % (
            lang, SLUG[o], src, (' srcset="%s" sizes="(max-width: 600px) 92vw, 260px"' % ss) if ss else '', e(d[ot['title']]), e(d[ot['price']]))
    langlinks = ''.join('<a href="/%s/tours/%s/" hreflang="%s"%s>%s</a>' % (l, SLUG[tid], l, ' aria-current="true" class="on"' if l == lang else '', l.upper()) for l in ['vi', 'en', 'fr', 'ru'])
    tour_en = data['TOUR_EN'].get(tid, tid)
    lang_en = {'ru': 'Russian', 'en': 'English', 'fr': 'French', 'vi': 'Vietnamese'}[lang]
    return '''<!doctype html>
<html lang="%(lang)s" translate="no" class="notranslate">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(head_title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="%(url)s">
%(alts)s<meta property="og:type" content="website">
<meta property="og:site_name" content="PRONET Travel">
<meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(head_title_a)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:image" content="%(og)s">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/img/logo.png">
<meta name="theme-color" content="#f6f0e4">
%(fonts)s
%(gtm)s
<script type="application/ld+json">%(ld)s</script>
<style>%(css)s%(pcss)s</style>
</head>
<body>
<header class="top solid" id="top-bar">
  <div class="wrap bar">
    <a href="/%(lang)s/" class="logo" aria-label="PRONET Travel"><img src="%(logo)s" alt="" width="46" height="46"><span><b>PRONET</b><small>TRAVEL</small></span></a>
    <nav class="menu" id="menu" aria-label="Main">
      <a href="/%(lang)s/#tours">%(nav_tours)s</a><a href="/%(lang)s/#faq">FAQ</a><a href="/%(lang)s/#about">%(nav_about)s</a><a href="/%(lang)s/#contact">%(nav_contact)s</a>
      <div class="lang lang-menu" role="group" aria-label="Language">%(langlinks)s</div>
    </nav>
    <div class="right">
      <a href="#book" class="btn btn-sand hdr-cta">%(book)s</a>
      <div class="lang" role="group" aria-label="Language">%(langlinks)s</div>
      <button class="burger" id="burger" aria-controls="menu" aria-expanded="false" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<main class="tp">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/%(lang)s/">%(home)s</a><span aria-hidden="true">›</span><a href="/%(lang)s/#tours">%(nav_tours)s</a><span aria-hidden="true">›</span><span>%(title_s)s</span></nav>
    <div class="tp-grid">
      <article>
        <div class="tp-gal"><div class="tp-track">%(slides)s</div>%(hint)s</div>
        <span class="tag">%(tag)s</span>
        <h1>%(title)s</h1>
        <ul class="ts-facts">%(facts)s</ul>
        <p class="tp-lead">%(lead)s</p>
        <h2>%(h_prog)s</h2>
        <ol class="ts-prog">%(prog)s</ol>
        %(approx)s
        <div class="ts-cols">
          <div><h2>%(h_incl)s</h2><ul class="ts-list">%(incl)s</ul></div>
          %(extra_box)s
        </div>
        <h2>%(h_note)s</h2>
        <p class="ts-note">%(note)s</p>
        <form class="tp-form" id="book" novalidate>
          <h2>%(m_title)s</h2>
          <p>%(m_lead)s</p>
          <p class="tp-hp" aria-hidden="true"><label>Don’t fill this out: <input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
          <label class="q-field"><span>%(f_name)s</span><input id="t-name" type="text" autocomplete="name" placeholder="%(f_name_ph)s"></label>
          <label class="q-field"><span>%(f_contact)s</span><input id="t-contact" type="text" autocomplete="tel" placeholder="%(f_contact_ph)s"></label>
          <button class="btn btn-sand btn-shine" type="submit">%(m_submit)s</button>
          <div class="form-msg" id="t-msg" role="status" aria-live="polite"></div>
          <p class="q-note">%(m_note)s</p>
        </form>
      </article>
      <aside class="tp-box">
        <div class="ts-price"><b>%(price)s</b><small>%(kid)s</small></div>
        <a href="#book" class="btn btn-sand btn-shine">%(book)s</a>
        <p class="tp-write">%(write)s</p>
        <div class="tp-msgs"><a href="https://t.me/Boat_nhatrang" target="_blank" rel="noopener">%(ico_tg)s Telegram</a><a href="https://zalo.me/84389935306" target="_blank" rel="noopener">Zalo</a></div>
      </aside>
    </div>
    <h2>%(others_h)s</h2>
    <div class="tp-others">%(others)s</div>
  </div>
</main>
<div class="tp-bar"><div class="ts-price"><b>%(price)s</b><small>%(kid)s</small></div><a href="#book" class="btn btn-sand btn-shine">%(book)s</a></div>
<footer><div class="wrap"><div class="copy">%(rights)s · <a href="/%(lang)s/">PRONET Travel</a></div></div></footer>
<script>
(function () {
  var b = document.getElementById("burger"), m = document.getElementById("menu"), bar = document.getElementById("top-bar");
  b.addEventListener("click", function () { var o = !m.classList.contains("open"); m.classList.toggle("open", o); bar.classList.toggle("open", o); b.setAttribute("aria-expanded", String(o)); });
  var f = document.getElementById("book"), msg = document.getElementById("t-msg"), n = document.getElementById("t-name"), c = document.getElementById("t-contact");
  f.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!n.value.trim() || !c.value.trim()) { msg.className = "form-msg err"; msg.textContent = %(j_check)s; (n.value.trim() ? c : n).focus(); return; }
    var body = ["form-name=contact", "bot-field=", "name=" + encodeURIComponent(n.value.trim()), "contact=" + encodeURIComponent(c.value.trim()),
      "tour=" + encodeURIComponent(%(j_tour)s), "source=" + encodeURIComponent("Tour page, site language: %(lang_en)s")].join("&");
    var btn = f.querySelector("button"); btn.disabled = true; msg.className = "form-msg"; msg.textContent = "…";
    fetch("/", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body })
      .then(function (r) { if (!r.ok) throw 0; msg.className = "form-msg ok"; msg.textContent = %(j_ok)s; f.reset();
        try { window.dataLayer = window.dataLayer || []; window.dataLayer.push({ event: "pt_generate_lead", tour: %(j_tid)s, place: "tour_page" }); } catch (x) {} })
      .catch(function () { msg.className = "form-msg err"; msg.textContent = %(j_err)s; })
      .then(function () { btn.disabled = false; });
  });
})();
</script>
</body>
</html>
''' % dict(lang=lang, head_title=html.escape(head_title), head_title_a=ea(head_title), desc=ea(desc), url=url, alts=alts, og=og, fonts=ctx['fonts'](lang), gtm=ctx['gtm'],
           ld=ldj, css=ctx['css'], pcss=PAGE_CSS, logo=ctx['logo'], nav_tours=e(d['nav.tours']), nav_about=e(d['nav.about']), nav_contact=e(d['nav.contact']),
           langlinks=langlinks, book=e(d['nav.book']), home=e(WORDS['home'][lang]), title_s=e(title), slides=slides,
           hint=('<span class="tp-hint">%d %s</span>' % (len(t['img']), '📷') if len(t['img']) > 1 else ''), tag=e(d[t['tag']]), title=e(title), facts=facts, lead=e(lead),
           h_prog=e(d['det.prog']), prog=prog, approx=('<p class="ts-approx">%s</p>' % e(d['det.approx'])) if c['approx'] else '',
           h_incl=e(d['det.incl']), incl=incl, extra_box=('<div><h2>%s</h2><ul class="ts-list no">%s</ul></div>' % (e(d['det.extra']), extra)) if extra else '',
           h_note=e(d['det.note']), note=e(c['note']), m_title=e(d['m.title']), m_lead=e(d['m.lead']), f_name=e(d['form.name']), f_name_ph=ea(d['form.name.ph']),
           f_contact=e(d['form.contact']), f_contact_ph=ea(d['form.contact.ph']), m_submit=e(d['m.submit']), m_note=e(d['m.note']), price=e(price), kid=e(kid),
           write=e(WORDS['write'][lang]), ico_tg=ICO_TG, others_h=e(WORDS['others'][lang]), others=others, rights=e(d['footer.rights']),
           j_check=json.dumps(d['form.check'], ensure_ascii=False), j_ok=json.dumps(d['form.ok'], ensure_ascii=False), j_err=json.dumps(d['form.err'], ensure_ascii=False),
           j_tour=json.dumps(tour_en), j_tid=json.dumps(tid), lang_en=lang_en)
