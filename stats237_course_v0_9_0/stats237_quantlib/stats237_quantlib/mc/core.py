from __future__ import annotations

import numpy as np
from scipy.stats import norm


def mc_mean_ci(samples: np.ndarray, alpha: float = 0.05) -> dict:
    """Mean and two-sided (1-alpha) confidence interval.

    Uses a normal approximation with estimated standard error.
    For typical Monte Carlo sample sizes (>= 1_000), this is standard.

    Returns:
        dict with n, mean, sd, se, ci_low, ci_high
    """
    x = np.asarray(samples, dtype=float)
    n = int(x.size)
    if n < 2:
        raise ValueError("Need at least 2 samples")

    mu = float(np.mean(x))
    sd = float(np.std(x, ddof=1))
    se = sd / float(np.sqrt(n))

    z = float(norm.ppf(1.0 - alpha / 2.0))
    lo = mu - z * se
    hi = mu + z * se

    return {
        "n": n,
        "mean": mu,
        "sd": sd,
        "se": se,
        "alpha": float(alpha),
        "ci_low": float(lo),
        "ci_high": float(hi),
    }
