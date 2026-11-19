# Builds the deployable site: / (x-default, English preview) + /ru/ /en/ /fr/ /vi/
import re, json, os, shutil, html
SRC = 'site2/index.html'; OUT = 'build'
BASE = 'https://travel.pronetservicesvn.com'
NB = ' '
# title comes from the page dictionary (meta.title); description and og:locale here
SEO = {
 'ru': ('Морские туры в Нячанге от местной команды: три острова и снорклинг, Тайная бухта Гань Няй, Хон Мун, Хон Там, VinWonders. Цены от 640' + NB + '000' + NB + '₫, офис в Нячанге.', 'ru_RU'),
 'en': ('Nha Trang boat tours by a local team: island trips with snorkelling, Ganh Nhay Secret Cove, Hon Tam mud baths, VinWonders. From 640,000 ₫.', 'en_US'),
 'fr': ('Excursions en mer à Nha Trang avec une équipe locale' + NB + ': îles et snorkeling, crique de Ganh Nhay, bains de boue de Hon Tam, VinWonders. Dès 640' + NB + '000' + NB + '₫.', 'fr_FR'),
 'vi': ('Tour biển Nha Trang của đội ngũ địa phương: tour đảo lặn ngắm san hô, Gành Nhảy, tắm bùn Hòn Tằm, VinWonders. Giá từ 640.000đ.', 'vi_VN'),
}
SEO['x'] = SEO['en']

src = open(SRC, encoding='utf-8').read()

# read the four dictionaries from the page's own script
def dict_for(lang):
    st = src.index('var I18N = {')
    a = src.index('    %s: {' % lang, st)
    b = src.index('\n    }', a)
    return {k: json.loads('"%s"' % v) for k, v in re.findall(r'"([^"]+)":\s*"((?:[^"\\]|\\.)*)"', src[a:b])}
D = {l: dict_for(l) for l in ['ru', 'en', 'fr', 'vi']}


# ---- structured data (schema.org) in the page's language: the agency, the tours with prices, the FAQ ----
def js_array(name):
    blk = re.search(r'  var %s = (\[.*?\n  \]);' % name, src, re.S).group(1)
    blk = re.sub(r'([{,]\s*)([A-Za-z_]+):', r'\1"\2":', blk)
    return json.loads(blk)
FAQ = js_array('FAQ')
TS_META = re.search(r'  var TS = \{(.*?)\n  \};', src, re.S).group(1)
TOURS = []   # (id, title key, lead key, price, first photos)
for m in re.finditer(r'(\w+):\s*\{ img: \[([^\]]*)\],\s*tag: "[^"]*", title: "([^"]*)", lead: "([^"]*)"', TS_META):
    TOURS.append((m.group(1), m.group(3), m.group(4), re.findall(r'"([^"]+)"', m.group(2))))
PRICES = {k: int(v) for k, v in re.findall(r'(\w+): (\d+)', re.search(r'var PRICE = \{([^}]*)\}', src).group(1))}
def absimg(p):
    return BASE + re.sub(r'\.jpg$', '.webp', p)
