# Public API (Step 2)

This repo exposes a **stable surface** for downstream use.

Python
------

Import stable symbols from:

```python
from stats237_quantlib.public_api import (
    bs_call, bs_put, greeks_call_put, implied_vol,
    CRRParams, crr_european, crr_american, one_step_replication,
    bounds_european_call_put, put_call_parity_residual,
    arithmetic_asian_call_mc, geometric_asian_call_closed_form,
    basket_call_mc_vr, geometric_basket_call_closed_form,
    mc_mean_ci,
    implied_vols_from_prices, fit_iv_curve, iv_surface_linear,
)
```

REST
----

FastAPI server (OpenAPI docs):

- `GET /health`
- `GET /meta`
- `POST /price/black_scholes`
- `POST /greeks/black_scholes`
- `POST /implied_vol`
- `POST /price/binomial`
- `POST /mc/asian/arithmetic_call`
- `POST /mc/basket/call`

All responses are:

```json
{ "provenance": { ... }, "result": { ... } }
```

SemVer policy
------------

- **MAJOR**: breaking changes to `public_api.py` or request/response schemas.
- **MINOR**: new functions/endpoints added (backwards-compatible).
- **PATCH**: bug fixes, performance improvements, doc updates.