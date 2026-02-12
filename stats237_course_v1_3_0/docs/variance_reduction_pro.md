# Variance Reduction Pro Pack (v1.2)

This release adds Quasi-Monte Carlo (Sobol/Halton), multi-control variates, and convergence reporting.

- Sampling methods: `plain`, `lhs`, `sobol`, `halton`
- Controls:
  - Asian: geometric Asian call + discounted terminal price
  - Basket: geometric basket call + discounted linear basket

Run the demo report:

```bash
python scripts/vr_pro_report.py
```

See `reports/vr_pro/vr_report.md`.
