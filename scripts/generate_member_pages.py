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
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import site_generation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import build_author_to_slug_map, ensure_list, escape_text, load_yaml, render_author_list, render_code_links, slugify, write_text

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "data" / "members.yml"
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
MEMBERS_OUTPUT_DIR = ROOT / "src" / "content" / "members"
MEMBERS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEGREE_LABELS = {"phd": "PhD", "msc": "MSc"}


def generate_standard_aliases(name: str) -> list[str]:
    """Generate standard name variations for alias matching.

    For "John Smith-Jones", generates:
    - j. smith-jones
    - j smith-jones
    - smith-jones, j.
    - smith-jones, j
    - j. smith
    - j smith
    - smith, j.
    - smith, j
    And similar variations for double last names.
    """
    import unicodedata

    # Normalize unicode
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.strip()

    parts = name.split()
    if len(parts) < 2:
        return []

    # Get first name(s) and last name(s)
    first_parts = parts[:-1]  # Everything except last part
    last_part = parts[-1]      # Last part

    first_name = " ".join(first_parts)
    last_name = last_part

    aliases = set()

    # Generate variations for full first name with last name
    first_initial = first_name[0].lower()

    # Variations: "F. Lastname", "F Lastname", "Lastname, F.", "Lastname, F"
    aliases.add(f"{first_initial}. {last_name.lower()}")
    aliases.add(f"{first_initial} {last_name.lower()}")
    aliases.add(f"{last_name.lower()}, {first_initial}.")
    aliases.add(f"{last_name.lower()}, {first_initial}")

    # Also handle compound first names - use each initial
    if "-" in first_name:
        first_name_parts = first_name.split("-")
        for part in first_name_parts:
            if part:
                part_initial = part[0].lower()
                aliases.add(f"{part_initial}. {last_name.lower()}")
                aliases.add(f"{part_initial} {last_name.lower()}")
                aliases.add(f"{last_name.lower()}, {part_initial}.")
                aliases.add(f"{last_name.lower()}, {part_initial}")

    # Handle compound last names - split and create variations with first part
    if "-" in last_name:
        last_name_parts = last_name.split("-")
        first_last_part = last_name_parts[0].lower()

        # Variations with just first part of compound last name
        aliases.add(f"{first_initial}. {first_last_part}")
        aliases.add(f"{first_initial} {first_last_part}")
        aliases.add(f"{first_last_part}, {first_initial}.")
        aliases.add(f"{first_last_part}, {first_initial}")

    return sorted(list(aliases))


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

        # Get manually-specified aliases
        manual_aliases = ensure_list(entry.get("aliases", []))

        # Generate standard aliases from full name
        auto_aliases = generate_standard_aliases(name)

        # Combine: auto-generated + manually-specified
        combined_aliases = list(set(auto_aliases + manual_aliases))

        member = {
            "name": name,
            "role": str(entry.get("role", "")).strip().lower(),
            "topic": str(entry.get("topic", "")).strip(),
            "contact": str(entry.get("contact", "")).strip(),
            "group": str(entry.get("group", "")).strip(),
            "codes": ensure_list(entry.get("codes", [])),
            "aliases": combined_aliases,
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
    """Build the profile section with picture on left (circular), info on right."""
    # Profile picture (left side) - circular frame
    if member["picture"]:
        photo = f'<img src="{escape_text(member["picture"])}" alt="{escape_text(member["name"])}" class="member-profile-photo-circle" />'
    else:
        photo = '<div class="member-profile-photo-circle member-photo-placeholder"></div>'

    # Info section (right side)
    info_lines = []

    # Group
    if member.get("group"):
        info_lines.append(f"<p><strong>Group:</strong> {escape_text(member['group'])}</p>")

    # Topic
    if member["topic"]:
        info_lines.append(f"<p><strong>Topic:</strong> {escape_text(member['topic'])}</p>")

    # Description (if exists)
    if member["description"]:
        info_lines.append(f"<p>{escape_text(member['description'])}</p>")

    # Codes
    if member["codes"]:
        codes_html = render_code_links(member["codes"])
        info_lines.append(f"<p><strong>Codes:</strong> {codes_html}</p>")

    info = "\n".join(info_lines) if info_lines else "<p>No additional information available.</p>"

    # Return HTML with two-column layout: photo on left, info on right
    return f"""<div class="member-profile-flex">
<div class="member-profile-photo-wrapper">
{photo}
</div>
<div class="member-profile-text">
{info}
</div>
</div>"""


def build_publications_table(publications: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    """Build HTML table for publications."""
    if not publications:
        return "<p>No publications yet.</p>"

    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    rows = []
    for pub in publications:
        rows.append(
            "\n".join(
                [
                    "  <tr>",
                    f"    <td>{pub['year'] or ''}</td>",
                    f"    <td>{escape_text(pub['title'])}</td>",
                    f"    <td>{render_author_list(pub['authors'], author_to_slug)}</td>",
                    f"    <td>{escape_text(pub['venue'])}</td>",
                    f'    <td><a href="https://doi.org/{escape_text(pub["doi"])}">DOI</a></td>',
                    "  </tr>",
                ]
            )
        )

    body = "\n".join(rows)
    return f"""<table>
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
        return "<p>No dissertations yet.</p>"

    lines = []
    for diss in dissertations:
        degree = DEGREE_LABELS.get(diss["degree"], diss["degree"])
        lines.append(
            f"- {escape_text(diss['title'])} ({degree}, {diss['year']}) - "
            f"[Full text]({escape_text(diss['link'])})"
        )

    return "\n".join(lines)


PROFILE_START = "<!-- AUTO:PROFILE:START -->"
PROFILE_END = "<!-- AUTO:PROFILE:END -->"
PUBLICATIONS_START = "<!-- AUTO:PUBLICATIONS:START -->"
PUBLICATIONS_END = "<!-- AUTO:PUBLICATIONS:END -->"
DISSERTATIONS_START = "<!-- AUTO:DISSERTATIONS:START -->"
DISSERTATIONS_END = "<!-- AUTO:DISSERTATIONS:END -->"


def inject_between_markers(
    content: str, start_marker: str, end_marker: str, payload: str
) -> str:
    """Replace content between markers, or add markers if not present."""
    pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
    replacement = f"{start_marker}\n{payload}\n{end_marker}"
    if start_marker in content:
        return re.sub(pattern, replacement, content, flags=re.DOTALL)
    return content


def ensure_member_markers(content: str, member_name: str) -> str:
    """Ensure all auto-generated section markers are present."""
    if PROFILE_START in content and PUBLICATIONS_START in content and DISSERTATIONS_START in content:
        return content

    # Create template if markers are missing
    block = f"""---
title: {escape_text(member_name)}
---

## Profile

{PROFILE_START}
{PROFILE_END}

## Publications

{PUBLICATIONS_START}
{PUBLICATIONS_END}

## Dissertations

{DISSERTATIONS_START}
{DISSERTATIONS_END}
"""
    return content if content.strip() else block


def build_member_page_content(member: dict, publications: list[dict], dissertations: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    """Build the complete member page content with markers."""
    profile_section = build_profile_section(member)
    pubs_section = build_publications_table(publications, author_to_slug)
    diss_section = build_dissertations_list(dissertations)

    # Start with template
    content = f"""---
title: {escape_text(member['name'])}
---

## Profile

{PROFILE_START}
{PROFILE_END}

## Publications

{PUBLICATIONS_START}
{PUBLICATIONS_END}

## Dissertations

{DISSERTATIONS_START}
{DISSERTATIONS_END}
"""

    # Inject content between markers
    content = inject_between_markers(content, PROFILE_START, PROFILE_END, profile_section)
    content = inject_between_markers(content, PUBLICATIONS_START, PUBLICATIONS_END, pubs_section)
    content = inject_between_markers(content, DISSERTATIONS_START, DISSERTATIONS_END, diss_section)

    return content


def main() -> None:
    """Generate member pages."""
    # Load data
    all_members = load_members()
    all_publications = load_publications_cache()
    all_dissertations = load_dissertations()
    author_to_slug = build_author_to_slug_map()

    print(f"Loaded {len(all_members)} members, {len(all_publications)} publications, {len(all_dissertations)} dissertations")

    # Build set of valid member slugs from YAML
    valid_slugs = {slugify(member["name"]) for member in all_members}

    # Generate page for each member
    for member in all_members:
        slug = slugify(member["name"])

        # Filter publications and dissertations for this member
        member_pubs = [p for p in all_publications if member_matches_publication(member, p)]
        member_pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))

        member_diss = [d for d in all_dissertations if member_matches_dissertation(member, d)]
        member_diss.sort(key=lambda d: (-d["year"], d["author"].lower()))

        # Generate page
        output_file = MEMBERS_OUTPUT_DIR / f"{slug}.md"

        # Read existing file if it exists, otherwise create new one
        if output_file.exists():
            existing_content = output_file.read_text(encoding="utf-8")
            content = ensure_member_markers(existing_content, member["name"])
        else:
            content = f"---\ntitle: {escape_text(member['name'])}\n---\n"

        # Inject generated content between markers
        page_content = build_member_page_content(member, member_pubs, member_diss, author_to_slug)
        write_text(output_file, page_content)

        print(f"  {member['name']:30} → {slug:30} ({len(member_pubs)} pubs, {len(member_diss)} diss)")

    print(f"\nGenerated {len(all_members)} member pages in {MEMBERS_OUTPUT_DIR}")

    # Check for orphaned member page files (no corresponding YAML entry)
    if MEMBERS_OUTPUT_DIR.exists():
        existing_files = list(MEMBERS_OUTPUT_DIR.glob("*.md"))
        orphaned = []
        for file_path in existing_files:
            slug = file_path.stem
            if slug not in valid_slugs:
                orphaned.append(file_path)

        if orphaned:
            print("\n⚠️  WARNING: Found member page files with no corresponding entry in members.yml:")
            for file_path in sorted(orphaned):
                print(f"  - {file_path.name}")
            print(f"\nThese files should be removed or added to members.yml")
        else:
            print("\n✓ All member page files have corresponding entries in members.yml")


if __name__ == "__main__":
    main()
