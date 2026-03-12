import re
from pathlib import Path


def _title_from_markdown(markdown_path: Path) -> str:
    try:
        for line in markdown_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass

    stem = markdown_path.stem
    if stem.isupper():
        return stem
    if re.fullmatch(r"[a-z0-9]+", stem):
        return stem.upper()
    return stem.replace("-", " ").replace("_", " ").title()


def on_config(config):
    docs_dir = Path(config["docs_dir"])
    codes_dir = docs_dir / "codes"

    code_pages = []
    if codes_dir.exists():
        for markdown_file in sorted(codes_dir.glob("*.md")):
            if markdown_file.name.lower() == "index.md":
                continue
            rel_path = markdown_file.relative_to(docs_dir).as_posix()
            title = _title_from_markdown(markdown_file)
            code_pages.append({title: rel_path})

    config["nav"] = [
        {"Home": "index.md"},
        {
            "Codes": [
                {"Overview": "codes.md"},
                *code_pages,
            ]
        },
        {"Publications": "publications.md"},
        {"Dissertations": "dissertations.md"},
        {"Members": "members.md"},
    ]

    return config
