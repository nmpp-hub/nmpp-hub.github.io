"""Generate the main members page with card-based layout for all staff.

Reads members.yml and generates src/pages/members.astro with card layouts
for all staff members (professors, permanent staff, postdocs, students, etc)
instead of boring tables. Uses default avatar if no profile picture.

Run as part of generate_website.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path to import site_generation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import (
    escape_text,
    load_yaml,
    render_code_links,
    write_text,
)

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "data" / "members.yml"
OUTPUT_FILE = ROOT / "src" / "pages" / "members.astro"

ROLE_ORDER = ["professor", "group leader", "permanent staff", "postdoc", "phd", "msc", "admin staff"]
ROLE_TITLES = {
    "professor": "Professors",
    "group leader": "Group Leaders",
    "permanent staff": "Permanent Staff",
    "postdoc": "Postdocs",
    "phd": "PhD Students",
    "msc": "MSc Students",
    "admin staff": "Administrative Staff",
}


def slugify(text: str) -> str:
    """Convert text to URL-safe ASCII slug."""
    import re
    import unicodedata

    slug = unicodedata.normalize("NFD", text)
    slug = slug.encode("ascii", "ignore").decode("ascii")
    slug = slug.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def get_member_photo(member: dict) -> str:
    """Get img tag for member photo or default avatar."""
    if member.get("picture"):
        src = escape_text(member["picture"])
        alt = escape_text(member["name"])
        return f'<img src="{src}" alt="{alt}" class="member-photo-circle" />'
    return '<div class="member-photo-circle member-photo-placeholder"></div>'


def render_member_card(member: dict) -> str:
    """Render a member as a card with photo, name, and topic."""
    slug = slugify(member["name"])
    photo = get_member_photo(member)
    name = escape_text(member["name"])
    topic = escape_text(member.get("topic", ""))

    return f"""      <a href="/members/{slug}/" class="member-card-link">
        <div class="member-card">
          {photo}
          <div class="member-card-name">{name}</div>
          <div class="member-card-topic">{topic}</div>
        </div>
      </a>"""


def render_alumni_card(member: dict) -> str:
    """Render an alumni member card."""
    slug = slugify(member["name"])
    photo = get_member_photo(member)
    name = escape_text(member["name"])
    role_map = {"phd": "PhD", "msc": "MSc"}
    role = role_map.get(member.get("role"), member.get("role", ""))
    topic = escape_text(member.get("topic", ""))

    return f"""      <a href="/members/{slug}/" class="member-card-link">
        <div class="member-card">
          {photo}
          <div class="member-card-name">{name}</div>
          <div class="member-card-role">{role}</div>
          <div class="member-card-topic">{topic}</div>
        </div>
      </a>"""


def validate_member(raw: dict, index: int) -> dict:
    """Validate and normalize member data."""
    name = str(raw.get("name", "")).strip()
    if not name:
        raise ValueError(f"Member {index} is missing a name")

    return {
        "name": name,
        "role": str(raw.get("role", "")).strip().lower(),
        "topic": str(raw.get("topic", "")).strip(),
        "group": str(raw.get("group", "")).strip(),
        "codes": raw.get("codes", []),
        "alumni": bool(raw.get("alumni", False)),
        "picture": str(raw.get("picture", "") or "").strip(),
    }


def build_page(members: list[dict]) -> str:
    """Build the members page with card layouts."""
    active_sections = []

    # Active members by role
    for role in ROLE_ORDER:
        role_members = [m for m in members if m["role"] == role and not m["alumni"]]
        if not role_members:
            continue

        cards = "\n".join(render_member_card(m) for m in role_members)
        section = f"""      <h2>{ROLE_TITLES[role]}</h2>
      <div class="member-cards">
{cards}
      </div>"""
        active_sections.append(section)

    # Alumni
    alumni = [m for m in members if m["alumni"]]
    if alumni:
        cards = "\n".join(render_alumni_card(m) for m in alumni)
        alumni_section = f"""      <h2>Alumni</h2>
      <div class="member-cards">
{cards}
      </div>"""
    else:
        alumni_section = "      <h2>Alumni</h2>\n      <p>No entries yet.</p>"

    sections = "\n\n".join(active_sections + [alumni_section])
    return f"""---
import Base from '../layouts/Base.astro';
---

<Base title="Members">
  <div class="page-wrapper">
    <div class="page-header">
      <h1>Members</h1>
      <p>NMPP division members at IPP.</p>
    </div>
    <div class="prose">
{sections}
    </div>
  </div>
</Base>
"""


def main() -> None:
    """Generate the members page."""
    raw_members = load_yaml(MEMBERS_FILE).get("members", [])
    if not isinstance(raw_members, list):
        raise ValueError("members.yml must contain a top-level 'members' list")

    members = [
        validate_member(raw_member, index + 1)
        for index, raw_member in enumerate(raw_members)
    ]

    write_text(OUTPUT_FILE, build_page(members))
    print(f"Updated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
