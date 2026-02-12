# Stats237 v0.7 — Reproducibility contract

The goal is: **same inputs → same outputs** (within floating-point tolerance), and every result is **auditable**.

## Response provenance envelope

Every API response is wrapped as:

```json
{ "provenance": { ... }, "result": { ... } }
```

`provenance` includes:
- `package_version` (stats237-quantlib version)
- `received_at` (UTC)
- `request_id` (client-supplied `X-Request-Id` or generated UUID)
- `request_hash` (stable SHA256 of canonical request JSON)
- `seed_effective` (the seed that actually drove randomness; deterministic endpoints still report it)
- `runtime` (python, numpy, scipy versions + platform)

## Seed policy

- Stochastic endpoints accept an explicit `seed`.
- If omitted, the default is **123**.
- The returned `seed_effective` is the source of truth.

Why: a missing seed should not silently produce unreproducible results.

## RNG algorithm

- NumPy `Generator` is used (default bit generator is typically `PCG64`).
- For antithetic sampling and LHS, the same seed produces the same sample stream.

## Floating-point caveats

Even with fixed seeds, some results can vary at the last decimal places across machines due to:
- CPU instruction differences (FMA, SIMD)
- BLAS/LAPACK implementations

The test suite asserts reproducibility using tolerances and, for variance-reduction, compares **relative** variance improvements rather than absolute numbers.

## Reproducing a run

To reproduce an API response:
1) Keep the request JSON identical.
2) Keep the `seed` identical (or rely on `seed_effective=123`).
3) Use the same `package_version`.

For long-lived reproducibility, pin dependencies in your environment and record:
- `package_version`
- python version
- numpy/scipy versions

