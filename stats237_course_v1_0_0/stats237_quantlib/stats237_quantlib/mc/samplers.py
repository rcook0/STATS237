from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.stats import norm

Method = Literal["plain", "lhs"]


@dataclass(frozen=True)
class MCNormalConfig:
    """Configuration for generating standard normal draws.

    method:
      - "plain": iid N(0,1)
      - "lhs": Latin hypercube sampling (stratified uniforms per-dimension)

    antithetic:
      - If True, generates pairs (Z, -Z). Total sample count will be rounded
        up to the next even number.

    seed:
      - Seed for numpy's Generator.
    """

    method: Method = "plain"
    antithetic: bool = False
    seed: int = 123


def _lhs_standard_normals(n: int, d: int, rng: np.random.Generator) -> np.ndarray:
    """Latin hypercube standard normal draws.

    For each dimension j, we create stratified uniforms u_i in (i/n, (i+1)/n)
    and apply the normal inverse CDF, with a random permutation per dimension.

    This is a basic, effective variance-reduction method for many smooth
    integrands (it is not guaranteed to reduce variance for every payoff).
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    if d <= 0:
        raise ValueError("d must be > 0")

    # base strata locations 0..n-1
    strata = np.arange(n, dtype=float)
    Z = np.empty((n, d), dtype=float)
    for j in range(d):
        u = (strata + rng.random(n)) / n
        rng.shuffle(u)
        Z[:, j] = norm.ppf(u)
    return Z


def standard_normals(n: int, d: int, cfg: MCNormalConfig) -> np.ndarray:
    """Generate N(0,1) draws with optional variance-reduction.

    Returns an array of shape (n_eff, d), where n_eff may differ from n if
    antithetic=True (n_eff is even).
    """
    rng = np.random.default_rng(cfg.seed)

    if cfg.antithetic:
        n_base = (n + 1) // 2
    else:
        n_base = n

    if cfg.method == "plain":
        Z = rng.standard_normal((n_base, d))
    elif cfg.method == "lhs":
        Z = _lhs_standard_normals(n_base, d, rng)
    else:
        raise ValueError(f"Unknown method: {cfg.method}")

    if cfg.antithetic:
        Z = np.vstack([Z, -Z])

    return Z


def correlated_normals(n: int, corr: np.ndarray, cfg: MCNormalConfig) -> np.ndarray:
    """Generate correlated standard normals with correlation matrix corr.

    corr is the correlation matrix of the underlying Gaussian vector.
    Returns array shape (n_eff, d).
    """
    corr = np.asarray(corr, dtype=float)
    if corr.ndim != 2 or corr.shape[0] != corr.shape[1]:
        raise ValueError("corr must be a square matrix")
    d = corr.shape[0]

    # Cholesky requires PSD; we assume well-formed corr.
    L = np.linalg.cholesky(corr)
    Z = standard_normals(n, d, cfg)
    return Z @ L.T
