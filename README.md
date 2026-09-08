# Rajneil Baruah — academic website

A lightweight static research website designed for GitHub Pages or any static host.

## What updates automatically?

`data/publications.json` is refreshed from the INSPIRE-HEP REST API by the GitHub Action in `.github/workflows/update-publications.yml`.

INSPIRE-HEP is the primary source used for the publication feed because it is the natural bibliographic record for HEP. ORCID, Google Scholar, arXiv and INSPIRE remain linked as external profiles.

## What stays manual?

- `data/current-work.json` — edit this whenever your active projects change.
- `data/talks.json` — add talks and presentation links here.
- `data/publications.json` is generated; do not edit it by hand except as a temporary fallback before the first GitHub Action run.

## Important edits before publishing

1. Put the current CV at `RAJNEILCV.pdf`.
2. Replace `YOUR_INSTAGRAM_URL` in `app.js` with the Instagram URL you want to expose — or leave it as-is to hide the link.
3. Review the prose in `index.html` and update the PhD end date / affiliation details when appropriate.
4. Push to GitHub and enable GitHub Pages.
5. The publication action runs twice daily and can also be run manually from **Actions → Update publications → Run workflow**.

## Why INSPIRE rather than calling arXiv directly from the browser?

The site is static, so a scheduled server-side refresh is more reliable than depending on a browser making live cross-origin requests every time a visitor opens the page. The GitHub Action keeps the site files current, while the public page remains fast and simple.
