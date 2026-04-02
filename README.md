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

Install the Python dependency once:

```bash
python -m pip install -r requirements.txt
```

Add or edit entries in `data/dois.yml`, then run:

```bash
python populate_publications.py
```

Each publication entry supports optional `groups` and `codes` fields in addition to the DOI.

## Update members

Edit `data/members.yml`, then run:

```bash
python generate_members_page.py
```

This regenerates `src/pages/members.astro` from the YAML roster.

## Update dissertations

Edit `data/dissertations.yml`, then run:

```bash
python generate_dissertations_page.py
```

This regenerates `src/pages/dissertations.astro` from the YAML list.

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
