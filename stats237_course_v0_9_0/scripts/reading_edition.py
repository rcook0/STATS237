"""Reading Edition: crop + contrast normalization for scanned handwriting.

Design goals:
 - deterministic outputs given same input + parameters
 - keep dependencies light (pymupdf + pillow + numpy)
 - produce a manifest with crop stats + input hash for provenance

This script is safe to run on any PDF (typed or scanned), but it shines on
camera-scanned handwritten notes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

try:
    import fitz  # pymupdf
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "pymupdf is required for the Reading Edition. Install with: pip install pymupdf"
    ) from e

from PIL import Image, ImageOps


@dataclass(frozen=True)
class ReadingEditionParams:
    dpi: int = 220
    threshold: int = 245
    pad: int = 18
    mode: str = "single"  # single|twoup
    margin_pt: int = 18


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def render_pdf_pages(pdf_path: Path, dpi: int) -> List[Image.Image]:
    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    images: List[Image.Image] = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        mode = "RGB" if pix.n < 4 else "RGBA"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        if mode == "RGBA":
            img = img.convert("RGB")
        images.append(img)
    doc.close()
    return images


def _ink_bbox(gray: np.ndarray, threshold: int) -> Tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) bbox of non-white pixels, or None."""
    # "Ink" defined as pixels darker than threshold.
    ys, xs = np.where(gray < threshold)
    if xs.size == 0 or ys.size == 0:
        return None
    left = int(xs.min())
    right = int(xs.max()) + 1
    top = int(ys.min())
    bottom = int(ys.max()) + 1
    return left, top, right, bottom


def autocrop(img: Image.Image, threshold: int, pad: int) -> Tuple[Image.Image, dict]:
    """Crop margins by detecting ink. Returns (cropped_image, stats)."""
    gray_img = img.convert("L")
    gray = np.asarray(gray_img)
    bbox = _ink_bbox(gray, threshold)
    w, h = img.size
    if bbox is None:
        crop = img
        crop_box = (0, 0, w, h)
    else:
        l, t, r, b = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        r = min(w, r + pad)
        b = min(h, b + pad)
        crop_box = (l, t, r, b)
        crop = img.crop(crop_box)

    cw, ch = crop.size
    stats = {
        "orig_size_px": [w, h],
        "crop_box_px": list(crop_box),
        "cropped_size_px": [cw, ch],
        "cropped_area_ratio": float((cw * ch) / max(1, w * h)),
    }
    return crop, stats


def enhance_for_reading(img: Image.Image) -> Image.Image:
    # Auto-contrast is the biggest win with minimal risk.
    return ImageOps.autocontrast(img)


def twoup_pair(images: List[Image.Image]) -> List[Tuple[Image.Image, Image.Image | None]]:
    out: List[Tuple[Image.Image, Image.Image | None]] = []
    i = 0
    while i < len(images):
        left = images[i]
        right = images[i + 1] if i + 1 < len(images) else None
        out.append((left, right))
        i += 2
    return out


def build_pdf_single(
    out_pdf: Path,
    images: List[Image.Image],
    margin_pt: int,
) -> None:
    """Build a PDF where each image becomes one page (page size adapts to image aspect)."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(out_pdf))
    for img in images:
        w_px, h_px = img.size
        # choose A4 orientation based on aspect
        page_w, page_h = (landscape(A4) if w_px > h_px else A4)
        c.setPageSize((page_w, page_h))
        avail_w = page_w - 2 * margin_pt
        avail_h = page_h - 2 * margin_pt
        scale = min(avail_w / w_px, avail_h / h_px)
        draw_w = w_px * scale
        draw_h = h_px * scale
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2
        # ReportLab can take a PIL image via temp PNG
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            img.save(tmp.name, format="PNG")
            c.drawImage(tmp.name, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True)
        c.showPage()
    c.save()


def build_pdf_twoup(
    out_pdf: Path,
    pairs: List[Tuple[Image.Image, Image.Image | None]],
    margin_pt: int,
) -> None:
    """Build a PDF with two pages per sheet (side-by-side)."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    page_w, page_h = landscape(A4)
    c = canvas.Canvas(str(out_pdf), pagesize=(page_w, page_h))
    gutter = margin_pt
    slot_w = (page_w - 2 * margin_pt - gutter) / 2
    slot_h = page_h - 2 * margin_pt

    import tempfile

    for left, right in pairs:
        for idx, img in enumerate([left, right]):
            if img is None:
                continue
            w_px, h_px = img.size
            scale = min(slot_w / w_px, slot_h / h_px)
            draw_w = w_px * scale
            draw_h = h_px * scale
            x0 = margin_pt + (slot_w + gutter) * idx
            x = x0 + (slot_w - draw_w) / 2
            y = margin_pt + (slot_h - draw_h) / 2
            with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
                img.save(tmp.name, format="PNG")
                c.drawImage(tmp.name, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True)
        c.showPage()
    c.save()


def run_reading_edition(
    in_pdf: Path,
    out_pdf: Path,
    params: ReadingEditionParams,
) -> Path:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    images = render_pdf_pages(in_pdf, params.dpi)

    processed: List[Image.Image] = []
    per_page_stats: List[dict] = []
    for i, img in enumerate(images, start=1):
        cropped, stats = autocrop(img, threshold=params.threshold, pad=params.pad)
        enhanced = enhance_for_reading(cropped)
        processed.append(enhanced)
        stats["page"] = i
        per_page_stats.append(stats)

    if params.mode == "twoup":
        build_pdf_twoup(out_pdf, twoup_pair(processed), margin_pt=params.margin_pt)
    else:
        build_pdf_single(out_pdf, processed, margin_pt=params.margin_pt)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": str(in_pdf),
            "sha256": sha256_file(in_pdf),
        },
        "output": {"path": str(out_pdf)},
        "params": asdict(params),
        "pages": per_page_stats,
    }
    manifest_path = out_pdf.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_pdf


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a Reading Edition PDF (crop + contrast).")
    p.add_argument("--in", dest="in_pdf", required=True, help="Input PDF")
    p.add_argument("--out", dest="out_pdf", required=True, help="Output PDF")
    p.add_argument("--dpi", type=int, default=220)
    p.add_argument("--threshold", type=int, default=245)
    p.add_argument("--pad", type=int, default=18)
    p.add_argument("--mode", choices=["single", "twoup"], default="single")
    p.add_argument("--margin-pt", type=int, default=18)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    params = ReadingEditionParams(
        dpi=args.dpi,
        threshold=args.threshold,
        pad=args.pad,
        mode=args.mode,
        margin_pt=args.margin_pt,
    )
    run_reading_edition(Path(args.in_pdf), Path(args.out_pdf), params)


if __name__ == "__main__":
    main()
