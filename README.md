# PRONET Travel — travel.pronetservicesvn.com

Source of the landing page (4 languages: VI, EN, FR, RU).

- `site2/index.html` — single source page with the i18n dictionary
- `build.py` — builds static language pages `/`, `/ru/`, `/en/`, `/fr/`, `/vi/` into `build/` (WebP images, fonts, SEO)
- `grade.py` — shared colour grading for photos
- `tourpages.py` — one page per tour and language (`/ru/tours/<slug>/` …), built from the same data as the tour window on the main page

Build: `pip install pillow && python3 build.py`, then deploy the `build/` folder to Netlify (project calm-frangipane-d75ca6).

## Deploy

Netlify builds automatically from the `main` branch (`netlify.toml`: `python3 build.py`, publish `build/`; Pillow from `requirements.txt`).
Changes go through pull requests: each PR gets a Netlify deploy preview link; merge to `main` publishes the site.

## Checks

Start a local server on the build (`python3 -m http.server 8772 --directory build`), then:

- `node tests/sheet.js` — every tour card opens its window on desktop, iPhone and Android; gallery, Back button, deep links (`#tour-sea`), booking hand-off
- `node tests/regress.js` — 4 languages × 3 widths: no sideways scroll, no broken images, no JS errors, anchors, quick booking
- `node tests/perf.js http://localhost:8772/ru/` — FCP / LCP / CLS / KB on a throttled phone
- `node tests/tourpages.js` — all 40 tour pages: no errors, no sideways scroll, images, booking form, links
- `node tests/esim_menu.js` — eSIM window, menu closes when booking opens
- `node tests/typo.js`, `node tests/words.js` — line breaks: hanging short words, buttons on 2 lines, words split across lines
