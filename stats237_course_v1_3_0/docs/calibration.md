# Calibration (v1.3)

v1.3 upgrades the earlier “hooks” into a small **smile + surface** layer that is stable enough
for research workflows:

- implied vols from prices (supports dividend yield `q`)
- **PCHIP smile fit** (shape-preserving cubic)
- **total-variance surface** construction on log-moneyness
- basic static-arb **sanity checks** (warnings/flags; not enforced constraints)

## IV curve from prices → smile

```python
import numpy as np
from stats237_quantlib.public_api import (
    implied_vols_from_prices,
    fit_iv_smile_pchip,
)

S0, r, q, T = 100.0, 0.02, 0.01, 0.5
strikes = np.array([80, 90, 100, 110, 120], dtype=float)
prices  = np.array([21.9, 13.1, 6.2, 2.5, 0.9], dtype=float)  # example calls

vols = implied_vols_from_prices(strikes=strikes, prices=prices, S0=S0, r=r, q=q, T=T, is_call=True)
smile = fit_iv_smile_pchip(strikes=strikes, vols=vols)

print(smile(np.array([95, 105], dtype=float)))
```

## IV surface via total variance

```python
import numpy as np
from stats237_quantlib.public_api import iv_surface_total_variance
from stats237_quantlib.calibration.iv_curve import SmileSlice

S0, r, q = 100.0, 0.02, 0.01

smiles = [
    SmileSlice(T=0.5, strikes=np.array([90, 100, 110]), vols=np.array([0.24, 0.20, 0.22])),
    SmileSlice(T=1.0, strikes=np.array([90, 100, 110]), vols=np.array([0.26, 0.22, 0.24])),
]

surf = iv_surface_total_variance(smiles=smiles, S0=S0, r=r, q=q)

Tq = np.array([0.75, 0.75, 0.75])
Kq = np.array([90, 100, 110])
print(surf(Tq, Kq))
```

## Sanity check: call prices vs strike

```python
import numpy as np
from stats237_quantlib.public_api import sanity_check_call_prices_convex_in_strike

K = np.array([90, 100, 110], dtype=float)
C = np.array([12.0, 7.0, 3.5], dtype=float)
print(sanity_check_call_prices_convex_in_strike(K, C))
```

Notes:
- This layer **does not guarantee** arbitrage-free fits. It’s a stable scaffold.
- The surface uses **total variance** interpolation, which is typically better-behaved than interpolating vol directly.
