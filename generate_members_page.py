from __future__ import annotations

from pathlib import Path

from site_generation import (
    ensure_list,
    escape_text,
    load_yaml,
    render_code_links,
    write_text,
)

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "members.yml"
OUTPUT_FILE = ROOT / "src" / "pages" / "members.astro"

ROLE_ORDER = ["permanent staff", "postdoc", "phd", "msc"]
ROLE_TITLES = {
    "permanent staff": "Permanent Staff",
    "postdoc": "Postdocs",
    "phd": "PhD Students",
    "msc": "MSc Students",
}
ROLE_LABELS = {
    "permanent staff": "Permanent staff",
    "postdoc": "Postdoc",
    "phd": "PhD",
    "msc": "MSc",
}


def validate_member(raw: dict, index: int) -> dict:
    name = str(raw.get("name", "")).strip()
    role = str(raw.get("role", "")).strip().lower()
    topic = str(raw.get("topic", "")).strip()
    contact = str(raw.get("contact", "")).strip()
    group = str(raw.get("group", "")).strip()
    codes = ensure_list(raw.get("codes", []))
    aliases = ensure_list(raw.get("aliases", []))
    alumni = bool(raw.get("alumni", False))

    if not name:
        raise ValueError(f"Member {index} is missing a name")
    if role not in ROLE_ORDER:
        raise ValueError(f"Member {name} has invalid role {role!r}")
    if not topic:
        raise ValueError(f"Member {name} is missing a topic")
    if not group:
        raise ValueError(f"Member {name} is missing a group")

    return {
        "name": name,
        "role": role,
        "topic": topic,
        "contact": contact,
        "group": group,
        "codes": codes,
        "aliases": aliases,
        "alumni": alumni,
    }


def render_member_rows(members: list[dict]) -> str:
    rows = []
    for member in members:
        rows.append(
            "\n".join(
                [
                    "        <tr>",
                    f"          <td>{escape_text(member['name'])}</td>",
                    f"          <td>{escape_text(member['topic'])}</td>",
                    f"          <td>{escape_text(member['contact'])}</td>",
                    f"          <td>{escape_text(member['group'])}</td>",
                    f"          <td>{render_code_links(member['codes'])}</td>",
                    "        </tr>",
                ]
            )
        )
    return "\n".join(rows)


def render_alumni_rows(members: list[dict]) -> str:
    rows = []
    for member in members:
        rows.append(
            "\n".join(
                [
                    "        <tr>",
                    f"          <td>{escape_text(member['name'])}</td>",
                    f"          <td>{escape_text(ROLE_LABELS[member['role']])}</td>",
                    f"          <td>{escape_text(member['topic'])}</td>",
                    f"          <td>{escape_text(member['contact'])}</td>",
                    f"          <td>{escape_text(member['group'])}</td>",
                    f"          <td>{render_code_links(member['codes'])}</td>",
                    "        </tr>",
                ]
            )
        )
    return "\n".join(rows)


def render_role_section(title: str, members: list[dict]) -> str:
    if not members:
        return f"""      <h2>{title}</h2>
      <p>No entries yet.</p>"""

    rows = render_member_rows(members)
    return f"""      <h2>{title}</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Topic</th>
            <th>Contact</th>
            <th>Group</th>
            <th>Codes</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>"""


def build_page(members: list[dict]) -> str:
    active_sections = []
    for role in ROLE_ORDER:
        role_members = [
            member
            for member in members
            if member["role"] == role and not member["alumni"]
        ]
        active_sections.append(render_role_section(ROLE_TITLES[role], role_members))

    alumni = [member for member in members if member["alumni"]]
    alumni_rows = render_alumni_rows(alumni)
    alumni_section = (
        f"""      <h2>Alumni</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Role</th>
            <th>Topic</th>
            <th>Contact</th>
            <th>Group</th>
            <th>Codes</th>
          </tr>
        </thead>
        <tbody>
{alumni_rows}
        </tbody>
      </table>"""
        if alumni
        else "      <h2>Alumni</h2>\n      <p>No entries yet.</p>"
    )

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
    raw_members = load_yaml(DATA_FILE).get("members", [])
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
