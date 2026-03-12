# NMPP Hub Docs Template

Template for a documentation site built with MkDocs and Material for MkDocs.

## Prerequisites

- Python 3.10+
- `pip`

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run locally

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000`.

## Build static site

```bash
mkdocs build
```

The generated site is written to `site/`.

## Customize the website

1. Edit or replace the landing page at `docs/index.md`.
2. Add code pages under `docs/codes/`; they are automatically included under the `Codes` menu.
3. Add non-code pages under `docs/` and register them in `nav` inside `mkdocs.yml`.
