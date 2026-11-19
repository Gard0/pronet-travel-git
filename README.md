# PRONET Travel — travel.pronetservicesvn.com

Source of the landing page (4 languages: VI, EN, FR, RU).

- `site2/index.html` — single source page with the i18n dictionary
- `build.py` — builds static language pages `/`, `/ru/`, `/en/`, `/fr/`, `/vi/` into `build/` (WebP images, fonts, SEO)
- `grade.py` — shared colour grading for photos

Build: `pip install pillow && python3 build.py`, then deploy the `build/` folder to Netlify (project calm-frangipane-d75ca6).
