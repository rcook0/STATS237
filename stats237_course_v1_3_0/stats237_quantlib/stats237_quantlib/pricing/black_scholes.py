from __future__ import annotations

import numpy as np
from scipy.stats import norm

# Numerical stability threshold: when sigma*sqrt(T) is tiny, d1/d2 become ill-conditioned.
_EPS_VSQRT = 1e-10


def _validate_inputs(
    S0: float,
    K: float,
    r: float,
    T: float,
    sigma: float,
    q: float = 0.0,
) -> tuple[float, float, float, float, float, float]:
    S0 = float(S0)
    K = float(K)
    r = float(r)
    T = float(T)
    sigma = float(sigma)
    q = float(q)
    if S0 <= 0:
        raise ValueError("S0 must be > 0")
    if K <= 0:
        raise ValueError("K must be > 0")
    if T <= 0:
        raise ValueError("T must be > 0")
    if sigma <= 0:
        # For v1.1+ we treat sigma<=0 as invalid; callers can use tiny sigma to approximate.
        raise ValueError("sigma must be > 0")
    return S0, K, r, T, sigma, q


def _d1_d2(
    S0: float,
    K: float,
    r: float,
    T: float,
    sigma: float,
    q: float = 0.0,
) -> tuple[float, float, float]:
    """Return (d1, d2, vsqrt).

    If vsqrt is extremely small, returns (nan, nan, vsqrt) as a signal to callers.
    """
    S0, K, r, T, sigma, q = _validate_inputs(S0, K, r, T, sigma, q)
    vsqrt = sigma * np.sqrt(T)
    if vsqrt < _EPS_VSQRT:
        return float("nan"), float("nan"), float(vsqrt)
    d1 = (np.log(S0 / K) + (r - q + 0.5 * sigma**2) * T) / vsqrt
    d2 = d1 - vsqrt
    return float(d1), float(d2), float(vsqrt)


def bs_call(S0: float, K: float, r: float, T: float, sigma: float, q: float = 0.0) -> float:
    d1, d2, _ = _d1_d2(S0, K, r, T, sigma, q)
    df = float(np.exp(-r * T))
    dq = float(np.exp(-q * T))
    if not np.isfinite(d1):
        # Deterministic forward limit (q-adjusted): discounted payoff is intrinsic on forward.
        return float(max(S0 * dq - K * df, 0.0))
    return float(S0 * dq * norm.cdf(d1) - K * df * norm.cdf(d2))


def bs_put(S0: float, K: float, r: float, T: float, sigma: float, q: float = 0.0) -> float:
    d1, d2, _ = _d1_d2(S0, K, r, T, sigma, q)
    df = float(np.exp(-r * T))
    dq = float(np.exp(-q * T))
    if not np.isfinite(d1):
        return float(max(K * df - S0 * dq, 0.0))
    return float(K * df * norm.cdf(-d2) - S0 * dq * norm.cdf(-d1))


def greeks_call_put(S0: float, K: float, r: float, T: float, sigma: float, q: float = 0.0) -> dict:
    d1, d2, _ = _d1_d2(S0, K, r, T, sigma, q)
    df = float(np.exp(-r * T))
    dq = float(np.exp(-q * T))

    if not np.isfinite(d1):
        # Near-deterministic regime: vega/gamma -> 0, delta is piecewise (q-adjusted).
        call = max(S0 * dq - K * df, 0.0)
        put = max(K * df - S0 * dq, 0.0)
        delta_call = dq if call > 0 else 0.0
        delta_put = delta_call - dq
        return {
            "call": float(call),
            "put": float(put),
            "delta_call": float(delta_call),
            "delta_put": float(delta_put),
            "gamma": 0.0,
            "vega": 0.0,
            "theta_call": float("nan"),
            "theta_put": float("nan"),
            "rho_call": float("nan"),
            "rho_put": float("nan"),
            "note": "sigma*sqrt(T) extremely small; returned stable limiting values; higher-order Greeks undefined/ill-conditioned.",
        }

    pdf = float(norm.pdf(d1))
    cdf1 = float(norm.cdf(d1))
    cdf2 = float(norm.cdf(d2))

    call = float(S0 * dq * cdf1 - K * df * cdf2)
    put = float(K * df * norm.cdf(-d2) - S0 * dq * norm.cdf(-d1))

    delta_call = dq * cdf1
    delta_put = dq * (cdf1 - 1.0)
    gamma = dq * pdf / (S0 * float(sigma) * float(np.sqrt(T)))
    vega = S0 * dq * pdf * float(np.sqrt(T))

    # Theta/rho with continuous dividend yield q.
    theta_call = - (S0 * dq * pdf * sigma) / (2.0 * float(np.sqrt(T))) + q * S0 * dq * cdf1 - r * K * df * cdf2
    theta_put = - (S0 * dq * pdf * sigma) / (2.0 * float(np.sqrt(T))) - q * S0 * dq * norm.cdf(-d1) + r * K * df * norm.cdf(-d2)

    rho_call = K * T * df * cdf2
    rho_put = -K * T * df * norm.cdf(-d2)

    return {
        "call": float(call),
        "put": float(put),
        "delta_call": float(delta_call),
        "delta_put": float(delta_put),
        "gamma": float(gamma),
        "vega": float(vega),
        "theta_call": float(theta_call),
        "theta_put": float(theta_put),
        "rho_call": float(rho_call),
        "rho_put": float(rho_put),
    }


def implied_vol(
    price: float,
    is_call: bool,
    S0: float,
    K: float,
    r: float,
    T: float,
    vol_low: float = 1e-6,
    vol_high: float = 5.0,
    tol: float = 1e-10,
    max_iter: int = 200,
    q: float = 0.0,
) -> float:
    """Implied volatility via robust bisection.

    Intentionally boring and stable: no Newton blow-ups.
    """
    price = float(price)
    if price <= 0:
        raise ValueError("price must be > 0")
    S0, K, r, T, _, q = _validate_inputs(S0, K, r, T, max(float(vol_low), 1e-12), q)

    def f(sig: float) -> float:
        return (bs_call(S0, K, r, T, sig, q=q) if is_call else bs_put(S0, K, r, T, sig, q=q)) - price

    lo = max(float(vol_low), 1e-12)
    hi = max(float(vol_high), lo * 1.01)

    flo = f(lo)
    fhi = f(hi)

    # Expand hi if needed to bracket (up to a sensible ceiling)
    expand = 0
    while flo * fhi > 0 and hi < 50.0 and expand < 30:
        hi *= 1.5
        fhi = f(hi)
        expand += 1

    if flo * fhi > 0:
        raise ValueError("Could not bracket implied vol: check price vs bounds")

    for _ in range(int(max_iter)):
        mid = 0.5 * (lo + hi)
        fmid = f(mid)
        if abs(fmid) < tol or (hi - lo) < tol:
            return float(mid)
        if flo * fmid <= 0:
            hi = mid
            fhi = fmid
        else:
            lo = mid
            flo = fmid

    return float(0.5 * (lo + hi))
