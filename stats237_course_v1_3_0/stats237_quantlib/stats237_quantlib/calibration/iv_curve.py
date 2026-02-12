from __future__ import annotations

"""Implied-vol calibration primitives.

v1.2 shipped *hooks*.
v1.3 upgrades them into a small, research-grade calibration layer:

- implied vols from prices (with dividend yield q)
- smile fitting:
    * linear interpolation (fast)
    * PCHIP (shape-preserving cubic; avoids spline oscillations)
- a simple surface construction:
    * interpolate **total variance** w(T,k)=sigma(T,k)^2 * T
      on log-moneyness k=log(K/F(T))
    * time interpolation is done in total variance for stability
- basic no-arbitrage sanity checks (warnings, not constraints)

The philosophy: stable primitives you can later upgrade into full arbitrage-free
fitting (SABR/SSVI/local vol/etc.) without changing call sites.
"""

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
from scipy.interpolate import interp1d, LinearNDInterpolator, NearestNDInterpolator, PchipInterpolator

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
    """Compute implied vols for a set of strikes."""
    strikes = np.asarray(strikes, dtype=float)
    prices = np.asarray(prices, dtype=float)
    if strikes.shape != prices.shape:
        raise ValueError("strikes and prices must have the same shape")

    vols = np.empty_like(strikes, dtype=float)
    lo, hi = clamp
    for i, (K, p) in enumerate(zip(strikes, prices)):
        v = implied_vol(
            price=float(p),
            S0=float(S0),
            K=float(K),
            r=float(r),
            T=float(T),
            q=float(q),
            is_call=bool(is_call),
        )
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

    Parameters
    ----------
    kind:
      Passed to scipy.interpolate.interp1d (e.g. "linear", "nearest").

    Returns
    -------
    vol_of_k:
      Callable mapping strike(s) -> vols.
    """
    strikes = np.asarray(strikes, dtype=float)
    vols = np.asarray(vols, dtype=float)
    if strikes.shape != vols.shape:
        raise ValueError("strikes and vols must have the same shape")

    order = np.argsort(strikes)
    x = strikes[order]
    y = vols[order]

    f = interp1d(x, y, kind=kind, fill_value=fill, bounds_error=False, assume_sorted=True)

    def vol_of_k(K: np.ndarray) -> np.ndarray:
        return np.asarray(f(np.asarray(K, dtype=float)), dtype=float)

    return vol_of_k


def fit_iv_smile_pchip(
    *,
    strikes: np.ndarray,
    vols: np.ndarray,
    extrapolate: bool = True,
) -> Callable[[np.ndarray], np.ndarray]:
    """Shape-preserving cubic smile fit using PCHIP.

    Compared to generic cubic splines, PCHIP avoids oscillations and tends
    to preserve monotonic segments.
    """
    strikes = np.asarray(strikes, dtype=float)
    vols = np.asarray(vols, dtype=float)
    if strikes.shape != vols.shape:
        raise ValueError("strikes and vols must have the same shape")

    order = np.argsort(strikes)
    x = strikes[order]
    y = vols[order]

    f = PchipInterpolator(x, y, extrapolate=bool(extrapolate))

    def vol_of_k(K: np.ndarray) -> np.ndarray:
        return np.asarray(f(np.asarray(K, dtype=float)), dtype=float)

    return vol_of_k


def iv_surface_linear(
    *,
    points: np.ndarray,
    values: np.ndarray,
    fallback: str = "nearest",
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """Fit a simple IV surface vol(T, K) using linear interpolation."""
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


@dataclass(frozen=True)
class SmileSlice:
    """A single maturity smile slice."""

    T: float
    strikes: np.ndarray
    vols: np.ndarray


def _forward_price(S0: float, r: float, q: float, T: float) -> float:
    return float(S0) * float(np.exp((float(r) - float(q)) * float(T)))


def _log_moneyness(K: np.ndarray, F: float) -> np.ndarray:
    K = np.asarray(K, dtype=float)
    return np.log(K / float(F))


def iv_surface_total_variance(
    *,
    smiles: Iterable[SmileSlice],
    S0: float,
    r: float,
    q: float = 0.0,
    extrapolate: bool = True,
) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    """Build a simple IV surface via total variance interpolation.

    Steps:
      1) For each maturity T, map strikes -> log-moneyness k = log(K/F(T))
      2) Fit a PCHIP interpolator of total variance w(k) = vol(k)^2 * T
      3) For a query (Tq, Kq):
           - compute kq at Tq
           - evaluate w on the nearest bracketing maturities (in k-space)
           - linearly interpolate w in T
           - return vol = sqrt(w / Tq)

    This is not a full arbitrage-free surface, but it's much more stable than
    directly interpolating vol across T.
    """
    slices = []
    for s in smiles:
        T = float(s.T)
        if T <= 0:
            raise ValueError("SmileSlice.T must be > 0")
        strikes = np.asarray(s.strikes, dtype=float)
        vols = np.asarray(s.vols, dtype=float)
        if strikes.shape != vols.shape:
            raise ValueError("SmileSlice strikes and vols must have same shape")
        F = _forward_price(S0, r, q, T)
        k = _log_moneyness(strikes, F)
        w = (vols ** 2) * T
        order = np.argsort(k)
        k = k[order]
        w = w[order]
        f_w = PchipInterpolator(k, w, extrapolate=bool(extrapolate))
        slices.append((T, f_w))

    if len(slices) < 2:
        raise ValueError("Need at least two maturities to build a surface")

    slices.sort(key=lambda x: x[0])
    Ts = np.array([t for t, _ in slices], dtype=float)

    def vol_of_tk(Tq: np.ndarray, Kq: np.ndarray) -> np.ndarray:
        Tq = np.asarray(Tq, dtype=float)
        Kq = np.asarray(Kq, dtype=float)
        out_shape = np.broadcast(Tq, Kq).shape
        T_flat = np.broadcast_to(Tq, out_shape).ravel()
        K_flat = np.broadcast_to(Kq, out_shape).ravel()

        vols_out = np.empty_like(T_flat, dtype=float)
        for i, (t, k_strike) in enumerate(zip(T_flat, K_flat)):
            t = float(t)
            if t <= 0:
                vols_out[i] = np.nan
                continue
            Fq = _forward_price(S0, r, q, t)
            kq = float(np.log(float(k_strike) / Fq))

            # Find bracketing maturities
            if t <= Ts[0]:
                t0, f0 = slices[0]
                wq = float(f0(kq))
            elif t >= Ts[-1]:
                t1, f1 = slices[-1]
                wq = float(f1(kq))
            else:
                j = int(np.searchsorted(Ts, t))
                t_lo, f_lo = slices[j - 1]
                t_hi, f_hi = slices[j]
                w_lo = float(f_lo(kq))
                w_hi = float(f_hi(kq))
                # Linear interpolation in total variance
                lam = (t - t_lo) / (t_hi - t_lo)
                wq = (1.0 - lam) * w_lo + lam * w_hi

            vols_out[i] = float(np.sqrt(max(wq, 0.0) / t))

        return vols_out.reshape(out_shape)

    return vol_of_tk


def sanity_check_call_prices_convex_in_strike(
    strikes: np.ndarray,
    call_prices: np.ndarray,
    atol: float = 1e-10,
) -> dict:
    """Basic static-arbitrage sanity checks for call prices vs strike.

    For fixed maturity, no static arbitrage implies call price is:
      - non-increasing in strike
      - convex in strike

    Returns a dict of boolean flags + worst violations.
    """
    K = np.asarray(strikes, dtype=float)
    C = np.asarray(call_prices, dtype=float)
    if K.shape != C.shape:
        raise ValueError("strikes and call_prices must have same shape")

    order = np.argsort(K)
    K = K[order]
    C = C[order]

    dC = np.diff(C)
    monotone_ok = bool(np.all(dC <= atol))
    worst_monotone = float(np.max(dC)) if dC.size else 0.0

    # Discrete convexity: second differences >= 0 (up to atol)
    ddC = np.diff(C, n=2)
    convex_ok = bool(np.all(ddC >= -atol))
    worst_convex = float(np.min(ddC)) if ddC.size else 0.0

    return {
        "monotone_nonincreasing": monotone_ok,
        "convex": convex_ok,
        "worst_monotone_slope": worst_monotone,
        "worst_convex_second_diff": worst_convex,
    }
