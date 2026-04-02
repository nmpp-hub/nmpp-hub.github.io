from __future__ import annotations

from pathlib import Path

from site_generation import (
    build_author_to_slug_map,
    ensure_list,
    escape_text,
    load_yaml,
    render_author_name,
    render_code_links,
    write_text,
)

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "dissertations.yml"
OUTPUT_FILE = ROOT / "src" / "pages" / "dissertations.astro"

DEGREE_LABELS = {
    "phd": "PhD",
    "msc": "MSc",
}


def validate_dissertation(raw: dict, index: int) -> dict:
    year = int(raw.get("year"))
    title = str(raw.get("title", "")).strip()
    author = str(raw.get("author", "")).strip()
    degree = str(raw.get("degree", "")).strip().lower()
    institution = str(raw.get("institution", "")).strip()
    link = str(raw.get("link", "")).strip()
    groups = ensure_list(raw.get("groups", []))
    codes = ensure_list(raw.get("codes", []))

    if not title:
        raise ValueError(f"Dissertation {index} is missing a title")
    if not author:
        raise ValueError(f"Dissertation {title} is missing an author")
    if degree not in DEGREE_LABELS:
        raise ValueError(f"Dissertation {title} has invalid degree {degree!r}")
    if not link:
        raise ValueError(f"Dissertation {title} is missing a link")

    return {
        "year": year,
        "title": title,
        "author": author,
        "degree": degree,
        "institution": institution,
        "link": link,
        "groups": groups,
        "codes": codes,
    }


def render_degree_and_institution(dissertation: dict) -> str:
    degree = DEGREE_LABELS[dissertation["degree"]]
    institution = dissertation["institution"]
    return escape_text(f"{degree} / {institution}" if institution else degree)


def build_page(dissertations: list[dict], author_to_slug: dict[str, str] | None = None) -> str:
    if author_to_slug is None:
        author_to_slug = build_author_to_slug_map()

    rows = []
    for dissertation in dissertations:
        rows.append(
            "\n".join(
                [
                    "        <tr>",
                    f"          <td>{dissertation['year']}</td>",
                    f"          <td>{escape_text(dissertation['title'])}</td>",
                    f"          <td>{render_author_name(dissertation['author'], author_to_slug)}</td>",
                    f"          <td>{render_degree_and_institution(dissertation)}</td>",
                    f"          <td>{render_code_links(dissertation['codes'])}</td>",
                    f"          <td><a href=\"{escape_text(dissertation['link'])}\">Full text</a></td>",
                    "        </tr>",
                ]
            )
        )

    body = "\n".join(rows)
    return f"""---
import Base from '../layouts/Base.astro';
---

<Base title="Dissertations">
  <div class="page-wrapper">
    <div class="page-header">
      <h1>Dissertations</h1>
      <p>Search and filter dissertations related to NMPP division research at IPP.</p>
    </div>

    <input id="pub-search" type="search" placeholder="Search by title, author, year, degree, institution, group, code, or keyword..." aria-label="Search dissertations" />

    <table id="publications-table">
      <thead>
        <tr>
          <th>Year</th>
          <th>Title</th>
          <th>Author</th>
          <th>Degree</th>
          <th>Codes</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
{body}
      </tbody>
    </table>
  </div>
</Base>

<script>
  document.addEventListener('DOMContentLoaded', function () {{
    const input = document.getElementById('pub-search') as HTMLInputElement | null;
    const table = document.getElementById('publications-table') as HTMLTableElement | null;
    if (!input || !table || !table.tBodies.length) return;
    const rows = Array.from(table.tBodies[0].rows);

    function normalize(text: string) {{
      return text.toLowerCase();
    }}

    input.addEventListener('input', function () {{
      const query = normalize(input.value.trim());
      rows.forEach(row => {{
        const visible = query === '' || normalize(row.textContent ?? '').includes(query);
        row.style.display = visible ? '' : 'none';
      }});
    }});
  }});
</script>
"""


def main() -> None:
    raw_dissertations = load_yaml(DATA_FILE).get("dissertations", [])
    if not isinstance(raw_dissertations, list):
        raise ValueError(
            "dissertations.yml must contain a top-level 'dissertations' list"
        )

    dissertations = [
        validate_dissertation(raw_dissertation, index + 1)
        for index, raw_dissertation in enumerate(raw_dissertations)
    ]
    dissertations.sort(
        key=lambda dissertation: (-dissertation["year"], dissertation["author"].lower())
    )

    author_to_slug = build_author_to_slug_map()
    write_text(OUTPUT_FILE, build_page(dissertations, author_to_slug))
    print(f"Updated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
