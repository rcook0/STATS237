from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_YAML = ROOT / "chapters" / "chapters.yaml"
BOOK_DOCS = ROOT / "book" / "docs"
CHAPTERS_DIR = BOOK_DOCS / "chapters"


def main() -> None:
    data = yaml.safe_load(CHAPTERS_YAML.read_text(encoding="utf-8"))
    chapters = data.get("chapters", [])

    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    # index
    lines = ["# Chapters", "", "This index is generated from `chapters/chapters.yaml`.", ""]
    for ch in chapters:
        cid = ch["id"]
        title = ch["title"]
        lines.append(f"- [{title}]({cid}.md)")
    (CHAPTERS_DIR / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # chapter pages
    for ch in chapters:
        cid = ch["id"]
        title = ch["title"]
        focus = ch.get("focus", [])
        qmods = ch.get("quantlib", [])
        out = CHAPTERS_DIR / f"{cid}.md"

        body = [f"# {title}", "", "## Focus", ""]
        for item in focus:
            body.append(f"- {item}")
        body += ["", "## Quantlib modules", ""]
        for m in qmods:
            body.append(f"- `{m}`")
        body += ["", "## Problem-bank alignment", "", "See `coverage/coverage_report.md` after running the pipeline.", ""]

        # Preserve hand-edited chapter pages; only scaffold if missing.
        if not out.exists():
            out.write_text("\n".join(body) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
