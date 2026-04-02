from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
CODE_DIR = ROOT / "src" / "content" / "codes"
KNOWN_CODES = {path.stem for path in CODE_DIR.glob("*.md")}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping at the top level of {path}")

    return data


def ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Expected list value, got {type(value).__name__}")
    return [str(item).strip() for item in value if str(item).strip()]


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def escape_text(value: Any) -> str:
    if value is None:
        return ""
    normalized = html.unescape(strip_tags(str(value)))
    normalized = " ".join(normalized.split())
    return html.escape(normalized, quote=True)


def slugify(text: str) -> str:
    """Convert text to URL-safe ASCII slug, normalizing special characters."""
    import re
    import unicodedata

    # Normalize unicode characters to ASCII equivalents (NFD decomposition)
    slug = unicodedata.normalize("NFD", text)
    slug = slug.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    slug = slug.lower().strip()

    # Replace spaces and underscores with hyphens, remove other special chars
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def get_known_members() -> set[str]:
    """Get set of known member slugs."""
    members_dir = ROOT / "src" / "content" / "members"
    return {path.stem for path in members_dir.glob("*.astro")}


def generate_standard_aliases(name: str) -> list[str]:
    """Generate standard name variations for alias matching.

    For "John Smith-Jones", generates:
    - john smith-jones (full normalized name)
    - j. smith-jones, j smith-jones, smith-jones, j., smith-jones, j, etc.
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
    last_part = parts[-1]      # Last part

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


def build_author_to_slug_map(members_file: Path | None = None) -> dict[str, str]:
    """Build a mapping from author names/aliases to member page slugs."""
    if members_file is None:
        members_file = ROOT / "data" / "members.yml"

    mapping = {}
    try:
        raw = load_yaml(members_file).get("members", [])
        for entry in raw:
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            slug = slugify(name)

            # Map the full name
            mapping[name.lower()] = slug

            # Map auto-generated standard aliases
            auto_aliases = generate_standard_aliases(name)
            for alias in auto_aliases:
                mapping[alias.lower()] = slug

            # Map manually-specified aliases
            aliases = entry.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    alias_str = str(alias).strip()
                    if alias_str:
                        mapping[alias_str.lower()] = slug
    except Exception:
        pass

    return mapping


def render_code_links(codes: list[str]) -> str:
    if not codes:
        return ""

    rendered = []
    for code in codes:
        label = escape_text(code)
        if code in KNOWN_CODES:
            rendered.append(
                f'<a href="/codes/{html.escape(code, quote=True)}/">{label}</a>'
            )
        else:
            rendered.append(label)

    return ", ".join(rendered)


def render_author_name(author: str, author_to_slug: dict[str, str] | None = None) -> str:
    """Render author name as a link if they have a member page."""
    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    label = escape_text(author)
    author_lower = author.lower().strip()

    # Check for exact match or any match in the mapping
    if author_lower in author_to_slug:
        slug = author_to_slug[author_lower]
        return f'<a href="/members/{html.escape(slug, quote=True)}/">{label}</a>'

    return label


def render_author_list(authors: str, author_to_slug: dict[str, str] | None = None) -> str:
    """Render comma-separated author list with links for known members."""
    if not authors:
        return ""
    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    author_names = [a.strip() for a in authors.split(",")]
    rendered = [render_author_name(name, author_to_slug) for name in author_names]
    return ", ".join(rendered)


def render_related(groups: list[str], codes: list[str]) -> str:
    parts = []
    if groups:
        parts.append(f"Groups: {', '.join(escape_text(group) for group in groups)}")
    if codes:
        parts.append(f"Codes: {render_code_links(codes)}")
    return "<br>".join(parts)


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
