# Release Notes

## v0.9.0 — Reading Edition

Adds a **Reading Edition** pipeline for scanned handwritten notes:

- Auto-crop to ink
- Contrast normalization
- Optional two-up layout
- Manifest output (parameters, per-page crop stats, input SHA256)

Run:

```bash
python scripts/build_reading_edition.py
```

Outputs land in `build/reading_edition/`.