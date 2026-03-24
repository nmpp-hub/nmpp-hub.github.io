# NMPP Hub website

## Local setup

```bash
npm install
```

## Run locally

```bash
npm run dev
```

Open `http://localhost:4321`.

## Build static site

```bash
npm run build
```

The generated site is written to `dist/`.

## Add new publications

Add DOIs to `dois.txt` (one per line), then run:

```bash
python populate_publications.py
```

This fetches metadata from doi.org and overwrites the `<tbody>` in `src/pages/publications.astro`.

## Customize the website

1. Edit the landing page at `src/pages/index.astro`.
2. Add code pages under `src/content/codes/`; they are automatically included under the Codes menu and get their own page. Each file needs a `title` frontmatter field:
   ```md
   ---
   title: MyCode
   ---
   Your content here.
   ```
3. Add non-code pages under `src/pages/` and add a nav link in `src/layouts/Base.astro`.
