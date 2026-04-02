from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from site_generation import (
    build_author_to_slug_map,
    ensure_list,
    escape_text,
    load_yaml,
    render_author_list,
    render_code_links,
    write_text,
)

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "dois.yml"
OUTPUT_FILE = ROOT / "src" / "pages" / "publications.astro"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"


def fetch_publication_metadata(doi: str) -> dict | None:
    try:
        req = urllib.request.Request(
            f"https://doi.org/{doi}",
            headers={"Accept": "application/vnd.citationstyles.csl+json"},
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        year = None
        for key in ("published-online", "published-print", "issued"):
            date_info = data.get(key, {})
            date_parts = date_info.get("date-parts", [])
            if date_parts and date_parts[0]:
                year = int(date_parts[0][0])
                break

        title = data.get("title")
        if isinstance(title, list):
            title = title[0] if title else "Unknown"

        names = []
        for author in data.get("author", []):
            if "family" in author:
                name = author["family"]
                if "given" in author:
                    name = f"{author['given']} {name}"
                names.append(name)
            elif "literal" in author:
                names.append(author["literal"])
            elif "name" in author:
                names.append(author["name"])

        venue = data.get("container-title") or data.get("publisher") or "Unknown"
        if isinstance(venue, list):
            venue = venue[0] if venue else "Unknown"

        return {
            "year": year,
            "title": title or "Unknown",
            "authors": ", ".join(names),
            "venue": venue,
            "doi": doi,
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
                k: v
                for k, v in raw_entry.items()
                if k != "doi" and v is not None
            }
        else:
            raise ValueError(
                f"Publication entry {index} has invalid type {type(raw_entry).__name__}"
            )

        if not doi:
            raise ValueError(f"Publication entry {index} is missing a DOI")
        if doi in seen:
            continue

        # Normalize list fields
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
                    f"          <td>{publication['year']}</td>",
                    f"          <td>{escape_text(publication['title'])}</td>",
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
import Base from '../layouts/Base.astro';
---

<Base title="Publications">
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
    """Load cached publication metadata indexed by DOI."""
    if not CACHE_FILE.exists():
        return {}
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {p["doi"]: p for p in cache}


def main() -> None:
    entries = load_publication_entries()
    print(f"Found {len(entries)} unique DOI entries")

    # Load existing cache
    cached_pubs = load_cached_publications()
    if cached_pubs:
        print(f"Loaded {len(cached_pubs)} publications from cache")

    publications = []
    for index, entry in enumerate(entries, start=1):
        doi = entry["doi"]
        print(f"[{index}/{len(entries)}] {doi}...", end=" ", flush=True)

        # Try to use cached version first
        if doi in cached_pubs:
            publication = cached_pubs[doi].copy()
            print("cached", end=" ")
        else:
            publication = fetch_publication_metadata(doi)
            if publication is None:
                print("failed")
                continue
            print("fetched", end=" ")

        # YAML-provided fields override fetched/cached metadata
        overrides = entry["overrides"]
        for key in ("title", "authors", "venue", "year"):
            if key in overrides:
                publication[key] = overrides[key]
        publication["groups"] = overrides.get("groups", [])
        publication["codes"] = overrides.get("codes", [])
        publications.append(publication)
        print("ok")

    publications.sort(
        key=lambda publication: (
            -(publication["year"] or 0),
            publication["title"].lower(),
        )
    )

    author_to_slug = build_author_to_slug_map()
    write_text(OUTPUT_FILE, build_page(publications, author_to_slug))
    print(f"Updated {OUTPUT_FILE} with {len(publications)} publications")

    # Save metadata cache for use by generate_code_pages.py
    cache = [
        {
            "doi": p["doi"],
            "title": p["title"],
            "authors": p["authors"],
            "venue": p["venue"],
            "year": p["year"],
            "codes": p["codes"],
        }
        for p in publications
    ]
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved metadata cache to {CACHE_FILE}")


if __name__ == "__main__":
    main()
