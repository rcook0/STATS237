# Calibration

This chapter is the bridge from “toy models” to “market data”.

Stats237 v1.3 provides a compact calibration layer:

- compute implied vols from option prices (Black–Scholes with dividend yield `q`)
- fit a smile with **PCHIP** (shape-preserving cubic)
- build a simple **surface** by interpolating **total variance** on log-moneyness

The goal is stability + reproducibility, not a full arbitrage-free model.

## Implied vol from prices

Given observed prices at a maturity, compute implied vols strike-by-strike:

```python
import numpy as np
from stats237_quantlib.public_api import implied_vols_from_prices

S0, r, q, T = 100.0, 0.02, 0.01, 0.5
K = np.array([80, 90, 100, 110, 120], dtype=float)
C = np.array([21.9, 13.1, 6.2, 2.5, 0.9], dtype=float)

iv = implied_vols_from_prices(strikes=K, prices=C, S0=S0, r=r, q=q, T=T, is_call=True)
print(iv)
```

## Smile fit (PCHIP)

```python
from stats237_quantlib.public_api import fit_iv_smile_pchip

smile = fit_iv_smile_pchip(strikes=K, vols=iv)
print(smile(np.array([95, 105], dtype=float)))
```

## Simple surface (total variance)

```python
from stats237_quantlib.public_api import iv_surface_total_variance
from stats237_quantlib.calibration.iv_curve import SmileSlice

smiles = [
    SmileSlice(T=0.5, strikes=K, vols=iv),
    SmileSlice(T=1.0, strikes=K, vols=iv + 0.02),
]

surf = iv_surface_total_variance(smiles=smiles, S0=S0, r=r, q=q)
print(surf(np.array([0.75]), np.array([100.0])))
```

## Sanity checks

These don’t enforce no-arbitrage, but they flag the obvious:

- call price should be non-increasing in strike
- call price should be convex in strike

```python
from stats237_quantlib.public_api import sanity_check_call_prices_convex_in_strike
print(sanity_check_call_prices_convex_in_strike(K, C))
```
