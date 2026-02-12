from __future__ import annotations

"""Implied-vol calibration hooks.

These functions are intentionally *minimal* and *composable*:

- Compute implied vols from observed option prices.
- Fit a 1D IV curve (strike -> vol).
- Fit a simple 2D IV surface (T, K -> vol) via linear interpolation.

The point is to provide a stable entrypoint for later upgrades:
smoothing, arbitrage-free constraints, splines, local vol, etc.
"""

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
from scipy.interpolate import interp1d, LinearNDInterpolator, NearestNDInterpolator

from ..pricing.black_scholes import implied_vol


def implied_vols_from_prices(
    *,
    strikes: np.ndarray,
    prices: np.ndarray,
    S0: float,
    r: float,
    T: float,
    is_call: bool = True,
    q: float = 0.0,
    clamp: tuple[float, float] = (1e-6, 5.0),
) -> np.ndarray:
    """Compute implied vols for a set of strikes.

    Parameters
    ----------
    strikes, prices:
        Arrays of equal length.
    clamp:
        Clamp implied vols to [lo, hi] (to keep later interpolators well-behaved).
    """
    strikes = np.asarray(strikes, dtype=float)
    prices = np.asarray(prices, dtype=float)
    if strikes.shape != prices.shape:
        raise ValueError("strikes and prices must have the same shape")

    vols = np.empty_like(strikes, dtype=float)
    lo, hi = clamp
    for i, (K, p) in enumerate(zip(strikes, prices)):
        v = implied_vol(price=float(p), S0=float(S0), K=float(K), r=float(r), T=float(T), q=float(q), is_call=bool(is_call))
        vols[i] = float(np.clip(v, lo, hi))
    return vols


def fit_iv_curve(
    *,
    strikes: np.ndarray,
    vols: np.ndarray,
    kind: str = "linear",
    fill: str = "extrapolate",
) -> Callable[[np.ndarray], np.ndarray]:
    """Fit a 1D implied-vol curve vol(K).

    Returns a callable that maps strikes -> vols.
    """
    strikes = np.asarray(strikes, dtype=float)
    vols = np.asarray(vols, dtype=float)
    if strikes.shape != vols.shape:
        raise ValueError("strikes and vols must have the same shape")

    # Ensure sorted for interpolation
    order = np.argsort(strikes)
    x = strikes[order]
    y = vols[order]

    f = interp1d(x, y, kind=kind, fill_value=fill, bounds_error=False, assume_sorted=True)

    def vol_of_k(K: np.ndarray) -> np.ndarray:
        return np.asarray(f(np.asarray(K, dtype=float)), dtype=float)

    return vol_of_k


def iv_surface_linear(
    *,
    points: np.ndarray,
    values: np.ndarray,
    fallback: str = "nearest",
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """Fit a simple IV surface vol(T, K) using linear interpolation.

    Parameters
    ----------
    points:
        Array shape (n, 2) with columns [T, K].
    values:
        Vols shape (n,).
    fallback:
        If linear interpolation is undefined at a query point, fallback to nearest.
    """
    pts = np.asarray(points, dtype=float)
    vals = np.asarray(values, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("points must be shape (n, 2) with columns [T, K]")
    if pts.shape[0] != vals.shape[0]:
        raise ValueError("points and values must have same number of rows")

    lin = LinearNDInterpolator(pts, vals)
    nn = NearestNDInterpolator(pts, vals) if fallback == "nearest" else None

    def vol_of_tk(T: np.ndarray, K: np.ndarray) -> np.ndarray:
        T = np.asarray(T, dtype=float)
        K = np.asarray(K, dtype=float)
        q = np.column_stack([T.ravel(), K.ravel()])
        out = lin(q)
        if nn is not None:
            mask = np.isnan(out)
            if np.any(mask):
                out[mask] = nn(q[mask])
        return np.asarray(out, dtype=float).reshape(np.broadcast(T, K).shape)

    return vol_of_tk
