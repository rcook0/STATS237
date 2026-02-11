from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .core import mc_mean_ci
from .samplers import MCNormalConfig, correlated_normals
from .variance_reduction import control_variate_adjust


def basket_call_mc(
    S0: np.ndarray,
    w: np.ndarray,
    K: float,
    r: float,
    T: float,
    vol: np.ndarray,
    corr: np.ndarray,
    n_paths: int = 20_000,
    seed: int = 123,
) -> dict:
    """Plain Monte Carlo price of a basket call: max(w^T S_T - K, 0).

    Under correlated GBM with constant vols.
    """
    S0 = np.asarray(S0, dtype=float)
    w = np.asarray(w, dtype=float)
    vol = np.asarray(vol, dtype=float)
    corr = np.asarray(corr, dtype=float)

    d = S0.size
    if w.size != d or vol.size != d or corr.shape != (d, d):
        raise ValueError("Dimension mismatch")
    if n_paths < 1000:
        raise ValueError("n_paths too small for stable CI")

    rng = np.random.default_rng(int(seed))
    L = np.linalg.cholesky(corr)
    Z = rng.standard_normal((n_paths, d)) @ L.T

    drift = (r - 0.5 * vol**2) * T
    diff = vol * np.sqrt(T) * Z
    ST = S0 * np.exp(drift + diff)

    basket = ST @ w
    payoff = np.maximum(basket - K, 0.0)
    disc = np.exp(-r * T) * payoff

    ci = mc_mean_ci(disc)
    ci["price"] = ci["mean"]
    return ci


def _lognormal_call_undiscounted(mean_log: float, var_log: float, K: float) -> float:
    """E[(exp(X) - K)^+] where X ~ N(mean_log, var_log)."""
    if var_log <= 0:
        # Degenerate: exp(X)=const
        s = float(np.exp(mean_log))
        return float(max(s - K, 0.0))
    sig = float(np.sqrt(var_log))
    d1 = (mean_log - np.log(K) + var_log) / sig
    d2 = d1 - sig
    return float(np.exp(mean_log + 0.5 * var_log) * norm.cdf(d1) - K * norm.cdf(d2))


def geometric_basket_call_closed_form(
    S0: np.ndarray,
    w: np.ndarray,
    K: float,
    r: float,
    T: float,
    vol: np.ndarray,
    corr: np.ndarray,
) -> float:
    """Closed form price for a *geometric* basket call used as a control variate.

    We build a lognormal proxy:
      G_T = sumW * exp( sum_i a_i log S_i(T) ), where a_i = w_i / sumW.

    Then price = exp(-rT) * E[(G_T - K)^+], with a lognormal closed form.

    Notes:
      - Requires positive weights with sumW>0.
      - This is a control variate for the arithmetic basket call.
    """
    S0 = np.asarray(S0, dtype=float)
    w = np.asarray(w, dtype=float)
    vol = np.asarray(vol, dtype=float)
    corr = np.asarray(corr, dtype=float)

    d = S0.size
    if w.size != d or vol.size != d or corr.shape != (d, d):
        raise ValueError("Dimension mismatch")

    sumW = float(np.sum(w))
    if sumW <= 0:
        raise ValueError("sum(w) must be > 0")
    if np.any(w < 0):
        raise ValueError("geometric control variate assumes non-negative weights")

    a = w / sumW

    # X_i = log S_i(T) = log S0_i + (r - 0.5 vol_i^2)T + vol_i sqrt(T) Z_i
    mean_log_S = np.log(S0) + (r - 0.5 * vol**2) * T

    # mean of log G_T
    mean_log_G = np.log(sumW) + float(a @ mean_log_S)

    # Var of sum a_i vol_i Z_i is a^T (vol_i vol_j corr_ij) a
    C = np.outer(vol, vol) * corr
    var_log_G = float(T * (a @ C @ a))

    undiscounted = _lognormal_call_undiscounted(mean_log_G, var_log_G, K)
    return float(np.exp(-r * T) * undiscounted)


def basket_call_mc_vr(
    S0: np.ndarray,
    w: np.ndarray,
    K: float,
    r: float,
    T: float,
    vol: np.ndarray,
    corr: np.ndarray,
    n_paths: int = 20_000,
    seed: int = 123,
    antithetic: bool = True,
    lhs: bool = False,
    use_control_variate: bool = True,
    alpha: float = 0.05,
) -> dict:
    """Basket call Monte Carlo with variance reduction.

    Variance-reduction options:
      - antithetic variates (default on)
      - Latin hypercube sampling (optional)
      - control variate: geometric basket call closed form (default on)

    Returns:
      dict containing baseline stats and, if enabled, CV-adjusted stats.
    """
    S0 = np.asarray(S0, dtype=float)
    w = np.asarray(w, dtype=float)
    vol = np.asarray(vol, dtype=float)
    corr = np.asarray(corr, dtype=float)

    d = S0.size
    if w.size != d or vol.size != d or corr.shape != (d, d):
        raise ValueError("Dimension mismatch")
    if n_paths < 1000:
        raise ValueError("n_paths too small for stable CI")

    cfg = MCNormalConfig(method=("lhs" if lhs else "plain"), antithetic=bool(antithetic), seed=int(seed))
    Z = correlated_normals(n_paths, corr=corr, cfg=cfg)
    n_eff = Z.shape[0]

    drift = (r - 0.5 * vol**2) * T
    diff = vol * np.sqrt(T) * Z
    ST = S0 * np.exp(drift + diff)

    arith_basket = ST @ w
    payoff_arith = np.maximum(arith_basket - K, 0.0)
    disc_arith = np.exp(-r * T) * payoff_arith

    out = {
        "n_paths": int(n_paths),
        "n_eff": int(n_eff),
        "antithetic": bool(antithetic),
        "lhs": bool(lhs),
        "control_variate": bool(use_control_variate),
        "baseline": mc_mean_ci(disc_arith, alpha=alpha),
    }
    out["baseline"]["price"] = out["baseline"]["mean"]

    if not use_control_variate:
        return out

    # Control variate: geometric basket payoff
    sumW = float(np.sum(w))
    if sumW <= 0:
        raise ValueError("sum(w) must be > 0")
    if np.any(w < 0):
        raise ValueError("control variate assumes non-negative weights")

    a = w / sumW
    geo_basket = sumW * np.exp(np.sum(a * np.log(ST), axis=1))
    payoff_geo = np.maximum(geo_basket - K, 0.0)
    disc_geo = np.exp(-r * T) * payoff_geo

    y_mean = geometric_basket_call_closed_form(S0=S0, w=w, K=K, r=r, T=T, vol=vol, corr=corr)
    cv = control_variate_adjust(disc_arith, disc_geo, y_mean=y_mean)

    cv_stats = mc_mean_ci(cv.adjusted_samples, alpha=alpha)
    cv_stats["price"] = cv_stats["mean"]
    cv_stats["beta"] = float(cv.beta)
    cv_stats["control_price"] = float(y_mean)
    out["control_variate_result"] = cv_stats

    return out