def jsonld(lang, url, d):
    org = BASE + '/#agency'
    g = [{
        '@type': 'TravelAgency', '@id': org, 'name': 'PRONET Travel', 'legalName': 'CÔNG TY TNHH PRONET SERVICES',
        'url': BASE + '/', 'logo': BASE + '/img/logo.png', 'image': BASE + '/img/hero.jpg', 'telephone': '+84389935306',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Lô 57, đường A3, KĐT VCN Phước Long 2', 'addressLocality': 'Nha Trang', 'addressRegion': 'Khánh Hòa', 'addressCountry': 'VN'},
        'geo': {'@type': 'GeoCoordinates', 'latitude': 12.2172849, 'longitude': 109.1821677},
        'hasMap': 'https://www.google.com/maps/place/C%C3%B4ng+ty+TNHH+Pronet+Services/@12.2172849,109.1821677,18z/data=!4m6!3m5!1s0x31705d0a87f86039:0x5287dd2b9c3a6234!8m2!3d12.2172849!4d109.1821677!16s%2Fg%2F11z87fyy1q',
        'areaServed': 'Nha Trang, Khánh Hòa', 'currenciesAccepted': 'VND', 'priceRange': '640 000 – 9 500 000 VND',
        'sameAs': ['https://t.me/Boat_nhatrang', 'https://www.facebook.com/profile.php?id=61594450346439', 'https://zalo.me/84389935306']},
      {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': d['meta.title'], 'description': SEO[lang][0], 'inLanguage': lang,
       'isPartOf': {'@type': 'WebSite', '@id': BASE + '/#site', 'url': BASE + '/', 'name': 'PRONET Travel', 'publisher': {'@id': org}},
       'about': {'@id': org}, 'primaryImageOfPage': BASE + '/img/hero.jpg'},
      {'@type': 'ItemList', 'name': d.get('tours.kicker', 'Tours'), 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'url': url + '#tour-' + tid, 'item': {
          '@type': 'TouristTrip', 'name': d.get(tk, tid), 'description': d.get(lk, ''), **({'image': [absimg(p) for p in imgs if p.endswith('.jpg')][:3]} if any(p.endswith('.jpg') for p in imgs) else {}),
          'provider': {'@id': org}, 'touristType': 'Leisure',
          'offers': {'@type': 'Offer', 'price': PRICES.get(tid), 'priceCurrency': 'VND', 'availability': 'https://schema.org/InStock', 'url': url + '#tour-' + tid, 'seller': {'@id': org}}}}
        for i, (tid, tk, lk, imgs) in enumerate(TOURS)]},
      {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': f['q'].get(lang, f['q']['ru']), 'acceptedAnswer': {'@type': 'Answer', 'text': f['a'].get(lang, f['a']['ru'])}} for f in FAQ]}]
    data = json.dumps({'@context': 'https://schema.org', '@graph': g}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return '<script type="application/ld+json">%s</script>' % data

def seo_block(key, url, title):
    desc, loc = SEO[key]
    e = lambda t: html.escape(t, quote=True)
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s/%s/">\n' % (l, BASE, l) for l in ['ru', 'en', 'fr', 'vi'])
    alts += '<link rel="alternate" hreflang="x-default" href="%s/">\n' % BASE
    return ('<meta name="description" content="%s">\n<meta name="robots" content="index, follow, max-image-preview:large">\n<link rel="canonical" href="%s">\n%s'
            '<meta property="og:type" content="website">\n<meta property="og:site_name" content="PRONET Travel">\n'
            '<meta property="og:url" content="%s">\n<meta property="og:locale" content="%s">\n'
            '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
            '<meta property="og:image" content="%s/img/hero.jpg">\n<meta property="og:image:width" content="1280">\n<meta property="og:image:height" content="720">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<meta name="twitter:title" content="%s">\n<meta name="twitter:description" content="%s">\n<meta name="twitter:image" content="%s/img/hero.jpg">'
            % (e(desc), url, alts, url, loc, e(title), e(desc), BASE, e(title), e(desc), BASE))

import base64, io
from PIL import Image as _I
_buf = io.BytesIO(); _I.open('site2/img/logo.png').convert('RGB').save(_buf, 'WEBP', quality=86); LOGO = 'data:image/webp;base64,' + base64.b64encode(_buf.getvalue()).decode()
def page(lang, key, url):
    s = src
    d = D[lang]
    html_end = s.index('<script>\n(function')
    body, script = s[:html_end], s[html_end:]
    # bake the page's own language into the static HTML (what crawlers and no-JS visitors see)
    body = re.sub(r'(data-i18n="([^"]+)"[^>]*>)[^<]*(<)', lambda m: m.group(1) + html.escape(d.get(m.group(2), ''), quote=False) + m.group(3) if m.group(2) in d else m.group(0), body)
    body = re.sub(r'(data-i18n-ph="([^"]+)"[^>]*?placeholder=")[^"]*(")', lambda m: m.group(1) + html.escape(d.get(m.group(2), ''), quote=True) + m.group(3), body)
    body = re.sub(r'(placeholder=")[^"]*("[^>]*?data-i18n-ph="([^"]+)")', lambda m: m.group(1) + html.escape(d.get(m.group(3), ''), quote=True) + m.group(2), body)
    body = re.sub(r'<html lang="[a-z]+"', '<html lang="%s"' % lang, body, count=1)
    body = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % html.escape(d['meta.title']), body, count=1)
    def card_alt(m):   # photo alt text of a tour card = the tour's title in this language
        art = m.group(0); k = re.search(r'<h3 data-i18n="([^"]+)"', art)
        if not k: return art
        return re.sub(r'(<a class="card-img"[^>]*>\s*<img [^>]*?)alt="[^"]*"', lambda n: n.group(1) + 'alt="%s"' % html.escape(d.get(k.group(1), ''), quote=True), art, count=1)
    body = re.sub(r'<article class="card[^"]*">.*?</article>', card_alt, body, flags=re.S)
    body = body.replace('<img src="/img/logo.png" alt="" width="46" height="46">', '<img src="%s" alt="" width="46" height="46">' % LOGO)   # tiny inline logo: no request, paints at once
    body = body.replace('<!--SEO-->', seo_block(key, url, d['meta.title']) + '\n' + jsonld(lang, url, d))
    fonts = ['latin'] + {'ru': ['cyrillic'], 'vi': ['vietnamese'], 'fr': [], 'en': []}[lang]
    body = body.replace('<!--FONTPRELOAD-->', '\n'.join('<link rel="preload" as="font" type="font/woff2" href="/fonts/manrope-%s.woff2" crossorigin>' % f for f in fonts))
    # serve WebP copies of every photo (made below); OG/Twitter images stay JPEG for link previews
    body = re.sub(r'(?<!\.com)/img/([A-Za-z0-9_.-]+)\.jpg', r'/img/\1.webp', body)
    script = re.sub(r'/img/([A-Za-z0-9_.-]+)\.jpg', r'/img/\1.webp', script)
    # responsive images: <img sizes=...> without srcset gets the WebP widths made below
    def add_srcset(m):
        tag = m.group(0)
        if 'srcset=' in tag or 'sizes=' not in tag: return tag
        name = re.search(r'src="/img/([A-Za-z0-9_.-]+)\.webp"', tag)
        ss = name and srcset(name.group(1))
        return tag.replace(' sizes=', ' srcset="%s" sizes=' % ss, 1) if ss else tag
    body = re.sub(r'<img [^>]+>', add_srcset, body)
    script = script.replace('{}/*IMGW*/', json.dumps(WIDTHS, separators=(',', ':')))
    for b in ['ru', 'en', 'fr', 'vi']:   # pressed state of the language buttons
        body = body.replace('data-lang="%s" aria-pressed="%s"' % (b, 'true' if b == 'ru' else 'false'),
                            'data-lang="%s" aria-pressed="%s"' % (b, 'true' if b == lang else 'false'))
    return body + script

if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copytree('site2/img', OUT + '/img')
shutil.copy('site2/_headers', OUT + '/_headers')
shutil.copytree('site2/fonts', OUT + '/fonts')
from PIL import Image
from grade import grade
# only photos the page uses are processed and published (plus hero.jpg for link previews)
USED = set(re.findall(r'/img/([A-Za-z0-9_.-]+)\.jpg', src)) | {'hero'}
WIDTHS = {}   # name -> widths available as WebP, smallest first; the full size is <name>.webp
for fn in sorted(os.listdir(OUT + '/img')):
    if fn.endswith('.jpg') and fn[:-4] in USED:
        im = Image.open(OUT + '/img/' + fn)
        if not fn.startswith('license'):   # documents stay as scanned
            im = grade(im, sharpen=fn.startswith(('sea-', 'real-')))
        im = im.convert('RGB')
        im.save(OUT + '/img/' + fn[:-4] + '.webp', 'WEBP', quality=74, method=6)
        ws = [] if fn.startswith('hero') else [w for w in (480, 960) if im.width >= w * 1.25]
        for w in ws:
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(OUT + '/img/%s-%d.webp' % (fn[:-4], w), 'WEBP', quality=74, method=6)
        if ws: WIDTHS[fn[:-4]] = ws + [im.width]
def srcset(name):
    w = WIDTHS.get(name)
    return w and ', '.join('/img/%s%s.webp %dw' % (name, '' if i == len(w) - 1 else '-%d' % x, x) for i, x in enumerate(w))
open(OUT + '/index.html', 'w', encoding='utf-8').write(page('en', 'x', BASE + '/'))
for l in ['ru', 'en', 'fr', 'vi']:
    os.makedirs('%s/%s' % (OUT, l))
    open('%s/%s/index.html' % (OUT, l), 'w', encoding='utf-8').write(page(l, l, '%s/%s/' % (BASE, l)))
# sitemap with language alternates, robots.txt
import datetime
today = datetime.date.today().isoformat()
alts = ''.join('<xhtml:link rel="alternate" hreflang="%s" href="%s/%s/"/>' % (l, BASE, l) for l in ['ru', 'en', 'fr', 'vi']) + '<xhtml:link rel="alternate" hreflang="x-default" href="%s/"/>' % BASE
urls = ''.join('<url><loc>%s</loc><lastmod>%s</lastmod>%s</url>' % (u, today, alts) for u in [BASE + '/'] + ['%s/%s/' % (BASE, l) for l in ['ru', 'en', 'fr', 'vi']])
open(OUT + '/sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">%s</urlset>\n' % urls)
open(OUT + '/robots.txt', 'w').write('User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % BASE)
# drop files no page refers to (unused photos, JPEG originals already served as WebP)
pages = ''.join(open(os.path.join(r, f), encoding='utf-8').read() for r, _, fs in os.walk(OUT) for f in fs if f.endswith('.html'))
refs = set(re.findall(r'/img/([A-Za-z0-9_.-]+)', pages)) | {'hero.jpg'}
for fn in os.listdir(OUT + '/img'):
    base = re.sub(r'-(480|960)\.webp$', '.webp', fn)
    if fn not in refs and not (base != fn and base in refs):
        os.remove(OUT + '/img/' + fn)
print('built:', sorted(os.listdir(OUT)), len(os.listdir(OUT + '/img')), 'images')
