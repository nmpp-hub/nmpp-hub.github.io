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

from site_generation import (build_author_to_slug_map, ensure_list,
                              escape_text, load_yaml, remove_stale_auto_partials,
                              remove_stale_pages, render_listing_author_list,
                              render_code_links, render_dissertation_title,
                              render_publication_title, slugify, write_text)

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "data" / "members.yml"
GROUPS_FILE = ROOT / "data" / "groups.yml"
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
CACHE_FILE = ROOT / "data" / ".publications_cache.json"
MEMBERS_OUTPUT_DIR = ROOT / "src" / "content" / "members"
MEMBERS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MEMBERS_AUTO_DIR = MEMBERS_OUTPUT_DIR / "_auto"
MEMBERS_AUTO_DIR.mkdir(parents=True, exist_ok=True)

DEGREE_LABELS = {"phd": "PhD", "msc": "MSc"}


def generate_standard_aliases(name: str) -> list[str]:
    """Generate standard name variations for alias matching.

    For "John Smith-Jones", generates:
    - john smith-jones (full name)
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
    name_normalized = unicodedata.normalize("NFD", name)
    name_normalized = name_normalized.encode("ascii", "ignore").decode("ascii")
    name_normalized = name_normalized.strip()

    parts = name_normalized.split()
    if len(parts) < 2:
        return []

    # Get first name(s) and last name(s)
    first_parts = parts[:-1]  # Everything except last part
    last_part = parts[-1]  # Last part

    first_name = " ".join(first_parts)
    last_name = last_part

    aliases = set()

    # Always include the full normalized name
    aliases.add(name_normalized.lower())

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
            # Social/academic profile links
            "github": str(entry.get("github", "")).strip(),
            "gitlab": str(entry.get("gitlab", "")).strip(),
            "gitlab_mpcdf": str(entry.get("gitlab_mpcdf", "")).strip(),
            "google_scholar": str(entry.get("google_scholar", "")).strip(),
            "orcid": str(entry.get("orcid", "")).strip(),
            "linkedin": str(entry.get("linkedin", "")).strip(),
            "website": str(entry.get("website", "")).strip(),
            "researchgate": str(entry.get("researchgate", "")).strip(),
            "twitter": str(entry.get("twitter", "")).strip(),
            "x": str(entry.get("x", "")).strip(),
            "bluesky": str(entry.get("bluesky", "")).strip(),
            "mastodon": str(entry.get("mastodon", "")).strip(),
            "academia_edu": str(entry.get("academia_edu", "")).strip(),
            "semanticscholar": str(entry.get("semanticscholar", "")).strip(),
            "dblp": str(entry.get("dblp", "")).strip(),
        }
        members.append(member)
    return members


def load_group_slug_map() -> dict[str, str]:
    """Load mapping from group display name to group slug."""
    raw = load_yaml(GROUPS_FILE).get("groups", [])
    mapping: dict[str, str] = {}
    for entry in raw:
        name = str(entry.get("name", "")).strip()
        slug = str(entry.get("slug", "")).strip()
        if name and slug:
            mapping[name] = slug
    return mapping


def load_dissertations() -> list[dict]:
    """Load and validate dissertations from YAML."""
    raw = load_yaml(DISSERTATIONS_FILE).get("dissertations", [])
    dissertations = []
    for entry in raw:
        dissertations.append(
            {
                "year": int(entry.get("year", 0)),
                "date": str(entry.get("date", f"{entry.get('year', 0)}-01-01")),
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


def member_matches_publication(
    member: dict, publication: dict, author_to_slug: dict[str, str]
) -> bool:
    """Check if a member is explicitly in the publication author list.

    This avoids false positives from code overlap (e.g., member works on a code
    but is not an author of every paper tagged with that code).
    """
    import unicodedata

    member_slug = slugify(member["name"])
    authors_raw = publication.get("authors", "")
    if not authors_raw:
        return False

    for author in [a.strip() for a in authors_raw.split(",") if a.strip()]:
        author_key = author.lower()
        author_slug = author_to_slug.get(author_key)
        if author_slug is None:
            normalized = (
                unicodedata.normalize("NFD", author)
                .encode("ascii", "ignore")
                .decode("ascii")
                .lower()
                .strip()
            )
            author_slug = author_to_slug.get(normalized)
        if author_slug == member_slug:
            return True

    return False


def build_social_links(member: dict) -> str:
    """Build social/academic profile links as icons."""
    social_platforms = {
        "github": {
            "icon": "fab fa-github",
            "url_template": "https://github.com/{username}",
        },
        "gitlab": {
            "icon": "fab fa-gitlab",
            "url_template": "https://gitlab.com/{username}",
        },
        "gitlab_mpcdf": {
            "icon": "fab fa-gitlab",
            "url_template": "https://gitlab.mpcdf.mpg.de/{username}",
        },
        "google_scholar": {
            "icon": "fas fa-graduation-cap",
            "url_template": "https://scholar.google.com/citations?user={user_id}",
        },
        "orcid": {
            "icon": "fab fa-orcid",
            "url_template": "https://orcid.org/{orcid_id}",
        },
        "linkedin": {
            "icon": "fab fa-linkedin",
            "url_template": "https://linkedin.com/in/{username}",
        },
        "website": {"icon": "fas fa-globe", "url_template": "{url}"},
        "researchgate": {
            "icon": "fab fa-researchgate",
            "url_template": "https://researchgate.net/profile/{username}",
        },
        "twitter": {
            "icon": "fab fa-twitter",
            "url_template": "https://twitter.com/{username}",
        },
        "x": {"icon": "fab fa-x-twitter", "url_template": "https://x.com/{username}"},
        "bluesky": {
            "icon": "fas fa-cloud",
            "url_template": "https://bsky.app/profile/{handle}",
        },
        "mastodon": {"icon": "fab fa-mastodon", "url_template": "{url}"},
        "academia_edu": {
            "icon": "fas fa-university",
            "url_template": "https://independent.academia.edu/{username}",
        },
        "semanticscholar": {
            "icon": "fas fa-book",
            "url_template": "https://semanticscholar.org/author/{author_id}",
        },
        "dblp": {
            "icon": "fas fa-database",
            "url_template": "https://dblp.org/pid/{pid}",
        },
    }

    links = []
    for platform, config in social_platforms.items():
        if platform in member and member[platform]:
            value = member[platform]
            if platform == "website" or platform == "mastodon":
                url = config["url_template"].format(url=value)
            elif platform == "google_scholar":
                url = config["url_template"].format(user_id=value)
            elif platform == "orcid":
                url = config["url_template"].format(orcid_id=value)
            elif platform == "semanticscholar":
                url = config["url_template"].format(author_id=value)
            elif platform == "dblp":
                url = config["url_template"].format(pid=value)
            else:
                url = config["url_template"].format(username=value)

            links.append(
                f'<a href="{escape_text(url)}" target="_blank" rel="noopener noreferrer" class="social-link" title="{platform.replace("_", " ").title()}"><i class="{config["icon"]}"></i></a>'
            )

    if links:
        return f'<div class="social-links">{"".join(links)}</div>'
    return ""


def build_profile_section(member: dict, group_slug_map: dict[str, str]) -> str:
    """Build the profile section with picture on left (circular), info on right."""
    # Profile picture (left side) - circular frame
    if member["picture"]:
        photo = f'<img src="{escape_text(member["picture"])}" alt="{escape_text(member["name"])}" class="member-profile-photo-circle" />'
    else:
        photo = (
            '<div class="member-profile-photo-circle member-photo-placeholder"></div>'
        )

    # Info section (right side)
    info_lines = []

    # Group
    if member.get("group"):
        group_name = member["group"]
        group_slug = group_slug_map.get(group_name)
        if group_slug:
            info_lines.append(
                f'<p><strong>Group:</strong> <a href="/groups/{group_slug}/">{escape_text(group_name)}</a></p>'
            )
        else:
            info_lines.append(
                f"<p><strong>Group:</strong> {escape_text(group_name)}</p>"
            )

    # Topic
    if member["topic"]:
        info_lines.append(
            f"<p><strong>Topic:</strong> {escape_text(member['topic'])}</p>"
        )

    # Description (if exists)
    if member["description"]:
        info_lines.append(f"<p>{escape_text(member['description'])}</p>")

    # Codes
    if member["codes"]:
        codes_html = render_code_links(member["codes"])
        info_lines.append(f"<p><strong>Codes:</strong> {codes_html}</p>")

    info = (
        "\n".join(info_lines)
        if info_lines
        else "<p>No additional information available.</p>"
    )

    # Social links section
    social_links = build_social_links(member)

    # Return HTML with two-column layout: photo on left, info on right
    return f"""<div class="member-profile-flex">
