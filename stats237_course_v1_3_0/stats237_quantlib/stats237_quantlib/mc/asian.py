from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .core import mc_mean_ci
from .samplers import MCNormalConfig, standard_normals
from .variance_reduction import control_variate_adjust_multi


def geometric_asian_call_closed_form(S0: float, K: float, r: float, T: float, sigma: float, n_obs: int) -> float:
    """Closed form for discretely monitored geometric Asian call (equal spacing).

    The geometric average is lognormal with adjusted drift/variance. We use this
    as a control variate for arithmetic Asian Monte Carlo.
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
    method: str = "plain",
    qmc_scramble: bool = True,
    use_extra_control: bool = True,
) -> dict:
    """Monte Carlo pricing for a discretely monitored arithmetic Asian call.

    Payoff: max( (1/n) sum_{i=1..n} S(t_i) - K, 0 )

    Variance reduction ("pro pack" in v1.2):
      - antithetic variates (default on)
      - sampling method: plain | lhs | sobol | halton
      - multi-control variates (default on):
          * geometric Asian call (closed form expectation)
          * discounted terminal price (expectation = S0)

    Returns:
      dict with baseline stats and, if enabled, CV-adjusted stats + beta + VR factor.
    """
    if n_obs <= 0:
        raise ValueError("n_obs must be > 0")
    if n_paths < 1000:
        raise ValueError("n_paths too small for stable CI")
    if T <= 0:
        raise ValueError("T must be > 0")
    if sigma <= 0:
        raise ValueError("sigma must be > 0")
    if method not in ("plain", "lhs", "sobol", "halton"):
        raise ValueError("method must be one of: plain, lhs, sobol, halton")

    n = int(n_obs)
    dt = float(T) / n
    times = np.arange(1, n + 1, dtype=float) * dt

    # Simulate GBM at observation times via cumulative increments.
    cfg = MCNormalConfig(method=method, antithetic=bool(antithetic), seed=int(seed), qmc_scramble=bool(qmc_scramble))
    Z = standard_normals(n_paths, d=n, cfg=cfg)
    n_eff = int(Z.shape[0])

    increments = (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    logS = np.log(float(S0)) + np.cumsum(increments, axis=1)
    S_path = np.exp(logS)

    A = np.mean(S_path, axis=1)  # arithmetic average
    df = float(np.exp(-r * T))
    payoff = df * np.maximum(A - float(K), 0.0)

    out = {
        "method": method,
        "qmc_scramble": bool(qmc_scramble) if method in ("sobol", "halton") else None,
        "antithetic": bool(antithetic),
        "baseline": mc_mean_ci(payoff, alpha=alpha),
    }

    if not use_control_variate:
        return out

    # Controls:
    # 1) geometric Asian call (discounted) with known expectation (closed form)
    G = np.exp(np.mean(logS, axis=1))
    control1 = df * np.maximum(G - float(K), 0.0)
    mu1 = float(geometric_asian_call_closed_form(S0=float(S0), K=float(K), r=float(r), T=float(T), sigma=float(sigma), n_obs=n))

    controls = [control1]
    mus = [mu1]

    # 2) discounted terminal price (E[df * S_T] = S0) — often a strong, cheap control
    if use_extra_control:
        ST = S_path[:, -1]
        control2 = df * ST
        mu2 = float(S0)  # risk-neutral: E[df*S_T] = S0
        controls.append(control2)
        mus.append(mu2)

    Y = np.vstack(controls).T  # (n_eff, k)
    res = control_variate_adjust_multi(payoff, Y=Y, y_means=np.asarray(mus, dtype=float))
    out["control_variate"] = {
        "controls": ["geom_asian_call", "disc_terminal_S"] if use_extra_control else ["geom_asian_call"],
        "beta": res.beta.tolist(),
        "variance_reduction_factor": res.variance_reduction_factor,
        "adjusted": mc_mean_ci(res.adjusted_samples, alpha=alpha),
    }
    out["control_variate_result"] = out["control_variate"]["adjusted"]
    return out
