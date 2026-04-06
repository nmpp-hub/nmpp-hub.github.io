# NMPP Hub website

## Local setup

```bash
npm install
```


## Data-driven content and regeneration

All dynamic content (publications, members, dissertations, code links, and group pages) is generated from YAML files in the `data/` directory:

- `data/dois.yml` - publication DOIs and metadata
- `data/members.yml` - member roster
- `data/dissertations.yml` - dissertations
- `data/groups.yml` - research groups

To update the site, simply edit the relevant YAML file(s) and run:

```bash
python -m pip install -r requirements.txt  # first time only
python generate_website.py
```

This will regenerate all derived pages and caches, including:
- Publication index and detail pages: `src/pages/publications/`
- Member list and profiles: `src/pages/members.astro`, `src/pages/members/`
- Dissertations: `src/pages/dissertations.astro`
- Code and group pages: `src/pages/codes/`, `src/pages/groups/`
- Publication cache: `data/.publications_cache.json`

To re-fetch publication metadata from remote APIs (DOI, abstracts, etc) and dissertation BibTeX from mediatum, use:

```bash
python generate_website.py --refresh
```

All generated content is written to the `src/pages/` directory and the publication cache in `data/`. The static site output is in `dist/` after running `npm run build`.
   ```md
   ---
   title: MyCode
   ---
   Your content here.
   ```
3. Add non-code pages under `src/pages/` and add a nav link in `src/layouts/Base.astro`.