<div class="member-profile-photo-wrapper">
{photo}
{social_links}
</div>
<div class="member-profile-text">
{info}
</div>
</div>"""


def build_publications_section(
    publications: list[dict], author_to_slug: dict[str, str] | None = None
) -> str:
    """Build HTML table + cards for publications."""
    if not publications:
        return "<p>No publications yet.</p>"

    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    table_rows = []
    cards = []
    for pub in publications:
        venue = escape_text(pub["venue"])
        doi_link = f"<a href=\"https://doi.org/{escape_text(pub['doi'])}\">DOI</a>"
        details = f"{venue} · {doi_link}"

        table_rows.append(f"""    <tr>
      <td>{pub['year'] or ''}</td>
      <td>{render_publication_title(pub)}</td>
      <td>{render_listing_author_list(pub['authors'], author_to_slug)}</td>
      <td>{details}</td>
    </tr>""")

        card = f"""
        <div class="publication-card">
          <div class="publication-card-header">
            <div class="publication-card-year">{pub['year'] or ''}</div>
            <div class="publication-card-title">{render_publication_title(pub)}</div>
            <div class="publication-card-authors">{render_listing_author_list(pub['authors'], author_to_slug)}</div>
            <div class="publication-card-details">
              {details}
            </div>
          </div>
        </div>
        """
        cards.append(card.strip())

    table_body = "\n".join(table_rows)
    cards_body = "\n".join(cards)

    return f"""<div class="searchable-section">
    <input type="search" class="section-search-input" placeholder="Search publications..." aria-label="Search publications" />
    <table class="publications-table">
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
    <div class="publication-cards">
{cards_body}
    </div>
    </div>"""


def build_dissertations_section(dissertations: list[dict]) -> str:
    """Build HTML table + cards for dissertations."""
    if not dissertations:
        return "<p>No dissertations yet.</p>"

    table_rows = []
    cards = []
    for diss in dissertations:
        degree = DEGREE_LABELS.get(diss["degree"], diss["degree"])
        codes_links = ", ".join(
            [f'<a href="/codes/{code}/">{code}</a>' for code in diss["codes"]]
        )

        table_rows.append(f"""    <tr>
      <td>{diss['date']}</td>
      <td>{render_dissertation_title(diss)}</td>
      <td>{escape_text(diss['author'])}</td>
      <td>{degree}</td>
      <td>{codes_links}</td>
    </tr>""")

        card = f"""
        <div class="publication-card">
          <div class="publication-card-header">
            <div class="publication-card-date">{diss['date']}</div>
            <div class="publication-card-title">{render_dissertation_title(diss)}</div>
            <div class="publication-card-authors">{escape_text(diss['author'])}</div>
            <div class="publication-card-degree">{degree}</div>
            <div class="publication-card-codes">{codes_links}</div>
          </div>
        </div>
        """
        cards.append(card.strip())

    table_body = "\n".join(table_rows)
    cards_body = "\n".join(cards)

    return f"""<div class="searchable-section">
    <input type="search" class="section-search-input" placeholder="Search dissertations..." aria-label="Search dissertations" />
    <table class="publications-table">
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
    <div class="publication-cards">
{cards_body}
    </div>
    </div>"""


def build_new_member_page(member: dict) -> str:
    """Build the initial member page .md content for a new member."""
    return f"""---
