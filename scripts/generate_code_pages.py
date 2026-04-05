"""Generate per-code auto partials and create missing code markdown files.

Reads the publications metadata cache (written by populate_publications.py) and
data/dissertations.yml, filters entries by code slug, writes HTML partials under
src/content/codes/_auto/, and creates src/content/codes/<slug>.md only if missing.

Run after populate_publications.py so the cache is up to date:
    python populate_publications.py
    python generate_code_pages.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path to import site_generation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import build_author_to_slug_map, ensure_list, escape_text, load_yaml, render_author_list, render_dissertation_title, render_publication_title, slugify

ROOT = Path(__file__).resolve().parent.parent
CODES_DIR = ROOT / "src" / "content" / "codes"
CODES_AUTO_DIR = CODES_DIR / "_auto"
CODES_AUTO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
MEMBERS_FILE = ROOT / "data" / "members.yml"

DEGREE_LABELS = {"phd": "PhD", "msc": "MSc"}

# Display labels for member roles (used in per-code member lists)
MEMBER_ROLE_LABELS = {
    "professor": "Professor",
    "group leader": "Group leader",
    "permanent staff": "Permanent staff",
    "postdoc": "Postdoc",
    "phd": "PhD student",
    "msc": "MSc student",
    "admin staff": "Admin staff",
}
MEMBER_ROLE_PRIORITY = {
    role: i for i, role in enumerate(MEMBER_ROLE_LABELS)
}


def load_publications_cache() -> list[dict]:
    if not CACHE_FILE.exists():
        print(f"Warning: {CACHE_FILE} not found. Run populate_publications.py first.")
        return []
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def load_members() -> list[dict]:
    raw = load_yaml(MEMBERS_FILE).get("members", [])
    members = []
    for entry in raw:
        members.append(
            {
                "name": str(entry.get("name", "")).strip(),
                "role": str(entry.get("role", "")).strip().lower(),
                "alumni": bool(entry.get("alumni", False)),
                "codes": ensure_list(entry.get("codes", [])),
            }
        )
    return members


def load_dissertations() -> list[dict]:
    raw = load_yaml(DISSERTATIONS_FILE).get("dissertations", [])
    dissertations = []
    for entry in raw:
        dissertations.append(
            {
                "year": int(entry.get("year", 0)),
                "title": str(entry.get("title", "")).strip(),
                "author": str(entry.get("author", "")).strip(),
                "degree": str(entry.get("degree", "")).strip().lower(),
                "link": str(entry.get("link", "")).strip(),
                "codes": ensure_list(entry.get("codes", [])),
            }
        )
    return dissertations


def build_members_list(members: list[dict]) -> str:
    if not members:
        return "<p>No members linked to this code yet.</p>"

    def sort_key(m: dict) -> tuple:
        priority = MEMBER_ROLE_PRIORITY.get(m["role"], 99)
        return (int(m["alumni"]), priority, m["name"].lower())

    items = []
    for member in sorted(members, key=sort_key):
        member_slug = slugify(member["name"])
        label = MEMBER_ROLE_LABELS.get(member["role"], member["role"])
        suffix = ", alumni" if member["alumni"] else ""
        items.append(
            f'  <li><a href="/members/{member_slug}/">{escape_text(member["name"])}</a> ({label}{suffix})</li>'
        )

    body = "\n".join(items)
    return f"<ul>\n{body}\n</ul>"


def build_publications_section(publications: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    if not publications:
        return "<p>No publications linked to this code yet.</p>"

    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    table_rows = []
    cards = []
    for pub in publications:
        venue = escape_text(pub['venue'])
        doi_link = f"<a href=\"https://doi.org/{escape_text(pub['doi'])}\">DOI</a>"
        details = f"{venue} · {doi_link}"

        table_rows.append(f"""    <tr>
      <td>{pub['year'] or ''}</td>
      <td>{render_publication_title(pub)}</td>
      <td>{render_author_list(pub['authors'], author_to_slug)}</td>
      <td>{details}</td>
    </tr>""")

        card = f"""
        <div class="publication-card">
          <div class="publication-card-header">
            <div class="publication-card-year">{pub['year'] or ''}</div>
            <div class="publication-card-title">{render_publication_title(pub)}</div>
            <div class="publication-card-authors">{render_author_list(pub['authors'], author_to_slug)}</div>
            <div class="publication-card-details">
              {details}
            </div>
          </div>
        </div>
        """
        cards.append(card.strip())

    table_body = "\n".join(table_rows)
    cards_body = "\n".join(cards)

    return f"""<table id="publications-table" class="publications-table">
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
    </div>"""


def build_dissertations_section(dissertations: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    if not dissertations:
        return "<p>No dissertations linked to this code yet.</p>"

    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    table_rows = []
    cards = []
    for diss in dissertations:
        degree = DEGREE_LABELS.get(diss["degree"], diss["degree"])
        link = f"<a href=\"{escape_text(diss['link'])}\">Full text</a>"
        details = f"{degree} · {link}"

        table_rows.append(f"""    <tr>
      <td>{diss['year']}</td>
      <td>{render_dissertation_title(diss)}</td>
      <td>{render_author_list(diss['author'], author_to_slug)}</td>
      <td>{details}</td>
    </tr>""")

        card = f"""
        <div class="publication-card">
          <div class="publication-card-header">
            <div class="publication-card-year">{diss['year']}</div>
            <div class="publication-card-title">{render_dissertation_title(diss)}</div>
            <div class="publication-card-authors">{render_author_list(diss['author'], author_to_slug)}</div>
            <div class="publication-card-details">
              {details}
            </div>
          </div>
        </div>
        """
        cards.append(card.strip())

    table_body = "\n".join(table_rows)
    cards_body = "\n".join(cards)

    return f"""<table id="publications-table" class="publications-table">
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
    </div>"""


def build_new_code_page(slug: str) -> str:
    """Build initial markdown content for a new code page."""
    title = slug.replace("-", " ").upper()
    return f"""---
