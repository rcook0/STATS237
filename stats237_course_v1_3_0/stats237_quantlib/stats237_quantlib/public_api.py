"""Public API (stable imports).

The goal: downstream notebooks/services import from **one place** so we can
refactor internals without breaking users.

Example
-------
>>> from stats237_quantlib.public_api import bs_call, implied_vol
"""

from __future__ import annotations

# Black–Scholes
from .pricing.black_scholes import bs_call, bs_put, greeks_call_put, implied_vol

# Binomial (CRR)
from .pricing.binomial import CRRParams, crr_european, crr_american, one_step_replication

# No-arbitrage helpers
from .pricing.no_arb import bounds_european_call_put, put_call_parity_residual

# Monte Carlo + exotics
from .mc.asian import arithmetic_asian_call_mc, geometric_asian_call_closed_form
from .mc.basket import basket_call_mc_vr, geometric_basket_call_closed_form
from .mc.core import mc_mean_ci

# Calibration
from .calibration.iv_curve import (
    implied_vols_from_prices,
    fit_iv_curve,
    fit_iv_smile_pchip,
    iv_surface_linear,
    iv_surface_total_variance,
    sanity_check_call_prices_convex_in_strike,
)

__all__ = [
    # BS
    "bs_call",
    "bs_put",
    "greeks_call_put",
    "implied_vol",
    # Binomial
    "CRRParams",
    "crr_european",
    "crr_american",
    "one_step_replication",
    # No-arb
    "bounds_european_call_put",
    "put_call_parity_residual",
    # MC/exotics
    "arithmetic_asian_call_mc",
    "geometric_asian_call_closed_form",
    "basket_call_mc_vr",
    "geometric_basket_call_closed_form",
    "mc_mean_ci",
    # Calibration
    "implied_vols_from_prices",
    "fit_iv_curve",
    "fit_iv_smile_pchip",
    "iv_surface_linear",
    "iv_surface_total_variance",
    "sanity_check_call_prices_convex_in_strike",
]
