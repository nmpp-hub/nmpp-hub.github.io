"""Generate individual member pages with their dissertations, publications, code, profile.

Reads members.yml, dissertations.yml, and the publications cache, then generates
individual .astro pages for each member in src/content/members/<member-slug>.astro.
Member pages include:
  - Profile picture (if available)
  - Topic/description
  - Code they work on
  - Publications (table format)
  - Dissertations (list format)

Run after populate_publications.py so the cache is up to date:
    python populate_publications.py
    python generate_member_pages.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from site_generation import build_author_to_slug_map, ensure_list, escape_text, load_yaml, render_author_list, render_code_links, write_text

ROOT = Path(__file__).resolve().parent
MEMBERS_FILE = ROOT / "data" / "members.yml"
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
MEMBERS_OUTPUT_DIR = ROOT / "src" / "content" / "members"

DEGREE_LABELS = {"phd": "PhD", "msc": "MSc"}


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def load_publications_cache() -> list[dict]:
    """Load the publications metadata cache."""
    if not CACHE_FILE.exists():
        print(f"Warning: {CACHE_FILE} not found. Run populate_publications.py first.")
        return []
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def load_members() -> list[dict]:
    """Load and validate members from YAML."""
    raw = load_yaml(MEMBERS_FILE).get("members", [])
    members = []
    for index, entry in enumerate(raw, start=1):
        name = str(entry.get("name", "")).strip()
        if not name:
            raise ValueError(f"Member {index} is missing a name")

        member = {
            "name": name,
            "role": str(entry.get("role", "")).strip().lower(),
            "topic": str(entry.get("topic", "")).strip(),
            "contact": str(entry.get("contact", "")).strip(),
            "group": str(entry.get("group", "")).strip(),
            "codes": ensure_list(entry.get("codes", [])),
            "aliases": ensure_list(entry.get("aliases", [])),
            "alumni": bool(entry.get("alumni", False)),
            "picture": str(entry.get("picture", "") or "").strip(),
            "description": str(entry.get("description", "")).strip(),
        }
        members.append(member)
    return members


def load_dissertations() -> list[dict]:
    """Load and validate dissertations from YAML."""
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


def member_matches_dissertation(member: dict, dissertation: dict) -> bool:
    """Check if a member's aliases match a dissertation author."""
    if not member["aliases"]:
        return False

    author_lower = dissertation["author"].lower()
    for alias in member["aliases"]:
        if alias.lower() in author_lower or author_lower in alias.lower():
            return True
    return False


def member_matches_publication(member: dict, publication: dict) -> bool:
    """Check if a member's aliases match publication authors or codes."""
    # Check if publication is linked to member's codes
    for code in member["codes"]:
        if code in publication.get("codes", []):
            return True

    # Check if member's aliases match author names
    if not member["aliases"]:
        return False

    authors_lower = publication.get("authors", "").lower()
    for alias in member["aliases"]:
        if alias.lower() in authors_lower or authors_lower in alias.lower():
            return True
    return False


def build_profile_section(member: dict) -> str:
    """Build the profile section with picture, topic, and codes."""
    lines = []

    # Profile picture
    if member["picture"]:
        lines.append(f'      <img src="{escape_text(member["picture"])}" alt="{escape_text(member["name"])}" class="member-profile-picture" />')

    # Topic
    if member["topic"]:
        lines.append(f"      <p><strong>Topic:</strong> {escape_text(member['topic'])}</p>")

    # Description (if exists)
    if member["description"]:
        lines.append(f"      <p>{escape_text(member['description'])}</p>")

    # Codes
    if member["codes"]:
        codes_html = render_code_links(member["codes"])
        lines.append(f"      <p><strong>Codes:</strong> {codes_html}</p>")

    return "\n".join(lines)


def build_publications_table(publications: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    """Build HTML table for publications."""
    if not publications:
        return "      <p>No publications yet.</p>"

    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    rows = []
    for pub in publications:
        rows.append(
            "\n".join(
                [
                    "        <tr>",
                    f"          <td>{pub['year'] or ''}</td>",
                    f"          <td>{escape_text(pub['title'])}</td>",
                    f"          <td>{render_author_list(pub['authors'], author_to_slug)}</td>",
                    f"          <td>{escape_text(pub['venue'])}</td>",
                    f'          <td><a href="https://doi.org/{escape_text(pub["doi"])}">DOI</a></td>',
                    "        </tr>",
                ]
            )
        )

    body = "\n".join(rows)
    return f"""      <table>
        <thead>
          <tr>
            <th>Year</th>
            <th>Title</th>
            <th>Authors</th>
            <th>Venue</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
{body}
        </tbody>
      </table>"""


def build_dissertations_list(dissertations: list[dict]) -> str:
    """Build list of dissertations."""
    if not dissertations:
        return "      <p>No dissertations yet.</p>"

    lines = []
    for diss in dissertations:
        degree = DEGREE_LABELS.get(diss["degree"], diss["degree"])
        lines.append(
            f"      <li>{escape_text(diss['title'])} ({degree}, {diss['year']}) - "
            f'<a href="{escape_text(diss["link"])}">Full text</a></li>'
        )

    body = "\n".join(lines)
    return f"""      <ul>
{body}
      </ul>"""


def build_member_page(member: dict, publications: list[dict], dissertations: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    """Build the complete member page."""
    profile_section = build_profile_section(member)
    pubs_section = build_publications_table(publications, author_to_slug)
    diss_section = build_dissertations_list(dissertations)

    return f"""---
import Base from '../../layouts/Base.astro';
---

<Base title="{escape_text(member['name'])}">
  <div class="page-wrapper">
    <div class="page-header">
      <h1>{escape_text(member['name'])}</h1>
      <p>{escape_text(member['topic'] or member['group'])}</p>
    </div>

    <div class="prose">
      <h2>Profile</h2>
{profile_section}

      <h2>Publications</h2>
{pubs_section}

      <h2>Dissertations</h2>
{diss_section}
    </div>
  </div>
</Base>
"""


def main() -> None:
    """Generate member pages."""
    # Create output directory
    MEMBERS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    all_members = load_members()
    all_publications = load_publications_cache()
    all_dissertations = load_dissertations()
    author_to_slug = build_author_to_slug_map()

    print(f"Loaded {len(all_members)} members, {len(all_publications)} publications, {len(all_dissertations)} dissertations")

    # Generate page for each member
    for member in all_members:
        slug = slugify(member["name"])

        # Filter publications and dissertations for this member
        member_pubs = [p for p in all_publications if member_matches_publication(member, p)]
        member_pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))

        member_diss = [d for d in all_dissertations if member_matches_dissertation(member, d)]
        member_diss.sort(key=lambda d: (-d["year"], d["author"].lower()))

        # Generate page
        page_content = build_member_page(member, member_pubs, member_diss, author_to_slug)
        output_file = MEMBERS_OUTPUT_DIR / f"{slug}.astro"
        write_text(output_file, page_content)

        print(f"  {member['name']:30} → {slug:30} ({len(member_pubs)} pubs, {len(member_diss)} diss)")

    print(f"\nGenerated {len(all_members)} member pages in {MEMBERS_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
