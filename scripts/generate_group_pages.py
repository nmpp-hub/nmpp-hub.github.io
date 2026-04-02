"""Generate individual group pages with members, publications, and dissertations.

Reads groups.yml and members.yml, then generates individual .md pages for each group
in src/content/groups/<group-slug>.md.

Run as part of generate_website.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import site_generation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import (
    build_author_to_slug_map,
    ensure_list,
    escape_text,
    load_yaml,
    render_author_list,
    slugify,
    write_text,
)

ROOT = Path(__file__).resolve().parent.parent
GROUPS_FILE = ROOT / "data" / "groups.yml"
MEMBERS_FILE = ROOT / "data" / "members.yml"
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
GROUPS_OUTPUT_DIR = ROOT / "src" / "content" / "groups"
GROUPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEGREE_LABELS = {"phd": "PhD", "msc": "MSc"}

CUSTOM_START = "<!-- CUSTOM:CONTENT:START -->"
CUSTOM_END = "<!-- CUSTOM:CONTENT:END -->"
MEMBERS_START = "<!-- AUTO:MEMBERS:START -->"
MEMBERS_END = "<!-- AUTO:MEMBERS:END -->"
PUBLICATIONS_START = "<!-- AUTO:PUBLICATIONS:START -->"
PUBLICATIONS_END = "<!-- AUTO:PUBLICATIONS:END -->"
DISSERTATIONS_START = "<!-- AUTO:DISSERTATIONS:START -->"
DISSERTATIONS_END = "<!-- AUTO:DISSERTATIONS:END -->"


def load_groups() -> list[dict]:
    """Load and validate groups from YAML."""
    raw = load_yaml(GROUPS_FILE).get("groups", [])
    groups = []
    for entry in raw:
        groups.append(
            {
                "name": str(entry.get("name", "")).strip(),
                "leader": str(entry.get("leader", "")).strip(),
                "slug": str(entry.get("slug", "")).strip(),
                "abbr": str(entry.get("abbr", "")).strip(),
                "ipp_url": str(entry.get("ipp_url", "")).strip(),
            }
        )
    return groups


def generate_standard_aliases(name: str) -> list[str]:
    """Generate standard name variations for alias matching."""
    import unicodedata

    # Normalize unicode
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.strip()

    parts = name.split()
    if len(parts) < 2:
        return []

    first_parts = parts[:-1]
    last_part = parts[-1]

    first_name = " ".join(first_parts)
    last_name = last_part

    aliases = set()
    first_initial = first_name[0].lower()

    aliases.add(f"{first_initial}. {last_name.lower()}")
    aliases.add(f"{first_initial} {last_name.lower()}")
    aliases.add(f"{last_name.lower()}, {first_initial}.")
    aliases.add(f"{last_name.lower()}, {first_initial}")

    if "-" in first_name:
        first_name_parts = first_name.split("-")
        for part in first_name_parts:
            if part:
                part_initial = part[0].lower()
                aliases.add(f"{part_initial}. {last_name.lower()}")
                aliases.add(f"{part_initial} {last_name.lower()}")
                aliases.add(f"{last_name.lower()}, {part_initial}.")
                aliases.add(f"{last_name.lower()}, {part_initial}")

    if "-" in last_name:
        last_name_parts = last_name.split("-")
        first_last_part = last_name_parts[0].lower()

        aliases.add(f"{first_initial}. {first_last_part}")
        aliases.add(f"{first_initial} {first_last_part}")
        aliases.add(f"{first_last_part}, {first_initial}.")
        aliases.add(f"{first_last_part}, {first_initial}")

    return sorted(list(aliases))


def load_members() -> list[dict]:
    """Load members from YAML."""
    raw = load_yaml(MEMBERS_FILE).get("members", [])
    members = []
    for entry in raw:
        name = str(entry.get("name", "")).strip()
        members.append(
            {
                "name": name,
                "group": str(entry.get("group", "")).strip(),
                "alumni": bool(entry.get("alumni", False)),
                "aliases": generate_standard_aliases(name),
            }
        )
    return members


def load_publications_cache() -> list[dict]:
    """Load the publications metadata cache."""
    if not CACHE_FILE.exists():
        return []
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


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
            }
        )
    return dissertations


def build_leader_section(group: dict, members: list[dict]) -> str:
    """Build the group leader section with link to member page."""
    leader_name = group["leader"]

    # Try to find matching member by extracting name from leader string
    # (e.g., "Dr. Stefan Possanner" -> find "Stefan Possanner")
    member_slug = None
    for member in members:
        # Check if member name appears in leader string (ignoring titles)
        if member["name"].lower() in leader_name.lower():
            member_slug = slugify(member["name"])
            break

    if member_slug:
        return f'<p><strong><a href="/members/{member_slug}/">{escape_text(leader_name)}</a></strong></p>'
    else:
        return f"<p><strong>{escape_text(leader_name)}</strong></p>"


def build_members_list(members: list[dict]) -> str:
    """Build HTML list of members."""
    if not members:
        return "<p>No members in this group yet.</p>"

    def sort_key(m: dict) -> tuple:
        return (int(m["alumni"]), m["name"].lower())

    items = []
    for member in sorted(members, key=sort_key):
        slug = slugify(member["name"])
        suffix = ", alumni" if member["alumni"] else ""
        items.append(f'  <li><a href="/members/{slug}/">{escape_text(member["name"])}</a>{suffix}</li>')

    body = "\n".join(items)
    return f"<ul>\n{body}\n</ul>"


def build_publications_table(publications: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    """Build HTML table for publications."""
    if not publications:
        return "<p>No publications for this group yet.</p>"

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


def build_dissertations_table(dissertations: list[dict]) -> str:
    """Build HTML table of dissertations."""
    if not dissertations:
        return "<p>No dissertations for this group yet.</p>"

    rows = []
    for diss in dissertations:
        degree = DEGREE_LABELS.get(diss["degree"], diss["degree"])
        rows.append(
            "\n".join(
                [
                    "  <tr>",
                    f"    <td>{diss['year']}</td>",
                    f"    <td>{escape_text(diss['title'])}</td>",
                    f"    <td>{escape_text(diss['author'])}</td>",
                    f"    <td>{escape_text(degree)}</td>",
                    f'    <td><a href="{escape_text(diss["link"])}">Full text</a></td>',
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
      <th>Author</th>
      <th>Degree</th>
      <th>Link</th>
    </tr>
  </thead>
  <tbody>
{body}
  </tbody>
</table>"""


