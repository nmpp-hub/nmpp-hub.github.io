from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

# Add parent directory to path to import site_generation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import (build_author_to_slug_map, dissertation_slug,
                             ensure_list, escape_text, load_yaml,
                             render_author_name, render_code_links,
                             render_dissertation_title, write_text)

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "dissertations.yml"
MEMBERS_FILE = ROOT / "data" / "members.yml"
GROUPS_FILE = ROOT / "data" / "groups.yml"
OUTPUT_FILE = ROOT / "src" / "pages" / "dissertations.astro"
CACHE_FILE = ROOT / "data" / "dissertations_cache.json"
ABSTRACTS_DIR = ROOT / "src" / "content" / "dissertations"

DEGREE_LABELS = {
    "phd": "PhD",
    "msc": "MSc",
}


def fetch_mediatum_bibtex(url: str) -> str:
    """Fetch BibTeX from a mediatum URL if it matches the expected pattern."""
    import re

    # Extract ID from mediatum URL
    match = re.search(r"mediatum\.ub\.tum\.de/\??(?:id=)?(\d+)", url)
    if not match:
        return ""

    doc_id = match.group(1)
    bibtex_url = f"https://mediatum.ub.tum.de/export/{doc_id}/bibtex"

    try:
        req = urllib.request.Request(
            bibtex_url,
            headers={
                "User-Agent": "nmpp-dissertations-generator/1.0 (mailto:webmaster@nmpp-hub.github.io)",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode("utf-8").strip()
    except Exception:
        return ""


def validate_dissertation(raw: dict, index: int) -> dict:
    year = int(raw.get("year"))
    date = str(raw.get("date", f"{year}-01-01"))
    title = str(raw.get("title", "")).strip()
    author = str(raw.get("author", "")).strip()
    degree = str(raw.get("degree", "")).strip().lower()
    institution = str(raw.get("institution", "")).strip()
    link = str(raw.get("link", "")).strip()
    fulltext = str(raw.get("fulltext", "")).strip()
    groups = ensure_list(raw.get("groups", []))
    codes = ensure_list(raw.get("codes", []))
    bibtex = str(raw.get("bibtex", "") or "").strip()

    if not title:
        raise ValueError(f"Dissertation {index} is missing a title")
    if not author:
        raise ValueError(f"Dissertation {title} is missing an author")
    if degree not in DEGREE_LABELS:
        raise ValueError(f"Dissertation {title} has invalid degree {degree!r}")

    return {
        "year": year,
        "date": date,
        "title": title,
        "author": author,
        "degree": degree,
        "institution": institution,
        "link": link,
        "fulltext": fulltext,
        "groups": groups,
        "codes": codes,
        "bibtex": bibtex,
    }


def render_degree_and_institution(dissertation: dict) -> str:
    degree = DEGREE_LABELS[dissertation["degree"]]
    institution = dissertation["institution"]
    return escape_text(f"{degree} / {institution}" if institution else degree)


def build_page(
    dissertations: list[dict], author_to_slug: dict[str, str] | None = None
) -> str:
    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    # Build table rows
    table_rows = []
    for dissertation in dissertations:
        degree_label = DEGREE_LABELS[dissertation["degree"]]
        codes = render_code_links(dissertation["codes"])

        row = f"""    <tr>
      <td>{dissertation['date']}</td>
      <td>{render_dissertation_title(dissertation)}</td>
      <td>{render_author_name(dissertation['author'], author_to_slug)}</td>
      <td>{degree_label}</td>
      <td>{codes}</td>
    </tr>"""
        table_rows.append(row)

    table_body = "\n".join(table_rows)

    # Build cards
    cards = []
    for dissertation in dissertations:
        degree_label = DEGREE_LABELS[dissertation["degree"]]
        codes = render_code_links(dissertation["codes"])

        card = f"""
        <div class="publication-card">
          <div class="publication-card-header">
            <div class="publication-card-date">{dissertation['date']}</div>
            <div class="publication-card-title">{render_dissertation_title(dissertation)}</div>
            <div class="publication-card-authors">{render_author_name(dissertation['author'], author_to_slug)}</div>
            <div class="publication-card-degree">{degree_label}</div>
            <div class="publication-card-codes">{codes}</div>
          </div>
        </div>
        """
        cards.append(card.strip())

    cards_body = "\n".join(cards)

    return f"""---
import Base from '../layouts/Base.astro';
import PageLayout from '../components/PageLayout.astro';

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
  title="Dissertations"
  breadcrumbs={{[
    {{ label: 'Home', href: '/' }},
    {{ label: 'Dissertations' }},
  ]}}
>
  <div class="page-wrapper">
    <PageLayout leftNav={{leftNav}}>
    <div class="page-header">
      <h1>Dissertations</h1>
      <p>Search and filter dissertations related to NMPP division research at IPP.</p>
    </div>

    <input id="pub-search" type="search" placeholder="Search by title, author, year, degree, institution, group, code, or keyword..." aria-label="Search dissertations" />

    <table id="publications-table" class="publications-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Title</th>
          <th>Author</th>
          <th>Degree</th>
          <th>Codes</th>
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


def build_author_group_map() -> dict[str, dict]:
    """Build a map from lowercased author name to {group, group_slug} for known members."""
    import unicodedata

    members = load_yaml(MEMBERS_FILE).get("members", [])
    groups_raw = load_yaml(GROUPS_FILE).get("groups", [])
    group_slug_map = {
        g["name"]: g["slug"] for g in groups_raw if g.get("name") and g.get("slug")
    }

    result: dict[str, dict] = {}
    for member in members:
        name = str(member.get("name", "")).strip()
        group_name = str(member.get("group", "")).strip()
        if not name or not group_name:
            continue
        group_slug = group_slug_map.get(group_name, "")
        key = (
            unicodedata.normalize("NFD", name)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        result[key] = {"group": group_name, "group_slug": group_slug}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate dissertation pages and cache."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch BibTeX from mediatum for missing or incomplete cache entries",
    )
    args = parser.parse_args()

    raw_dissertations = load_yaml(DATA_FILE).get("dissertations", [])
    if not isinstance(raw_dissertations, list):
        raise ValueError(
            "dissertations.yml must contain a top-level 'dissertations' list"
        )

    # Load existing cache
    cached_dissertations = {}
    if CACHE_FILE.exists():
        try:
            cache_data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            cached_dissertations = {d["slug"]: d for d in cache_data}
        except (json.JSONDecodeError, KeyError):
            pass  # Start with empty cache if corrupted

    dissertations = []
    for index, raw_dissertation in enumerate(raw_dissertations, 1):
        dissertation = validate_dissertation(raw_dissertation, index)

        # Check if we need to fetch BibTeX
        slug = dissertation_slug(dissertation)
        cached = cached_dissertations.get(slug, {})
        was_cached = bool(cached.get("bibtex", "").strip()) or bool(dissertation["bibtex"].strip())

        # Fetch BibTeX if not cached OR if refresh is requested
        if not was_cached or args.refresh:
            if "mediatum.ub.tum.de" in dissertation["link"]:
                bibtex = fetch_mediatum_bibtex(dissertation["link"])
                if bibtex:
                    dissertation["bibtex"] = bibtex
                    print(f"  Fetched BibTeX for: {dissertation['title'][:50]}...")
                elif was_cached:
                    # Keep existing BibTeX if fetch failed but we had cached data
                    dissertation["bibtex"] = cached.get("bibtex", "")
            elif was_cached:
                # Keep existing BibTeX for non-mediatum links
                dissertation["bibtex"] = cached.get("bibtex", "")
            # Otherwise preserve raw YAML bibtex if present
        else:
            # Use cached BibTeX
            dissertation["bibtex"] = cached.get("bibtex", "")

        dissertations.append(dissertation)

    dissertations.sort(key=lambda dissertation: dissertation["date"], reverse=True)

    author_group_map = build_author_group_map()
    author_to_slug = build_author_to_slug_map()

    def enrich(d: dict) -> dict:
        import unicodedata

        key = (
            unicodedata.normalize("NFD", d["author"])
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        member_info = author_group_map.get(key, {})
        author_html = render_author_name(d["author"], author_to_slug)
        return {
            "slug": dissertation_slug(d),
            "author_html": author_html,
            **d,
            **member_info,
        }

    # Write JSON cache for use by the Astro [slug].astro page
    cache = [enrich(d) for d in dissertations]
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Updated {CACHE_FILE}")

    # Create empty abstract markdown files for new dissertations (never overwrite)
    ABSTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    for d in dissertations:
        slug = dissertation_slug(d)
        abstract_file = ABSTRACTS_DIR / f"{slug}.md"
        if not abstract_file.exists():
            abstract_file.write_text("---\n---\n", encoding="utf-8")
            print(f"  Created abstract stub: {abstract_file.name}")

    author_to_slug = build_author_to_slug_map()
    write_text(OUTPUT_FILE, build_page(dissertations, author_to_slug))
    print(f"Updated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
