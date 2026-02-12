from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .core import mc_mean_ci
from .samplers import MCNormalConfig, standard_normals
from .variance_reduction import control_variate_adjust


def geometric_asian_call_closed_form(S0: float, K: float, r: float, T: float, sigma: float, n_obs: int) -> float:
    """Closed form for discretely monitored geometric Asian call (equal spacing).

    Standard result: the geometric average is lognormal with adjusted drift/variance.
    We use this as a control variate for arithmetic Asian Monte Carlo.
    """
    if n_obs <= 0:
        raise ValueError("n_obs must be > 0")

    n = int(n_obs)
    mu = np.log(S0) + (r - 0.5 * sigma**2) * T * (n + 1) / (2 * n)
    var_ln = sigma**2 * T * ((n + 1) * (2 * n + 1) / (6 * n**2))
    sig_ln = np.sqrt(var_ln)

    d1 = (mu - np.log(K) + var_ln) / sig_ln
    d2 = d1 - sig_ln

    # E[(G-K)^+] for lognormal G, discounted
    undiscounted = np.exp(mu + 0.5 * var_ln) * norm.cdf(d1) - K * norm.cdf(d2)
    return float(np.exp(-r * T) * undiscounted)


def arithmetic_asian_call_mc(
    S0: float,
    K: float,
    r: float,
    T: float,
    sigma: float,
    n_obs: int,
    n_paths: int = 20_000,
    seed: int = 123,
    antithetic: bool = True,
    use_control_variate: bool = True,
    alpha: float = 0.05,
) -> dict:
    """Monte Carlo pricing for a discretely monitored arithmetic Asian call.

    Payoff: max( (1/n) sum_{i=1..n} S(t_i) - K, 0 )

    Variance-reduction:
      - antithetic variates on the Gaussian increments (enabled by default)
      - control variate using geometric Asian call closed-form (enabled by default)

    Returns:
      dict with baseline MC stats and, if control variate is on, CV-adjusted stats.
    """
    if n_obs <= 0:
        raise ValueError("n_obs must be > 0")
    if n_paths < 1000:
        raise ValueError("n_paths too small for stable CI")
    if T <= 0:
        raise ValueError("T must be > 0")
    if sigma <= 0:
        raise ValueError("sigma must be > 0")

    n = int(n_obs)
    dt = float(T / n)

    # We simulate Brownian increments: dW ~ sqrt(dt) * Z
    cfg = MCNormalConfig(method="plain", antithetic=bool(antithetic), seed=int(seed))
    Z = standard_normals(n_paths, n, cfg)  # shape (n_eff, n_obs)
    n_eff = Z.shape[0]

    drift = (r - 0.5 * sigma**2) * dt
    incr = drift + sigma * np.sqrt(dt) * Z
    logS = np.log(S0) + np.cumsum(incr, axis=1)
    S = np.exp(logS)

    A = np.mean(S, axis=1)
    payoff_arith = np.maximum(A - K, 0.0)
    disc_arith = np.exp(-r * T) * payoff_arith

    out = {
        "n_paths": int(n_paths),
        "n_eff": int(n_eff),
        "antithetic": bool(antithetic),
        "control_variate": bool(use_control_variate),
        "baseline": mc_mean_ci(disc_arith, alpha=alpha),
    }
    out["baseline"]["price"] = out["baseline"]["mean"]

    if not use_control_variate:
        return out

    # geometric average and its payoff as control
    G = np.exp(np.mean(logS, axis=1))
    payoff_geom = np.maximum(G - K, 0.0)
    disc_geom = np.exp(-r * T) * payoff_geom

    y_mean = geometric_asian_call_closed_form(S0=S0, K=K, r=r, T=T, sigma=sigma, n_obs=n)
    cv = control_variate_adjust(disc_arith, disc_geom, y_mean=y_mean)
    cv_stats = mc_mean_ci(cv.adjusted_samples, alpha=alpha)
    cv_stats["price"] = cv_stats["mean"]
    cv_stats["beta"] = float(cv.beta)
    cv_stats["control_price"] = float(y_mean)

    out["control_variate_result"] = cv_stats
    return out
