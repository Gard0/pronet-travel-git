# Builds the deployable site: / (x-default, English preview) + /ru/ /en/ /fr/ /vi/
import re, json, os, shutil, html
SRC = 'site2/index.html'; OUT = 'build'
BASE = 'https://travel.pronetservicesvn.com'
NB = ' '
SEO = {
 'ru': ('PRONET Travel — морские туры в Нячанге',
        'Три тура: морской тур по трём островам, Тайная бухта Гань Няй и Хон Мун с рыбацкой деревней. Настоящие фото с наших поездок, цены и доплаты заранее.', 'ru_RU'),
 'en': ('PRONET Travel — sea tours in Nha Trang',
        'Three tours: the three-island sea tour, Ganh Nhay Secret Cove and Hon Mun with a fishing village. Real photos from our trips, prices and extras up front.', 'en_US'),
 'fr': ('PRONET Travel — excursions en mer à Nha Trang',
        'Trois excursions'+NB+': la sortie en mer sur trois îles, la crique secrète de Ganh Nhay et Hon Mun avec un village de pêcheurs. De vraies photos de nos sorties, prix et suppléments annoncés.', 'fr_FR'),
 'vi': ('PRONET Travel — tour biển Nha Trang',
        'Ba tour: tour biển 3 đảo, Gành Nhảy – góc biển riêng tư và Hòn Mun cùng làng chài. Ảnh thật từ các chuyến đi, giá và phụ phí báo trước.', 'vi_VN'),
 'x':  ('PRONET Travel — Nha Trang sea tours · Tour biển Nha Trang',
        'Three tours: the three-island sea tour, Ganh Nhay Secret Cove and Hon Mun with a fishing village. Real photos from our trips. RU · EN · FR · VI', 'en_US'),
}
src = open(SRC, encoding='utf-8').read()

# read the four dictionaries from the page's own script
def dict_for(lang):
    st = src.index('var I18N = {')
    a = src.index('    %s: {' % lang, st)
    b = src.index('\n    }', a)
    return {k: json.loads('"%s"' % v) for k, v in re.findall(r'"([^"]+)":\s*"((?:[^"\\]|\\.)*)"', src[a:b])}
D = {l: dict_for(l) for l in ['ru', 'en', 'fr', 'vi']}

def seo_block(key, url):
    title, desc, loc = SEO[key]
    e = lambda t: html.escape(t, quote=True)
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s/%s/">\n' % (l, BASE, l) for l in ['ru', 'en', 'fr', 'vi'])
    alts += '<link rel="alternate" hreflang="x-default" href="%s/">\n' % BASE
    return ('<meta name="description" content="%s">\n<link rel="canonical" href="%s">\n%s'
            '<meta property="og:type" content="website">\n<meta property="og:site_name" content="PRONET Travel">\n'
            '<meta property="og:url" content="%s">\n<meta property="og:locale" content="%s">\n'
            '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
            '<meta property="og:image" content="%s/img/hero.jpg">\n<meta property="og:image:width" content="1280">\n<meta property="og:image:height" content="720">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<meta name="twitter:title" content="%s">\n<meta name="twitter:description" content="%s">\n<meta name="twitter:image" content="%s/img/hero.jpg">'
            % (e(desc), url, alts, url, loc, e(title), e(desc), BASE, e(title), e(desc), BASE))

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
    body = body.replace('<!--SEO-->', seo_block(key, url))
    fonts = ['latin'] + {'ru': ['cyrillic'], 'vi': ['vietnamese'], 'fr': [], 'en': []}[lang]
    body = body.replace('<!--FONTPRELOAD-->', '\n'.join('<link rel="preload" as="font" type="font/woff2" href="/fonts/manrope-%s.woff2" crossorigin>' % f for f in fonts))
    # serve WebP copies of every photo (made below); OG/Twitter images stay JPEG for link previews
    body = re.sub(r'(?<!\.com)/img/([A-Za-z0-9_.-]+)\.jpg', r'/img/\1.webp', body)
    script = re.sub(r'/img/([A-Za-z0-9_.-]+)\.jpg', r'/img/\1.webp', script)
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
for fn in os.listdir(OUT + '/img'):
    if fn.endswith('.jpg'):
        im = Image.open(OUT + '/img/' + fn)
        if not fn.startswith('license'):   # documents stay as scanned
            im = grade(im, sharpen=fn.startswith(('sea-', 'real-')))
        im.convert('RGB').save(OUT + '/img/' + fn[:-4] + '.webp', 'WEBP', quality=74, method=6)
open(OUT + '/index.html', 'w', encoding='utf-8').write(page('en', 'x', BASE + '/'))
for l in ['ru', 'en', 'fr', 'vi']:
    os.makedirs('%s/%s' % (OUT, l))
    open('%s/%s/index.html' % (OUT, l), 'w', encoding='utf-8').write(page(l, l, '%s/%s/' % (BASE, l)))
print('built:', sorted(os.listdir(OUT)))
