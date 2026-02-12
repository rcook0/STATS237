#!/usr/bin/env python3
"""
Ingest PDFs/ZIPs from inputs/ into materials/ and produce a materials registry.

Registry fields:
- id, filename, kind (slides/notes/hw/final/handout/unknown), sha256, pages, extracted_at, source_path
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json, zipfile, re, datetime
from typing import List, Dict, Any, Tuple

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
MATERIALS = ROOT / "materials"
REGISTRY = ROOT / "registry" / "materials_registry.json"

KIND_RULES = [
    ("notes", re.compile(r"notes|handwritten", re.I)),
    ("slides", re.compile(r"slides|lecture|deck|stats237(?!hw)", re.I)),
    ("hw", re.compile(r"hw|homework|assignment|stats237hw", re.I)),
    ("final", re.compile(r"final|exam", re.I)),
    ("handout", re.compile(r"conditionalexpectation|handout", re.I)),
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(name: str) -> str:
    for kind, rx in KIND_RULES:
        if rx.search(name):
            return kind
    return "unknown"

def extract_zip(zpath: Path, outdir: Path) -> List[Path]:
    pdfs: List[Path] = []
    with zipfile.ZipFile(zpath, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            # only extract PDFs + nested zips
            low = info.filename.lower()
            if low.endswith(".pdf") or low.endswith(".zip"):
                target = outdir / Path(info.filename).name
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, target.open("wb") as dst:
                    dst.write(src.read())
                if low.endswith(".pdf"):
                    pdfs.append(target)
                elif low.endswith(".zip"):
                    pdfs.extend(extract_zip(target, outdir))
    return pdfs

def discover_inputs() -> List[Path]:
    items = []
    for p in INPUTS.glob("*"):
        if p.is_file() and (p.suffix.lower() in [".pdf", ".zip"]):
            items.append(p)
    return sorted(items)

def count_pages(pdf_path: Path) -> int:
    r = PdfReader(str(pdf_path))
    return len(r.pages)

def main() -> None:
    MATERIALS.mkdir(exist_ok=True, parents=True)
    extracted_dir = MATERIALS / "src"
    extracted_dir.mkdir(exist_ok=True, parents=True)

    pdfs: List[Path] = []
    for item in discover_inputs():
        if item.suffix.lower() == ".pdf":
            tgt = extracted_dir / item.name
            if tgt.resolve() != item.resolve():
                tgt.write_bytes(item.read_bytes())
            pdfs.append(tgt)
        elif item.suffix.lower() == ".zip":
            pdfs.extend(extract_zip(item, extracted_dir))

    entries: List[Dict[str, Any]] = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for p in sorted(set(pdfs)):
        try:
            pages = count_pages(p)
        except Exception as e:
            pages = None
        entry = {
            "id": hashlib.sha1(p.name.encode("utf-8")).hexdigest()[:10],
            "filename": p.name,
            "kind": classify(p.name),
            "sha256": sha256_file(p),
            "pages": pages,
            "extracted_at": now,
            "source_path": str(p.relative_to(ROOT)),
        }
        entries.append(entry)

    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps({"generated_at": now, "materials": entries}, indent=2))
    print(f"Wrote {REGISTRY} ({len(entries)} materials)")

if __name__ == "__main__":
    main()
