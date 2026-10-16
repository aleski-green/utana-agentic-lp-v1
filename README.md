# Utana Agentic Technologies

Responsive static website for Utana, with a navy and silver design, automation use cases, articles, team profiles, and a pilot enquiry form.

## Run locally

From this directory:

```sh
python3 -m http.server 8766
```

Open http://localhost:8766. No build step or package installation is required.

## Website files

- `index.html`: main landing page
- `services.html` and `services/`: global automation services
- `technology.html`: supported tools and model policy
- `sapiens4.html`: product overview and official website link
- `styles.css` and `navy.css`: shared layout, responsive styles, and colours
- `site.js`: navigation, decorative motion, and enquiry form behaviour
- `use-cases.html`, `use-cases/`, and `use-cases.css`: automation workflow library
- `blog/`: articles linked from the homepage
- `assets/team/`: original team portraits and optimized WebP versions used by the website
- `privacy.html`: privacy information
- `preview-*.html`, `navy.html`, and `blog-navy/`: design variants and alternate pages

## Deploy

Serve this directory from any static web host, with `index.html` at the site root. Include the CSS, JavaScript, articles, use-case pages, and assets. Preview pages are optional for deployment.

## Contact form

The form validates the required contact name, business name, phone, email, and workflow description, then opens an email draft addressed to `sapiens@utana.group`. The visitor must send the draft from their email application. There is no submission backend or database.

Google Fonts are loaded remotely with system-font fallbacks. Workflow articles describe proposed implementations, not measured customer results.

## Local files

The `.gitignore` excludes credentials, editor files, generated archives, and local research/editing notes.

## Image and font performance

Team pages use WebP portraits sized to at most 660 pixels on their longest edge, with explicit dimensions and native lazy loading. Keep the original files as editing sources; use the optimized variants in page markup. The four displayed portraits total approximately 148 KB.

Pages load Google Fonts directly from the document head with preconnections and `display=swap`, avoiding a chained CSS import. When changing shared CSS, update its version query in HTML pages so existing visitors receive the change.

## Search and AI discovery

After changing content or adding a page, run `python3 scripts/build_seo.py`, then `python3 scripts/check_site.py` before committing. The generator reads page titles, descriptions, and visible headings to refresh canonical URLs, Open Graph/Twitter previews, organization/page/service/article/software structured data, and visible breadcrumbs. It also generates `sitemap.xml`, `robots.txt`, and the optional `llms.txt` directory.

Production pages are indexable. Design previews (`preview-*`, `navy.html`, `privacy-navy.html`, and `blog-navy/`) carry `noindex,follow` and are excluded from the sitemap. Legacy meta-refresh pages point to the destination canonical and are also excluded. Do not disallow preview crawling in robots.txt: crawlers must be able to read their noindex directive. The crawler policy permits search and preserves the previous open crawling policy; it does not opt out of model-training crawlers.

The social preview is `assets/social/utana.png` (1200×630). Structured data contains only published company details; no invented reviews, prices, publication dates, vendor partnerships, or customer results. Organizational article authorship is visible. New client evidence should be reviewed before publication.

Search Console and Bing Webmaster Tools ownership verification and sitemap submission require the owner's account. No verification tokens, analytics, or submission backend are configured by this change. The robots and sitemap files alone do not confirm indexing or AI citations.

Sapiens4 copy follows the source-available Sustainable Use License in its repository and links to https://sapiens4.ai/. Do not describe it as unrestricted open-source software or promise remote access beyond the current documented setup.
