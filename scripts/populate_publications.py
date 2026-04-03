from __future__ import annotations

import html
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import (
    build_author_to_slug_map,
    ensure_list,
    escape_text,
    load_yaml,
    publication_base_slug,
    render_author_list,
    render_code_links,
    render_publication_title,
    strip_tags,
    write_text,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "dois.yml"
OUTPUT_FILE = ROOT / "src" / "pages" / "publications" / "index.astro"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
REQUIRED_CACHE_FIELDS = {
    "doi",
    "slug",
    "title",
    "authors",
    "authors_html",
    "venue",
    "journal",
    "year",
    "abstract",
    "bibtex",
    "publisher",
    "volume",
    "issue",
    "pages",
    "url",
    "groups",
    "codes",
}


def normalize_plain_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = value[0] if value else ""
    normalized = html.unescape(strip_tags(str(value)))
    return " ".join(normalized.split())


def normalize_year(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def fetch_doi_content(doi: str, accept: str) -> str:
    req = urllib.request.Request(
        f"https://doi.org/{doi}",
        headers={
            "Accept": accept,
            "User-Agent": "nmpp-publications-generator/1.0",
        },
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def extract_publication_year(data: dict) -> int | None:
    for key in ("published-online", "published-print", "issued", "created"):
        date_info = data.get(key, {})
        if not isinstance(date_info, dict):
            continue
        date_parts = date_info.get("date-parts", [])
        if date_parts and date_parts[0]:
            return normalize_year(date_parts[0][0])
    return None


def extract_author_names(data: dict) -> list[str]:
    names: list[str] = []
    authors = data.get("author", [])
    if not isinstance(authors, list):
        return names

    for author in authors:
        if not isinstance(author, dict):
            continue
        if "family" in author:
            family = normalize_plain_text(author.get("family"))
            given = normalize_plain_text(author.get("given"))
            names.append(f"{given} {family}".strip())
        elif "literal" in author:
            names.append(normalize_plain_text(author["literal"]))
        elif "name" in author:
            names.append(normalize_plain_text(author["name"]))

    return [name for name in names if name]


def fetch_publication_metadata(doi: str) -> dict | None:
    try:
        data = json.loads(fetch_doi_content(doi, "application/vnd.citationstyles.csl+json"))
        try:
            bibtex = fetch_doi_content(doi, "application/x-bibtex; charset=utf-8")
        except Exception:
            bibtex = ""

        title = normalize_plain_text(data.get("title")) or "Unknown"
        authors = extract_author_names(data)
        journal = normalize_plain_text(data.get("container-title"))
        publisher = normalize_plain_text(data.get("publisher"))
        venue = journal or publisher or "Unknown"
        abstract = normalize_plain_text(data.get("abstract"))

        return {
            "doi": doi,
            "slug": "",
            "title": title,
            "authors": ", ".join(authors) or "Unknown",
            "venue": venue,
            "journal": journal,
            "year": extract_publication_year(data),
            "abstract": abstract,
            "bibtex": bibtex.strip(),
            "publisher": publisher,
            "volume": normalize_plain_text(data.get("volume")),
            "issue": normalize_plain_text(data.get("issue")),
            "pages": normalize_plain_text(data.get("page")),
            "url": normalize_plain_text(data.get("URL")) or f"https://doi.org/{doi}",
            "groups": [],
            "codes": [],
        }
    except Exception as exc:
        print(f"Error fetching DOI {doi}: {exc}")
        return None


def load_publication_entries() -> list[dict]:
    raw_entries = load_yaml(DATA_FILE).get("publications", [])
    if not isinstance(raw_entries, list):
        raise ValueError("dois.yml must contain a top-level 'publications' list")

    entries = []
    seen = set()
    for index, raw_entry in enumerate(raw_entries, start=1):
        if isinstance(raw_entry, str):
            doi = raw_entry.strip()
            overrides = {}
        elif isinstance(raw_entry, dict):
            doi = str(raw_entry.get("doi", "")).strip()
            overrides = {
                key: value
                for key, value in raw_entry.items()
                if key != "doi" and value is not None
            }
        else:
            raise ValueError(
                f"Publication entry {index} has invalid type {type(raw_entry).__name__}"
            )

        if not doi:
            raise ValueError(f"Publication entry {index} is missing a DOI")
        if doi in seen:
            continue

        overrides["codes"] = ensure_list(overrides.get("codes", []))
        overrides["groups"] = ensure_list(overrides.get("groups", []))

        entries.append({"doi": doi, "overrides": overrides})
        seen.add(doi)

    return entries


def build_page(publications: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    rows = []
    for publication in publications:
        rows.append(
            "\n".join(
                [
                    "        <tr>",
                    f"          <td>{publication['year'] or ''}</td>",
                    f"          <td>{render_publication_title(publication)}</td>",
                    f"          <td>{render_author_list(publication['authors'], author_to_slug)}</td>",
                    f"          <td>{escape_text(publication['venue'])}</td>",
                    f"          <td>{render_code_links(publication['codes'])}</td>",
                    f"          <td><a href=\"https://doi.org/{escape_text(publication['doi'])}\">DOI</a></td>",
                    "        </tr>",
                ]
            )
        )

    body = "\n".join(rows)
    return f"""---
import Base from '../../layouts/Base.astro';
---

<Base
    title="Publications"
    breadcrumbs={{[
        {{ label: 'Home', href: '/' }},
        {{ label: 'Publications' }},
    ]}}
>
  <div class="page-wrapper">
    <div class="page-header">
      <h1>Publications</h1>
      <p>Search and filter NMPP division publications.</p>
    </div>

    <input id="pub-search" type="search" placeholder="Search by title, author, year, journal, group, code, or keyword..." aria-label="Search publications" />

    <table id="publications-table">
      <thead>
        <tr>
          <th>Year</th>
          <th>Title</th>
          <th>Authors</th>
          <th>Venue</th>
          <th>Codes</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
{body}
      </tbody>
    </table>
  </div>
</Base>

<script>
  document.addEventListener('DOMContentLoaded', function () {{
    const input = document.getElementById('pub-search') as HTMLInputElement | null;
    const table = document.getElementById('publications-table') as HTMLTableElement | null;
    if (!input || !table || !table.tBodies.length) return;
    const rows = Array.from(table.tBodies[0].rows);

    function normalize(text: string) {{
      return text.toLowerCase();
    }}

    input.addEventListener('input', function () {{
      const query = normalize(input.value.trim());
      rows.forEach(row => {{
        const visible = query === '' || normalize(row.textContent ?? '').includes(query);
        row.style.display = visible ? '' : 'none';
      }});
    }});
  }});
</script>
"""


def load_cached_publications() -> dict[str, dict]:
    if not CACHE_FILE.exists():
        return {}

    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    if not isinstance(cache, list):
        return {}

    return {
        publication["doi"]: publication
        for publication in cache
        if isinstance(publication, dict) and isinstance(publication.get("doi"), str)
    }


def cache_needs_refresh(publication: dict) -> bool:
    return any(field not in publication for field in REQUIRED_CACHE_FIELDS)


def assign_publication_slugs(publications: list[dict]) -> None:
    seen: set[str] = set()
    for publication in publications:
        preferred_slug = normalize_plain_text(publication.get("slug"))
        base_slug = (
            publication_base_slug(preferred_slug)
            if preferred_slug
            else publication_base_slug(publication.get("title", ""), publication.get("doi", ""))
        )
        candidate = base_slug or "publication"

        if candidate in seen:
            doi_suffix = publication_base_slug("", publication.get("doi", ""), max_words=12)
            if doi_suffix:
                candidate = f"{base_slug}-{doi_suffix}"

        counter = 2
        while candidate in seen:
            candidate = f"{base_slug}-{counter}"
            counter += 1

        publication["slug"] = candidate
        seen.add(candidate)


def main() -> None:
    entries = load_publication_entries()
    print(f"Found {len(entries)} unique DOI entries")

    cached_pubs = load_cached_publications()
    if cached_pubs:
        print(f"Loaded {len(cached_pubs)} publications from cache")

    publications = []
    for index, entry in enumerate(entries, start=1):
        doi = entry["doi"]
        print(f"[{index}/{len(entries)}] {doi}...", end=" ", flush=True)

        publication = cached_pubs.get(doi, {}).copy()
        was_cached = bool(publication)
        needs_refresh = not was_cached or cache_needs_refresh(publication)

        if needs_refresh:
            fetched = fetch_publication_metadata(doi)
            if fetched is not None:
                publication.update(fetched)
                print("fetched", end=" ")
            elif not publication:
                print("failed")
                continue
            else:
                print("cache-fallback", end=" ")
        else:
            print("cached", end=" ")

        overrides = entry["overrides"]
        for key, value in overrides.items():
            if key not in {"codes", "groups"}:
                publication[key] = value

        publication["doi"] = doi
        publication["title"] = normalize_plain_text(publication.get("title")) or "Unknown"
        publication["authors"] = normalize_plain_text(publication.get("authors")) or "Unknown"
        publication["journal"] = normalize_plain_text(publication.get("journal"))
        publication["publisher"] = normalize_plain_text(publication.get("publisher"))
        publication["venue"] = normalize_plain_text(publication.get("venue")) or publication["journal"] or publication["publisher"] or "Unknown"
        publication["abstract"] = normalize_plain_text(publication.get("abstract"))
        publication["bibtex"] = str(publication.get("bibtex", "")).strip()
        publication["volume"] = normalize_plain_text(publication.get("volume"))
        publication["issue"] = normalize_plain_text(publication.get("issue"))
        publication["pages"] = normalize_plain_text(publication.get("pages"))
        publication["url"] = normalize_plain_text(publication.get("url")) or f"https://doi.org/{doi}"
        publication["year"] = normalize_year(publication.get("year"))
        publication["groups"] = overrides.get("groups", ensure_list(publication.get("groups", [])))
        publication["codes"] = overrides.get("codes", ensure_list(publication.get("codes", [])))
        publications.append(publication)
        print("ok")

    publications.sort(
        key=lambda publication: (
            -(publication["year"] or 0),
            publication["title"].lower(),
            publication["doi"].lower(),
        )
    )
    assign_publication_slugs(publications)

    author_to_slug = build_author_to_slug_map()
    for publication in publications:
        publication["authors_html"] = render_author_list(publication["authors"], author_to_slug)

    write_text(OUTPUT_FILE, build_page(publications, author_to_slug))
    print(f"Updated {OUTPUT_FILE} with {len(publications)} publications")

    CACHE_FILE.write_text(
        json.dumps(publications, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved metadata cache to {CACHE_FILE}")


if __name__ == "__main__":
    main()
