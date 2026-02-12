from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.stats import norm

def _d1_d2(S0: float, K: float, r: float, T: float, sigma: float) -> tuple[float,float]:
    if T <= 0:
        raise ValueError("T must be > 0")
    if sigma <= 0:
        raise ValueError("sigma must be > 0")
    vsqrt = sigma * np.sqrt(T)
    d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / vsqrt
    d2 = d1 - vsqrt
    return float(d1), float(d2)

def bs_call(S0: float, K: float, r: float, T: float, sigma: float) -> float:
    d1, d2 = _d1_d2(S0, K, r, T, sigma)
    df = float(np.exp(-r * T))
    return float(S0 * norm.cdf(d1) - K * df * norm.cdf(d2))

def bs_put(S0: float, K: float, r: float, T: float, sigma: float) -> float:
    d1, d2 = _d1_d2(S0, K, r, T, sigma)
    df = float(np.exp(-r * T))
    return float(K * df * norm.cdf(-d2) - S0 * norm.cdf(-d1))

def greeks_call_put(S0: float, K: float, r: float, T: float, sigma: float) -> dict:
    d1, d2 = _d1_d2(S0, K, r, T, sigma)
    df = float(np.exp(-r * T))
    pdf = float(norm.pdf(d1))
    cdf1 = float(norm.cdf(d1))
    cdf2 = float(norm.cdf(d2))

    delta_call = cdf1
    delta_put = cdf1 - 1.0
    gamma = pdf / (S0 * sigma * np.sqrt(T))
    vega = S0 * pdf * np.sqrt(T)
    theta_call = -(S0 * pdf * sigma) / (2*np.sqrt(T)) - r * K * df * cdf2
    theta_put = -(S0 * pdf * sigma) / (2*np.sqrt(T)) + r * K * df * float(norm.cdf(-d2))
    rho_call = K * T * df * cdf2
    rho_put = -K * T * df * float(norm.cdf(-d2))

    return {
        "d1": d1, "d2": d2,
        "delta_call": float(delta_call),
        "delta_put": float(delta_put),
        "gamma": float(gamma),
        "vega": float(vega),
        "theta_call": float(theta_call),
        "theta_put": float(theta_put),
        "rho_call": float(rho_call),
        "rho_put": float(rho_put),
    }

def implied_vol(price: float, is_call: bool, S0: float, K: float, r: float, T: float,
                vol_low: float = 1e-6, vol_high: float = 5.0, tol: float = 1e-10, max_iter: int = 200) -> float:
    """
    Robust implied vol solver using bisection (monotone in sigma for vanilla options).
    """
    if price <= 0:
        raise ValueError("price must be > 0")
    f = (lambda sig: bs_call(S0, K, r, T, sig)) if is_call else (lambda sig: bs_put(S0, K, r, T, sig))
    lo, hi = vol_low, vol_high
    flo, fhi = f(lo), f(hi)
    if not (flo <= price <= fhi):
        # widen range once
        hi2 = vol_high * 2
        fhi2 = f(hi2)
        if flo <= price <= fhi2:
            hi, fhi = hi2, fhi2
        else:
            raise ValueError("price outside bracket for implied vol")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = f(mid)
        if abs(fmid - price) <= tol:
            return float(mid)
        if fmid < price:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))