def inject_between_markers(content: str, start_marker: str, end_marker: str, payload: str) -> str:
    """Replace content between markers."""
    import re

    pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
    replacement = f"{start_marker}\n{payload}\n{end_marker}"
    if start_marker in content:
        return re.sub(pattern, replacement, content, flags=re.DOTALL)
    return content


def extract_custom_content(content: str) -> str:
    """Extract content between custom markers."""
    import re
    pattern = re.escape(CUSTOM_START) + r"(.*?)" + re.escape(CUSTOM_END)
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def build_group_page_content(
    group: dict, members: list[dict], publications: list[dict], dissertations: list[dict], existing_content: str = "", author_to_slug: dict[str, str] | None = None
) -> str:
    """Build the complete group page content with markers, preserving custom content."""
    leader_section = build_leader_section(group, members)
    members_section = build_members_list(members)
    pubs_section = build_publications_table(publications, author_to_slug)
    diss_section = build_dissertations_table(dissertations)

    # Preserve existing custom content, or create default with IPP link
    if existing_content:
        custom_content = extract_custom_content(existing_content)
    else:
        # Build default custom content with Links section and IPP link
        abbr = group.get("abbr", "")
        ipp_url = group.get("ipp_url", "")
        if ipp_url:
            link_text = f"{group['name']} ({abbr})" if abbr else group['name']
            custom_content = f"""## Links

- [{link_text}]({escape_text(ipp_url)})"""
        else:
            custom_content = ""

    content = f"""---
title: {escape_text(group['name'])}
---

## Group Leader

{leader_section}

{CUSTOM_START}
{custom_content}
{CUSTOM_END}

## Members

{MEMBERS_START}
{MEMBERS_END}

## Publications

{PUBLICATIONS_START}
{PUBLICATIONS_END}

## Dissertations

{DISSERTATIONS_START}
{DISSERTATIONS_END}
"""

    # Inject content between markers
    content = inject_between_markers(content, MEMBERS_START, MEMBERS_END, members_section)
    content = inject_between_markers(content, PUBLICATIONS_START, PUBLICATIONS_END, pubs_section)
    content = inject_between_markers(content, DISSERTATIONS_START, DISSERTATIONS_END, diss_section)

    return content


def main() -> None:
    """Generate group pages."""
    all_groups = load_groups()
    all_members = load_members()
    all_publications = load_publications_cache()
    all_dissertations = load_dissertations()
    author_to_slug = build_author_to_slug_map()

    print(f"Loaded {len(all_groups)} groups, {len(all_members)} members, {len(all_publications)} publications, {len(all_dissertations)} dissertations")

    # Generate page for each group
    for group in all_groups:
        # Filter members for this group
        group_members = [m for m in all_members if m["group"] == group["name"]]
        group_members.sort(key=lambda m: (int(m["alumni"]), m["name"].lower()))

        # Build set of all member aliases for matching
        member_aliases = set()
        for member in group_members:
            member_aliases.add(member["name"].lower())
            member_aliases.update(member["aliases"])

        # Filter publications by matching authors to group members
        group_pubs = []
        for pub in all_publications:
            authors_lower = pub["authors"].lower()
            for alias in member_aliases:
                if alias.lower() in authors_lower:
                    group_pubs.append(pub)
                    break
        group_pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))

        # Filter dissertations by matching authors to group members
        group_diss = []
        for diss in all_dissertations:
            author_lower = diss["author"].lower()
            for alias in member_aliases:
                if alias.lower() in author_lower:
                    group_diss.append(diss)
                    break
        group_diss.sort(key=lambda d: (-d["year"], d["author"].lower()))

        # Generate page
        output_file = GROUPS_OUTPUT_DIR / f"{group['slug']}.md"

        # Read existing content to preserve custom section
        existing_content = ""
        if output_file.exists():
            existing_content = output_file.read_text(encoding="utf-8")

        page_content = build_group_page_content(group, group_members, group_pubs, group_diss, existing_content, author_to_slug)
        write_text(output_file, page_content)

        print(f"  {group['name']:50} → {group['slug']:30} ({len(group_members)} members, {len(group_pubs)} pubs, {len(group_diss)} diss)")

    print(f"\nGenerated {len(all_groups)} group pages in {GROUPS_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