title: {escape_text(title)}
path: /codes/{slug}/
---

Add custom content here.
"""


def main() -> None:
    all_pubs = load_publications_cache()
    all_diss = load_dissertations()
    all_members = load_members()
    author_to_slug = build_author_to_slug_map()

    known_slugs = {path.stem for path in CODES_DIR.glob("*.md")}
    for member in all_members:
        known_slugs.update(ensure_list(member.get("codes", [])))
    for pub in all_pubs:
        known_slugs.update(ensure_list(pub.get("codes", [])))
    for dissertation in all_diss:
        known_slugs.update(ensure_list(dissertation.get("codes", [])))

    if not known_slugs:
        print("No code slugs found.")
        return

    for slug in sorted(known_slugs):
        code_file = CODES_DIR / f"{slug}.md"
        if not code_file.exists():
            code_file.write_text(build_new_code_page(slug), encoding="utf-8")

        # Filter data for this code
        members = [m for m in all_members if slug in m.get("codes", [])]

        pubs = [p for p in all_pubs if slug in p.get("codes", [])]
        pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))

        diss = [d for d in all_diss if slug in d.get("codes", [])]
        diss.sort(key=lambda d: (-d["year"], d["author"].lower()))

        # Write auto sections to separate files
        (CODES_AUTO_DIR / f"{slug}.members.html").write_text(
            build_members_list(members) + "\n", encoding="utf-8"
        )
        (CODES_AUTO_DIR / f"{slug}.publications.html").write_text(
            build_publications_section(pubs, author_to_slug) + "\n", encoding="utf-8"
        )
        (CODES_AUTO_DIR / f"{slug}.dissertations.html").write_text(
            build_dissertations_section(diss, author_to_slug) + "\n", encoding="utf-8"
        )

        print(f"  {slug}: {len(members)} members, {len(pubs)} publications, {len(diss)} dissertations")

    print(f"Updated {len(known_slugs)} code entries")


if __name__ == "__main__":
    main()
