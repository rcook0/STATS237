from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .core import mc_mean_ci
from .samplers import MCNormalConfig, correlated_normals
from .variance_reduction import control_variate_adjust_multi


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
    alpha: float = 0.05,
) -> dict:
    """Plain Monte Carlo price of a basket call: max(w^T S_T - K, 0)."""
    S0 = np.asarray(S0, dtype=float)
    w = np.asarray(w, dtype=float)
    vol = np.asarray(vol, dtype=float)
    corr = np.asarray(corr, dtype=float)

    d = int(S0.size)
    if w.size != d or vol.size != d or corr.shape != (d, d):
        raise ValueError("Dimension mismatch")
    if n_paths < 1000:
        raise ValueError("n_paths too small for stable CI")
    if T <= 0:
        raise ValueError("T must be > 0")

    rng = np.random.default_rng(int(seed))
    L = np.linalg.cholesky(corr)
    Z = rng.standard_normal((int(n_paths), d)) @ L.T

    drift = (r - 0.5 * vol**2) * T
    diff = vol * np.sqrt(T) * Z
    ST = S0 * np.exp(drift + diff)

    basket = ST @ w
    df = float(np.exp(-r * T))
    payoff = df * np.maximum(basket - float(K), 0.0)
    return {"method": "plain", "baseline": mc_mean_ci(payoff, alpha=alpha)}


def _lognormal_call_undiscounted(mean_log: float, var_log: float, K: float) -> float:
    """E[(X-K)^+] where log X ~ N(mean_log, var_log)."""
    sig = float(np.sqrt(var_log))
    if sig <= 0:
        return float(max(np.exp(mean_log) - K, 0.0))
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
    """Closed form for a geometric basket call under correlated GBM.

    If G = prod_i S_T,i^{w_i} (with sum w_i = 1), then log G is normal.
    """
    S0 = np.asarray(S0, dtype=float)
    w = np.asarray(w, dtype=float)
    vol = np.asarray(vol, dtype=float)
    corr = np.asarray(corr, dtype=float)
    d = int(S0.size)
    if w.size != d or vol.size != d or corr.shape != (d, d):
        raise ValueError("Dimension mismatch")
    if not np.isclose(float(np.sum(w)), 1.0):
        # For general weights, treat as exponents but keep formula; users can normalize weights if needed.
        pass

    mean_log_G = float(np.sum(w * np.log(S0)) + (r - 0.5 * float(np.sum((w * vol)**2))) * T)
    # variance of log G: w^T (diag(vol) corr diag(vol)) w * T
    Sigma = np.outer(vol, vol) * corr
    var_log_G = float((w @ Sigma @ w) * T)

    undiscounted = _lognormal_call_undiscounted(mean_log_G, var_log_G, float(K))
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
    method: str = "plain",
    qmc_scramble: bool = True,
    use_extra_control: bool = True,
) -> dict:
    """Basket call Monte Carlo with variance reduction (v1.2 pro pack).

    Sampling method:
      - method: plain | lhs | sobol | halton
      - lhs flag is kept for back-compat; if lhs=True, method is forced to "lhs".

    Controls (multi-control):
      - geometric basket call (closed form expectation)
      - discounted linear basket (expectation = df * E[w^T S_T])

    Returns:
      dict containing baseline stats and, if enabled, CV-adjusted stats + beta + VR factor.
    """
    if lhs:
        method = "lhs"
    if method not in ("plain", "lhs", "sobol", "halton"):
        raise ValueError("method must be one of: plain, lhs, sobol, halton")

    S0 = np.asarray(S0, dtype=float)
    w = np.asarray(w, dtype=float)
    vol = np.asarray(vol, dtype=float)
    corr = np.asarray(corr, dtype=float)

    d = int(S0.size)
    if w.size != d or vol.size != d or corr.shape != (d, d):
        raise ValueError("Dimension mismatch")
    if n_paths < 1000:
        raise ValueError("n_paths too small for stable CI")
    if T <= 0:
        raise ValueError("T must be > 0")

    cfg = MCNormalConfig(method=method, antithetic=bool(antithetic), seed=int(seed), qmc_scramble=bool(qmc_scramble))
    Z = correlated_normals(n_paths, corr=corr, cfg=cfg)

    drift = (r - 0.5 * vol**2) * T
    diff = vol * np.sqrt(T) * Z
    ST = S0 * np.exp(drift + diff)

    basket = ST @ w
    df = float(np.exp(-r * T))
    payoff = df * np.maximum(basket - float(K), 0.0)

    out = {
        "method": method,
        "qmc_scramble": bool(qmc_scramble) if method in ("sobol", "halton") else None,
        "antithetic": bool(antithetic),
        "baseline": mc_mean_ci(payoff, alpha=alpha),
    }

    if not use_control_variate:
        return out

    # Control 1: discounted geometric basket call
    # Compute simulated geometric basket G = exp(sum w_i log S_T,i)
    G = np.exp(np.sum(w * np.log(ST), axis=1))
    control1 = df * np.maximum(G - float(K), 0.0)
    mu1 = float(geometric_basket_call_closed_form(S0=S0, w=w, K=float(K), r=float(r), T=float(T), vol=vol, corr=corr))

    controls = [control1]
    mus = [mu1]

    # Control 2: discounted linear basket (known expectation)
    if use_extra_control:
        control2 = df * basket
        mu2 = float(df * (w @ S0) * np.exp(r * T))
        controls.append(control2)
        mus.append(mu2)

    Y = np.vstack(controls).T
    res = control_variate_adjust_multi(payoff, Y=Y, y_means=np.asarray(mus, dtype=float))
    out["control_variate"] = {
        "controls": ["geom_basket_call", "disc_linear_basket"] if use_extra_control else ["geom_basket_call"],
        "beta": res.beta.tolist(),
        "variance_reduction_factor": res.variance_reduction_factor,
        "adjusted": mc_mean_ci(res.adjusted_samples, alpha=alpha),
    }
    out["control_variate_result"] = out["control_variate"]["adjusted"]
    return out
