from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import (build_author_to_slug_map, ensure_list,
                             escape_text, load_yaml, publication_base_slug,
                             render_author_list, render_code_links,
                             render_publication_title, strip_tags, write_text)

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


CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"
OPENALEX_API = "https://api.openalex.org/works"
CROSSREF_USER_AGENT = (
    "nmpp-publications-generator/1.0 (mailto:webmaster@nmpp-hub.github.io)"
)


def fetch_doi_content(doi: str, accept: str) -> str:
    req = urllib.request.Request(
        f"https://doi.org/{doi}",
        headers={
            "Accept": accept,
            "User-Agent": CROSSREF_USER_AGENT,
        },
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def _fetch_url_json(url: str, extra_headers: dict | None = None) -> dict:
    headers = {"User-Agent": CROSSREF_USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_abstract_from_semantic_scholar(doi: str) -> str:
    """Query the Semantic Scholar Graph API for an abstract."""
    try:
        data = _fetch_url_json(
            f"{SEMANTIC_SCHOLAR_API}/DOI:{doi}?fields=abstract",
            extra_headers={"Accept": "application/json"},
        )
        return normalize_plain_text(data.get("abstract") or "")
    except Exception:
        return ""


def fetch_abstract_from_openalex(doi: str) -> str:
    """Query the OpenAlex API and reconstruct abstract from inverted index."""
    try:
        data = _fetch_url_json(f"{OPENALEX_API}/https://doi.org/{doi}")
        inv = data.get("abstract_inverted_index") or {}
        if not inv:
            return ""
        size = max(pos for positions in inv.values() for pos in positions) + 1
        words: list[str] = [""] * size
        for word, positions in inv.items():
            for pos in positions:
                words[pos] = word
        return normalize_plain_text(" ".join(words))
    except Exception:
        return ""


def fetch_abstract_fallbacks(doi: str) -> str:
    """Try Semantic Scholar then OpenAlex to find a missing abstract."""
    abstract = fetch_abstract_from_semantic_scholar(doi)
    if abstract:
        return abstract
    return fetch_abstract_from_openalex(doi)


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
        data = json.loads(
            fetch_doi_content(doi, "application/vnd.citationstyles.csl+json")
        )
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


def build_page(
    publications: list[dict], author_to_slug: dict[str, str] | None = None
) -> str:
    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    # Build table rows
    table_rows = []
    for publication in publications:
        venue = escape_text(publication["venue"])
        codes = render_code_links(publication["codes"])
        doi_link = (
            f"<a href=\"https://doi.org/{escape_text(publication['doi'])}\">DOI</a>"
        )
        details = f"{venue}"
        if codes:
            details += f" · {codes}"
        details += f" · {doi_link}"

        row = f"""    <tr>
      <td>{publication['year'] or ''}</td>
      <td>{render_publication_title(publication)}</td>
      <td>{render_author_list(publication['authors'], author_to_slug)}</td>
      <td>{details}</td>
    </tr>"""
        table_rows.append(row)

    table_body = "\n".join(table_rows)

    # Build cards
    cards = []
    for publication in publications:
        venue = escape_text(publication["venue"])
        codes = render_code_links(publication["codes"])
        doi_link = (
            f"<a href=\"https://doi.org/{escape_text(publication['doi'])}\">DOI</a>"
        )
        details = f"{venue}"
        if codes:
            details += f" · {codes}"
        details += f" · {doi_link}"

        card = f"""
        <div class="publication-card">
          <div class="publication-card-header">
            <div class="publication-card-year">{publication['year'] or ''}</div>
            <div class="publication-card-title">{render_publication_title(publication)}</div>
            <div class="publication-card-authors">{render_author_list(publication['authors'], author_to_slug)}</div>
            <div class="publication-card-details">
              {details}
            </div>
          </div>
        </div>
        """
        cards.append(card.strip())

    cards_body = "\n".join(cards)

    return f"""---
import Base from '../../layouts/Base.astro';
import PageLayout from '../../components/PageLayout.astro';

const path = Astro.url.pathname;
const leftNav = [{{
  heading: 'Navigate',
  items: [
    {{ href: '/', label: 'Home', active: path === '/' }},
    {{ href: '/codes/', label: 'Codes', active: path.startsWith('/codes') }},
    {{ href: '/groups/', label: 'Groups', active: path.startsWith('/groups') }},
    {{ href: '/members/', label: 'Members', active: path.startsWith('/members') }},
    {{ href: '/publications/', label: 'Publications', active: path.startsWith('/publications') }},
    {{ href: '/dissertations/', label: 'Dissertations', active: path.startsWith('/dissertations') }},
    {{ href: '/about/', label: 'About', active: path.startsWith('/about') }},
  ],
}}];
---

<Base
    title="Publications"
    breadcrumbs={{[
        {{ label: 'Home', href: '/' }},
        {{ label: 'Publications' }},
    ]}}
>
  <div class="page-wrapper">
    <PageLayout leftNav={{leftNav}}>
    <div class="page-header">
      <h1>Publications</h1>
      <p>Search and filter NMPP division publications.</p>
    </div>

    <input id="pub-search" type="search" placeholder="Search by title, author, year, journal, group, code, or keyword..." aria-label="Search publications" />

    <table id="publications-table" class="publications-table">
      <thead>
        <tr>
          <th>Year</th>
          <th>Title</th>
          <th>Authors</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
{table_body}
      </tbody>
    </table>

    <div id="publications-cards" class="publication-cards">
{cards_body}
    </div>
    </PageLayout>
  </div>
</Base>

<script>
  document.addEventListener('DOMContentLoaded', function () {{
    const input = document.getElementById('pub-search') as HTMLInputElement | null;
    const table = document.getElementById('publications-table') as HTMLTableElement | null;
    const cardsContainer = document.getElementById('publications-cards') as HTMLElement | null;
    if (!input) return;

    function normalize(text: string) {{
      return text.toLowerCase();
    }}

    input.addEventListener('input', function () {{
      const query = normalize(input.value.trim());

      // Handle table rows
      if (table) {{
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        rows.forEach(row => {{
          const visible = query === '' || normalize(row.textContent ?? '').includes(query);
          row.style.display = visible ? '' : 'none';
        }});
      }}

      // Handle cards
      if (cardsContainer) {{
        const cards = Array.from(cardsContainer.querySelectorAll('.publication-card'));
        cards.forEach(card => {{
          const visible = query === '' || normalize(card.textContent ?? '').includes(query);
          card.style.display = visible ? '' : 'none';
        }});
      }}
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
            else publication_base_slug(
                publication.get("title", ""), publication.get("doi", "")
            )
        )
        candidate = base_slug or "publication"

        if candidate in seen:
            doi_suffix = publication_base_slug(
                "", publication.get("doi", ""), max_words=12
            )
            if doi_suffix:
                candidate = f"{base_slug}-{doi_suffix}"

        counter = 2
        while candidate in seen:
            candidate = f"{base_slug}-{counter}"
            counter += 1

        publication["slug"] = candidate
        seen.add(candidate)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate publications cache and generate index page."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch metadata from DOI for missing or incomplete cache entries",
    )
    parser.add_argument(
        "--fill-abstracts",
        action="store_true",
        help="Try Semantic Scholar / OpenAlex to fill in missing abstracts without a full re-fetch",
    )
    parser.add_argument(
        "--doi",
        metavar="DOI",
        nargs="+",
        help="Limit processing to these specific DOIs (useful with --fill-abstracts for quick tests)",
    )
    args = parser.parse_args()

    entries = load_publication_entries()
    print(f"Found {len(entries)} unique DOI entries")

    # When --doi is given, filter the list immediately
    if args.doi:
        doi_filter = {d.strip() for d in args.doi}
        entries = [e for e in entries if e["doi"] in doi_filter]
        print(f"Filtered to {len(entries)} DOI(s) via --doi")

    cached_pubs = load_cached_publications()
    if cached_pubs:
        print(f"Loaded {len(cached_pubs)} publications from cache")

    # --fill-abstracts: patch only the abstract field for publications that are
    # missing one, without touching any other cached data.
    if args.fill_abstracts:
        targets = {
            e["doi"]: cached_pubs[e["doi"]]
            for e in entries
            if e["doi"] in cached_pubs
            and not cached_pubs[e["doi"]].get("abstract", "").strip()
        }
        if not targets:
            print(
                "No publications with missing abstracts found in the given selection."
            )
        else:
            print(f"Attempting to fill abstracts for {len(targets)} publication(s)…")
            filled = 0
            for idx, (doi, pub) in enumerate(targets.items(), start=1):
                print(f"  [{idx}/{len(targets)}] {doi}...", end=" ", flush=True)
                abstract = fetch_abstract_fallbacks(doi)
                if abstract:
                    pub["abstract"] = abstract
                    cached_pubs[doi]["abstract"] = abstract
                    filled += 1
                    print(f"found ({len(abstract)} chars)")
                else:
                    print("not found")
            print(f"Filled {filled}/{len(targets)} abstracts")

        # Rebuild authors_html and regenerate outputs even if nothing changed
        all_pubs = list(cached_pubs.values())
        all_pubs.sort(
            key=lambda p: (
                -(p.get("year") or 0),
                p.get("title", "").lower(),
                p.get("doi", "").lower(),
            )
        )
        assign_publication_slugs(all_pubs)
        author_to_slug = build_author_to_slug_map()
        for pub in all_pubs:
            pub["authors_html"] = render_author_list(
                pub.get("authors", ""), author_to_slug
            )
        write_text(OUTPUT_FILE, build_page(all_pubs, author_to_slug))
        print(f"Updated {OUTPUT_FILE} with {len(all_pubs)} publications")
        CACHE_FILE.write_text(
            json.dumps(all_pubs, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Saved metadata cache to {CACHE_FILE}")
        return

    publications = []
    for index, entry in enumerate(entries, start=1):
        doi = entry["doi"]
        print(f"[{index}/{len(entries)}] {doi}...", end=" ", flush=True)

        publication = cached_pubs.get(doi, {}).copy()
        was_cached = bool(publication)
        needs_refresh = args.refresh and (
            not was_cached or cache_needs_refresh(publication)
        )

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
        elif not was_cached:
            print("not in cache (run with --refresh to fetch)")
            continue
        else:
            print("cached", end=" ")

        overrides = entry["overrides"]
        for key, value in overrides.items():
            if key not in {"codes", "groups"}:
                publication[key] = value

        publication["doi"] = doi
        publication["title"] = (
            normalize_plain_text(publication.get("title")) or "Unknown"
        )
        publication["authors"] = (
            normalize_plain_text(publication.get("authors")) or "Unknown"
        )
        publication["journal"] = normalize_plain_text(publication.get("journal"))
        publication["publisher"] = normalize_plain_text(publication.get("publisher"))
        publication["venue"] = (
            normalize_plain_text(publication.get("venue"))
            or publication["journal"]
            or publication["publisher"]
            or "Unknown"
        )
        publication["abstract"] = normalize_plain_text(publication.get("abstract"))
        publication["bibtex"] = str(publication.get("bibtex", "")).strip()
        publication["volume"] = normalize_plain_text(publication.get("volume"))
        publication["issue"] = normalize_plain_text(publication.get("issue"))
        publication["pages"] = normalize_plain_text(publication.get("pages"))
        publication["url"] = (
            normalize_plain_text(publication.get("url")) or f"https://doi.org/{doi}"
        )
        publication["year"] = normalize_year(publication.get("year"))
        publication["groups"] = overrides.get(
            "groups", ensure_list(publication.get("groups", []))
        )
        publication["codes"] = overrides.get(
            "codes", ensure_list(publication.get("codes", []))
        )
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
        publication["authors_html"] = render_author_list(
            publication["authors"], author_to_slug
        )

    write_text(OUTPUT_FILE, build_page(publications, author_to_slug))
    print(f"Updated {OUTPUT_FILE} with {len(publications)} publications")

    CACHE_FILE.write_text(
        json.dumps(publications, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved metadata cache to {CACHE_FILE}")


if __name__ == "__main__":
    main()
