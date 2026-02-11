# v1 Roadmap

v1.0 should mean: **publishable + stable + reproducible**.

## v1.0 — “Course-as-spec” baseline

Ship criteria:

1. **Problem bank coverage push**
   - ≥80% of parsed problems moved from `pending` to `numeric` or `invariant`.
   - `coverage/coverage_matrix.csv` has no `unmapped` items among HW + final (handouts/slides can lag).

2. **Public API frozen**
   - `stats237_quantlib.public_api` is stable; internal refactors don’t break imports.
   - FastAPI request/response models versioned and documented.

3. **Calibration entrypoints usable**
   - `implied_vols_from_prices(...)`, `fit_iv_curve(...)`, `iv_surface_linear(...)` wired into examples.

4. **Deterministic regression guards**
   - Golden runs pass in CI (within tolerances).

5. **Distribution**
   - `pip install -e stats237_quantlib` works cleanly.
   - `docker compose up --build` runs the API.

## v1.1 — Reader polish + citations

- Better problem segmentation (fewer false splits)
- Inline references: each solved item links to source page ranges
- Optional OCR lane for notes (only where needed)

## v1.2 — Quant extensions (high-signal)

- Heston / SABR “toy but correct” modules
- Basic no-arb surface checks (calendar, butterfly) on fitted surfaces

## v1.3 — Performance lane

- Numba vectorization where it matters (MC paths)
- Batch pricing APIs (arrays in/out)

## v1.4 — Data adapters

- Minimal market-data adapters (CSV, parquet)
- Calibration workflows (quote sets -> fitted surface -> pricing)
