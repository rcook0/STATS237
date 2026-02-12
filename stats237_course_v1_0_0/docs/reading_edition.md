# Reading Edition (handwritten notes)

The goal is to turn camera-scanned handwriting into a **screen-friendly** PDF without “destroying the vibe”.

This pipeline:

1. **Renders** each PDF page to an image (MuPDF / `pymupdf`).
2. **Auto-crops** to the ink (removes margins).
3. **Normalizes contrast** for readability.
4. Re-assembles into a new PDF (ReportLab).

## Fast path

Put notes into `inputs/` (PDF or ZIP). Files containing `note` / `notes` in the filename are auto-detected.

```bash
python scripts/build_reading_edition.py
```

Outputs:

- `build/reading_edition/<name>_ReadingEdition.pdf`
- `build/reading_edition/<name>_manifest.json` (parameters + per-page crop stats + SHA256)

## Manual CLI

```bash
python scripts/reading_edition.py \
  --in inputs/Notes-Stat237.pdf \
  --out build/reading_edition/Notes-Stat237_ReadingEdition.pdf \
  --dpi 220 \
  --threshold 245 \
  --pad 18 \
  --mode single
```

Two-up (two pages per sheet):

```bash
python scripts/reading_edition.py \
  --in inputs/Notes-Stat237.pdf \
  --out build/reading_edition/Notes-Stat237_ReadingEdition_twoup.pdf \
  --mode twoup
```

## Notes on “deskew”

Deskew is intentionally **off by default**. In practice, for handwriting scans, auto-deskew can sometimes “chase noise” and make pages worse.
If you want deskew later, we can add a robust method (Hough / projection profile) behind a `--deskew` flag.
