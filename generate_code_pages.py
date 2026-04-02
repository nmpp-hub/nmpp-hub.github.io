"""Inject per-code publications and dissertations tables into code markdown files.

Reads the publications metadata cache (written by populate_publications.py) and
data/dissertations.yml, filters entries by code slug, and injects HTML tables
between marker comments in each src/content/codes/<slug>.md file.

Run after populate_publications.py so the cache is up to date:
    python populate_publications.py
    python generate_code_pages.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from site_generation import build_author_to_slug_map, ensure_list, escape_text, load_yaml, render_author_list

ROOT = Path(__file__).resolve().parent
CODES_DIR = ROOT / "src" / "content" / "codes"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
MEMBERS_FILE = ROOT / "data" / "members.yml"

MEM_START = "<!-- AUTO:MEMBERS:START -->"
MEM_END = "<!-- AUTO:MEMBERS:END -->"
PUB_START = "<!-- AUTO:PUBLICATIONS:START -->"
PUB_END = "<!-- AUTO:PUBLICATIONS:END -->"
DISS_START = "<!-- AUTO:DISSERTATIONS:START -->"
DISS_END = "<!-- AUTO:DISSERTATIONS:END -->"

DEGREE_LABELS = {"phd": "PhD", "msc": "MSc"}

# Display labels for member roles (used in per-code member lists)
MEMBER_ROLE_LABELS = {
    "professor": "Professor",
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
        label = MEMBER_ROLE_LABELS.get(member["role"], member["role"])
        suffix = ", alumni" if member["alumni"] else ""
        items.append(f"  <li>{escape_text(member['name'])} ({label}{suffix})</li>")

    body = "\n".join(items)
    return f"<ul>\n{body}\n</ul>"


def build_publications_table(publications: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    if not publications:
        return "<p>No publications linked to this code yet.</p>"

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
    if not dissertations:
        return "<p>No dissertations linked to this code yet.</p>"

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


def inject_between_markers(
    content: str, start_marker: str, end_marker: str, payload: str
) -> str:
    pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
    replacement = f"{start_marker}\n{payload}\n{end_marker}"
    if start_marker in content:
        return re.sub(pattern, replacement, content, flags=re.DOTALL)
    return content


def ensure_markers(content: str) -> str:
    """Ensure all auto-generated section markers are present."""
    # All markers already present → nothing to do
    if MEM_START in content and PUB_START in content and DISS_START in content:
        return content

    # Files that already have pub/diss markers but not members markers (migration)
    if PUB_START in content and MEM_START not in content:
        # Update old comment lines
        content = content.replace(
            "<!-- Do not edit the tables below manually. -->",
            "<!-- Do not edit the sections below manually. -->",
            1,
        )
        content = content.replace(
            "<!-- They are auto-generated by generate_code_pages.py from data/dois.yml and data/dissertations.yml. -->",
            "<!-- They are auto-generated by generate_code_pages.py from data/members.yml, data/dois.yml and data/dissertations.yml. -->",
            1,
        )
        # Insert members section immediately before ## Publications
        content = content.replace(
            "\n## Publications\n",
            f"\n## Members\n\n{MEM_START}\n{MEM_END}\n\n## Publications\n",
            1,
        )
        return content

    # Fresh file: append full block
    block = f"""
<!-- Do not edit the sections below manually. -->
<!-- They are auto-generated by generate_code_pages.py from data/members.yml, data/dois.yml and data/dissertations.yml. -->
<!-- To update, edit the YAML files and run: python populate_publications.py && python generate_code_pages.py -->

## Members

{MEM_START}
{MEM_END}

## Publications

{PUB_START}
{PUB_END}

## Dissertations

{DISS_START}
{DISS_END}
"""
    return content.rstrip() + "\n" + block


def main() -> None:
    all_pubs = load_publications_cache()
    all_diss = load_dissertations()
    all_members = load_members()
    author_to_slug = build_author_to_slug_map()

    code_files = sorted(CODES_DIR.glob("*.md"))
    if not code_files:
        print("No code markdown files found.")
        return

    for code_file in code_files:
        slug = code_file.stem
        content = code_file.read_text(encoding="utf-8")

        # Ensure markers exist (also handles migration)
        content = ensure_markers(content)

        # Filter data for this code
        members = [m for m in all_members if slug in m.get("codes", [])]

        pubs = [p for p in all_pubs if slug in p.get("codes", [])]
        pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))

        diss = [d for d in all_diss if slug in d.get("codes", [])]
        diss.sort(key=lambda d: (-d["year"], d["author"].lower()))

        # Inject content
        content = inject_between_markers(
            content, MEM_START, MEM_END, build_members_list(members)
        )
        content = inject_between_markers(
            content, PUB_START, PUB_END, build_publications_table(pubs, author_to_slug)
        )
        content = inject_between_markers(
            content, DISS_START, DISS_END, build_dissertations_table(diss)
        )

        code_file.write_text(content, encoding="utf-8")
        print(f"  {slug}: {len(members)} members, {len(pubs)} publications, {len(diss)} dissertations")

    print(f"Updated {len(code_files)} code pages")


if __name__ == "__main__":
    main()
