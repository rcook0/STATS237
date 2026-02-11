"""One-command research-grade build.

- Ingest PDFs/ZIPs from inputs/ (if present)
- Extract typed text, build problem bank + coverage matrix
- Run tests
- Build book (HTML via MkDocs) + PDF fallback export
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


def main() -> None:
    # 1) Ingestion if inputs contain something beyond README
    inputs = ROOT / "inputs"
    has_inputs = any(p for p in inputs.iterdir() if p.is_file() and p.name.lower() != "readme.md")

    if has_inputs:
        run([sys.executable, "scripts/ingest.py"])
        run([sys.executable, "scripts/extract_text.py"])
        run([sys.executable, "scripts/problem_bank.py"])
        run([sys.executable, "scripts/coverage_matrix.py"])

    # 2) Chapter registry and generated pages
    run([sys.executable, "scripts/build_chapter_registry.py"])
    run([sys.executable, "scripts/build_book.py"])

    # 3) tests
    run([sys.executable, "-m", "pytest", "-q"])

    # 4) HTML build (if mkdocs installed)
    try:
        import mkdocs  # noqa: F401
        run(["mkdocs", "-f", "book/mkdocs.yml", "build"])
    except Exception:
        print("(mkdocs not installed — skipping HTML site build)")

    # 5) PDF fallback always (ReportLab)
    run([sys.executable, "scripts/export_reader_pdf.py"])


if __name__ == "__main__":
    main()
