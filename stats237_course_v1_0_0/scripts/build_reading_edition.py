"""Auto-detect handwritten notes in inputs/ and build a Reading Edition.

Heuristic:
 - any PDF with filename containing 'note' or 'notes'
 - any ZIP containing PDFs with filename containing 'note' or 'notes'

Outputs:
 - build/reading_edition/<stem>_ReadingEdition.pdf
 - alongside a <stem>_ReadingEdition.manifest.json
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Allow importing scripts/reading_edition.py when invoked as `python scripts/build_reading_edition.py`
sys.path.insert(0, str(ROOT / "scripts"))

from reading_edition import ReadingEditionParams, run_reading_edition  # noqa: E402


def iter_input_files() -> list[Path]:
    inputs = ROOT / "inputs"
    return [p for p in inputs.iterdir() if p.is_file() and p.name.lower() != "readme.md"]


def extract_zip(zip_path: Path, dst: Path) -> None:
    import zipfile

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dst)


def find_note_pdfs(paths: list[Path]) -> list[Path]:
    needles = ("note", "notes", "handwritten")
    out: list[Path] = []
    for p in paths:
        name = p.name.lower()
        if p.suffix.lower() == ".pdf" and any(n in name for n in needles):
            out.append(p)
    return out


def main() -> None:
    candidates = iter_input_files()
    build_dir = ROOT / "build" / "reading_edition"
    build_dir.mkdir(parents=True, exist_ok=True)

    note_pdfs: list[Path] = []
    tmp_dirs: list[Path] = []

    for c in candidates:
        if c.suffix.lower() == ".pdf":
            note_pdfs.extend(find_note_pdfs([c]))
        elif c.suffix.lower() == ".zip":
            tmp = Path(tempfile.mkdtemp(prefix="stats237_notes_"))
            tmp_dirs.append(tmp)
            extract_zip(c, tmp)
            pdfs = list(tmp.rglob("*.pdf"))
            note_pdfs.extend(find_note_pdfs(pdfs))

    note_pdfs = sorted(set(note_pdfs), key=lambda p: p.name.lower())

    if not note_pdfs:
        print("(no notes found in inputs/; skipping Reading Edition)")
        return

    params = ReadingEditionParams()
    for p in note_pdfs:
        out_pdf = build_dir / f"{p.stem}_ReadingEdition.pdf"
        print(f"+ reading edition: {p} -> {out_pdf}")
        run_reading_edition(p, out_pdf, params)

    # cleanup temp
    for d in tmp_dirs:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main()