title: {escape_text(member['name'])}
---

## About

Add custom content here (research interests, bio, etc.)
"""


def main() -> None:
    """Generate member pages."""
    # Load data
    all_members = load_members()
    group_slug_map = load_group_slug_map()
    all_publications = load_publications_cache()
    all_dissertations = load_dissertations()
    author_to_slug = build_author_to_slug_map()

    print(
        f"Loaded {len(all_members)} members, {len(all_publications)} publications, {len(all_dissertations)} dissertations"
    )

    # Build set of valid member slugs from YAML
    valid_slugs = {slugify(member["name"]) for member in all_members}

    # Generate page for each member
    for member in all_members:
        slug = slugify(member["name"])

        # Filter publications and dissertations for this member
        member_pubs = [
            p
            for p in all_publications
            if member_matches_publication(member, p, author_to_slug)
        ]
        member_pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))

        member_diss = [
            d for d in all_dissertations if member_matches_dissertation(member, d)
        ]
        member_diss.sort(key=lambda d: d["date"], reverse=True)

        # Generate page
        output_file = MEMBERS_OUTPUT_DIR / f"{slug}.md"

        # Only create the .md file if it doesn't exist yet; never overwrite existing files
        if not output_file.exists():
            write_text(output_file, build_new_member_page(member))

        # Write auto sections to separate files
        (MEMBERS_AUTO_DIR / f"{slug}.profile.html").write_text(
            build_profile_section(member, group_slug_map) + "\n", encoding="utf-8"
        )
        (MEMBERS_AUTO_DIR / f"{slug}.publications.html").write_text(
            build_publications_section(member_pubs, author_to_slug) + "\n",
            encoding="utf-8",
        )
        (MEMBERS_AUTO_DIR / f"{slug}.dissertations.html").write_text(
            build_dissertations_section(member_diss) + "\n", encoding="utf-8"
        )

        print(
            f"  {member['name']:30} → {slug:30} ({len(member_pubs)} pubs, {len(member_diss)} diss)"
        )

    removed_pages = remove_stale_pages(MEMBERS_OUTPUT_DIR, valid_slugs)
    removed_partials = remove_stale_auto_partials(MEMBERS_AUTO_DIR, valid_slugs)

    for file_path in removed_pages:
        print(f"  removed page: {file_path.relative_to(ROOT)}")
    for file_path in removed_partials:
        print(f"  removed partial: {file_path.relative_to(ROOT)}")

    print(f"\nGenerated {len(all_members)} member pages in {MEMBERS_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
