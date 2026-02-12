# Release Notes

## v0.10.0 — Pre-v1 ship gates

Adds the remaining pre-v1 “ship gates”:

- Problems → Tests (spec-driven pytest)
- Public API freeze + SemVer policy
- Calibration hooks (IV curve + surface)
- Golden runs (deterministic regression checks)
- Docker deployment scaffolding

### Reading Edition (still included)

The Reading Edition pipeline for scanned handwritten notes remains:

- Auto-crop to ink
- Contrast normalization
- Optional two-up layout
- Manifest output (parameters, per-page crop stats, input SHA256)

Run:

```bash
python scripts/build_reading_edition.py
```

Outputs land in `build/reading_edition/`.