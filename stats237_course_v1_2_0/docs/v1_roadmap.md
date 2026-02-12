# v1 Roadmap

v1.x is the *stabilization* line: keep the public surface boring, predictable, and
reproducible, while we crank coverage and correctness.

## v1.0.0 — GA baseline

Ship criteria:

1) **Problems → Tests coverage**
   - `coverage/coverage_matrix.csv` exists (i.e., you've ingested inputs)
   - ≥70% of distinct problems are `ready` (or higher)

2) **Public API frozen**
   - `stats237_quantlib.public_api` is the only supported import surface

3) **OpenAPI freeze**
   - `api/openapi_snapshot.json` matches the live app schema

4) **Deterministic regression guards**
   - golden runs pass in CI (within tolerances)

5) **Distribution scaffolding**
   - `pip install -e stats237_quantlib` works cleanly
   - `docker compose up --build` runs the API

See `docs/release.md` for the gate runner.

## v1.1 — Reliability hardening

- Numerical edge-case suite (tiny T, extreme moneyness, tiny vol, etc.)
- More property tests (parity/bounds/monotonicity/convexity) where safe

## v1.2 — Variance reduction “pro”

- Quasi-MC (Sobol/Halton) + reproducible scrambling options
- Diagnostics in `reports/` (variance + CI width + convergence)

## v1.3 — Calibration v1

- Smile fitting + interpolation that is stable and transparent
- Basic no-arb sanity checks as warnings

## v1.4 — Reader citations + linking

- Per-problem backlinks: reader → test spec → function
- Better segmentation heuristics for PDFs
