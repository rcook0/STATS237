from __future__ import annotations

import numpy as np
from scipy.stats import norm

# Numerical stability threshold: when sigma*sqrt(T) is tiny, d1/d2 become ill-conditioned.
_EPS_VSQRT = 1e-10

def _validate_inputs(S0: float, K: float, r: float, T: float, sigma: float) -> tuple[float,float,float,float,float]:
    S0 = float(S0); K = float(K); r = float(r); T = float(T); sigma = float(sigma)
    if S0 <= 0:
        raise ValueError("S0 must be > 0")
    if K <= 0:
        raise ValueError("K must be > 0")
    if T <= 0:
        raise ValueError("T must be > 0")
    if sigma <= 0:
        # For v1.1+ we treat sigma<=0 as invalid; callers can use tiny sigma to approximate.
        raise ValueError("sigma must be > 0")
    return S0, K, r, T, sigma

def _d1_d2(S0: float, K: float, r: float, T: float, sigma: float) -> tuple[float, float, float]:
    S0, K, r, T, sigma = _validate_inputs(S0, K, r, T, sigma)
    vsqrt = sigma * np.sqrt(T)
    if vsqrt < _EPS_VSQRT:
        # Signal to callers: near-deterministic regime.
        return float("nan"), float("nan"), float(vsqrt)
    d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / vsqrt
    d2 = d1 - vsqrt
    return float(d1), float(d2), float(vsqrt)

def bs_call(S0: float, K: float, r: float, T: float, sigma: float) -> float:
    d1, d2, vsqrt = _d1_d2(S0, K, r, T, sigma)
    df = float(np.exp(-r * T))
    if not np.isfinite(d1):
        # Deterministic forward limit: S_T = S0 * exp(rT). Discounted payoff is intrinsic on forward.
        return float(max(S0 - K * df, 0.0))
    return float(S0 * norm.cdf(d1) - K * df * norm.cdf(d2))

def bs_put(S0: float, K: float, r: float, T: float, sigma: float) -> float:
    d1, d2, vsqrt = _d1_d2(S0, K, r, T, sigma)
    df = float(np.exp(-r * T))
    if not np.isfinite(d1):
        return float(max(K * df - S0, 0.0))
    return float(K * df * norm.cdf(-d2) - S0 * norm.cdf(-d1))

def greeks_call_put(S0: float, K: float, r: float, T: float, sigma: float) -> dict:
    d1, d2, vsqrt = _d1_d2(S0, K, r, T, sigma)
    df = float(np.exp(-r * T))

    if not np.isfinite(d1):
        # Near-deterministic regime: vega/gamma -> 0, delta is piecewise.
        call = max(S0 - K * df, 0.0)
        put = max(K * df - S0, 0.0)
        delta_call = 1.0 if call > 0 else 0.0
        delta_put = delta_call - 1.0
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

    call = float(S0 * cdf1 - K * df * cdf2)
    put = float(K * df * norm.cdf(-d2) - S0 * norm.cdf(-d1))

    delta_call = cdf1
    delta_put = cdf1 - 1.0
    gamma = pdf / (S0 * float(sigma) * float(np.sqrt(T)))
    vega = S0 * pdf * float(np.sqrt(T))

    # Standard theta/rho (no dividends)
    theta_call = - (S0 * pdf * sigma) / (2.0 * float(np.sqrt(T))) - r * K * df * cdf2
    theta_put  = - (S0 * pdf * sigma) / (2.0 * float(np.sqrt(T))) + r * K * df * norm.cdf(-d2)

    rho_call = K * T * df * cdf2
    rho_put  = -K * T * df * norm.cdf(-d2)

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
) -> float:
    """Implied volatility via robust bisection.

    This is intentionally boring and stable: no Newton blow-ups.
    """
    price = float(price)
    if price <= 0:
        raise ValueError("price must be > 0")
    S0, K, r, T, _ = _validate_inputs(S0, K, r, T, max(float(vol_low), 1e-12))

    def f(sig: float) -> float:
        return (bs_call(S0, K, r, T, sig) if is_call else bs_put(S0, K, r, T, sig)) - price

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
