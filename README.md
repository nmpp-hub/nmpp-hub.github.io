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

## Regenerate generated content

Install the Python dependency once:

```bash
python -m pip install -r requirements.txt
```


- Edit members in `data/members.yml`
- Edit publication entries in `data/dois.yml`
- Edit dissertations in `data/dissertations.yml`

Each publication entry supports optional `groups` and `codes` fields in addition to the DOI. This regenerates all derived website content, including `src/pages/members.astro` from the YAML roster. This regenerates all derived website content, including `src/pages/dissertations.astro` from the YAML list.

## Regenerate generated content

After editing any YAML data files, run:

```bash
python generate_website.py
```

Use `python generate_website.py --refresh` only when you want to re-fetch publication metadata from remote APIs.

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
