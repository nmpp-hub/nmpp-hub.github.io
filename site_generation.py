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


def render_code_links(codes: list[str]) -> str:
    if not codes:
        return ""

    rendered = []
    for code in codes:
        label = escape_text(code)
        if code in KNOWN_CODES:
            rendered.append(f'<a href="/codes/{html.escape(code, quote=True)}/">{label}</a>')
        else:
            rendered.append(label)

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
