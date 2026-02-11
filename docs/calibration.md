# Calibration hooks (Step 3)

The library includes minimal entrypoints to support market-data calibration workflows.

## IV curve

```python
import numpy as np
from stats237_quantlib.public_api import implied_vols_from_prices, fit_iv_curve

strikes = np.array([90, 100, 110], dtype=float)
prices  = np.array([13.4, 8.43, 4.7], dtype=float)

vols = implied_vols_from_prices(strikes=strikes, prices=prices, S0=100, r=0.01, T=1.0, is_call=True)
vol_of_k = fit_iv_curve(strikes=strikes, vols=vols, kind="linear")

print(vol_of_k(np.array([95, 105])))
```

## IV surface

```python
from stats237_quantlib.public_api import iv_surface_linear

points = np.array([
    [0.5, 90], [0.5, 100], [0.5, 110],
    [1.0, 90], [1.0, 100], [1.0, 110],
])
values = np.array([0.23, 0.20, 0.21, 0.25, 0.22, 0.23])

surf = iv_surface_linear(points=points, values=values)
print(surf(np.array([0.75]), np.array([100])))
```

These hooks deliberately avoid enforcing arbitrage-free structure (that’s v1.2+ work).
