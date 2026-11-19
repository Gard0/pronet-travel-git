# PRONET Travel — travel.pronetservicesvn.com

Source of the landing page (4 languages: VI, EN, FR, RU).

- `site2/index.html` — single source page with the i18n dictionary
- `build.py` — builds static language pages `/`, `/ru/`, `/en/`, `/fr/`, `/vi/` into `build/` (WebP images, fonts, SEO)
- `grade.py` — shared colour grading for photos

Build: `pip install pillow && python3 build.py`, then deploy the `build/` folder to Netlify (project calm-frangipane-d75ca6).

## Deploy

Netlify builds automatically from the `main` branch (`netlify.toml`: `python3 build.py`, publish `build/`; Pillow from `requirements.txt`).
Changes go through pull requests: each PR gets a Netlify deploy preview link; merge to `main` publishes the site.
