## v1.3.0 — Calibration (smile + surface)

- Black–Scholes upgraded to support continuous dividend yield `q` (pricing, Greeks, implied vol)
- Calibration layer upgraded:
  - PCHIP smile fit (`fit_iv_smile_pchip`)
  - total-variance surface construction on log-moneyness (`iv_surface_total_variance`)
  - static-arbitrage sanity check helper for call prices vs strike
- API: new calibration endpoints + `q` in Black–Scholes requests
- Reader: added Calibration chapter

## v1.2.0 — Variance Reduction Pro Pack

- QMC methods: `sobol`, `halton` (+ optional scramble)
- Multi-control variates for Asian and Basket MC
- Diagnostics report generator under `scripts/vr_pro_report.py`

