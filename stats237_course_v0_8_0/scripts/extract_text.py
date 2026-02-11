#!/usr/bin/env python3
"""
Extract per-page text from typed PDFs (slides/hw/final/handout).

Handwritten notes typically extract poorly without OCR; we skip them unless they contain meaningful text.
"""
from __future__ import annotations
from pathlib import Path
import json, datetime
from typing import Dict, Any, List

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "materials_registry.json"
OUTDIR = ROOT / "materials" / "text"

SKIP_KINDS = {"notes"}

def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    reg = json.loads(REGISTRY.read_text())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    n = 0
    for m in reg["materials"]:
        if m["kind"] in SKIP_KINDS:
            continue
        pdf_path = ROOT / m["source_path"]
        try:
            r = PdfReader(str(pdf_path))
        except Exception:
            continue
        pages: List[Dict[str, Any]] = []
        for i, page in enumerate(r.pages):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            pages.append({"page_index": i, "text": txt})
        out = {
            "material_id": m["id"],
            "filename": m["filename"],
            "kind": m["kind"],
            "extracted_at": now,
            "pages": pages,
        }
        (OUTDIR / f"{m['id']}.json").write_text(json.dumps(out, indent=2))
        n += 1

    print(f"Extracted text for {n} PDFs into {OUTDIR}")

if __name__ == "__main__":
    main()
