from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
from scipy.stats import norm, qmc

Method = Literal["plain", "lhs", "sobol", "halton"]

@dataclass(frozen=True)
class MCNormalConfig:
    """Configuration for generating standard normal draws.

    method:
      - "plain": iid N(0,1)
      - "lhs": Latin hypercube sampling (stratified uniforms per-dimension)
      - "sobol": low-discrepancy Sobol sequence (optionally Owen-scrambled)
      - "halton": low-discrepancy Halton sequence (optionally scrambled)

    antithetic:
      - If True, generates pairs (Z, -Z) (for normal-based methods) or
        (u, 1-u) for uniform-based methods before inverse-CDF.

    seed:
      - Seed for deterministic generation when rng is not provided.

    qmc_scramble:
      - If True and method is Sobol/Halton, uses SciPy's scrambling for better
        practical performance while staying reproducible under a fixed seed.

    rng:
      - Optional numpy Generator. If provided, seed is ignored for "plain"/"lhs".
        For QMC methods, SciPy uses its own seed for scrambling; rng is not used.
    """
    method: Method = "plain"
    antithetic: bool = False
    seed: int = 123
    qmc_scramble: bool = True
    rng: Optional[np.random.Generator] = None


def _clip_u(u: np.ndarray) -> np.ndarray:
    # avoid infinities in ppf
    eps = 1e-12
    return np.clip(u, eps, 1.0 - eps)


def _lhs_uniforms(n: int, d: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0:
        raise ValueError("n must be > 0")
    if d <= 0:
        raise ValueError("d must be > 0")
    strata = np.arange(n, dtype=float)
    U = np.empty((n, d), dtype=float)
    for j in range(d):
        u = (strata + rng.random(n)) / n
        rng.shuffle(u)
        U[:, j] = u
    return U


def _qmc_uniforms(n: int, d: int, method: Method, scramble: bool, seed: int) -> np.ndarray:
    if method == "sobol":
        engine = qmc.Sobol(d=d, scramble=bool(scramble), seed=int(seed))
        return engine.random(n)
    if method == "halton":
        engine = qmc.Halton(d=d, scramble=bool(scramble), seed=int(seed))
        return engine.random(n)
    raise ValueError(f"Not a QMC method: {method}")


def standard_normals(n: int, d: int, cfg: MCNormalConfig) -> np.ndarray:
    """Generate N(0,1) draws with optional variance-reduction.

    Returns an array of shape (n_eff, d), where n_eff may differ from n if
    antithetic=True (n_eff is even).
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    if d <= 0:
        raise ValueError("d must be > 0")

    rng = cfg.rng if cfg.rng is not None else np.random.default_rng(int(cfg.seed))

    # base sample count if antithetic
    n_base = (n + 1) // 2 if cfg.antithetic else n

    if cfg.method == "plain":
        Z = rng.standard_normal((n_base, d))
        if cfg.antithetic:
            Z = np.vstack([Z, -Z])
        return Z

    if cfg.method == "lhs":
        U = _lhs_uniforms(n_base, d, rng)
        if cfg.antithetic:
            U = np.vstack([U, 1.0 - U])
        Z = norm.ppf(_clip_u(U))
        return Z

    if cfg.method in ("sobol", "halton"):
        U = _qmc_uniforms(n_base, d, cfg.method, cfg.qmc_scramble, cfg.seed)
        if cfg.antithetic:
            U = np.vstack([U, 1.0 - U])
        Z = norm.ppf(_clip_u(U))
        return Z

    raise ValueError(f"Unknown method: {cfg.method}")


def correlated_normals(n: int, corr: np.ndarray, cfg: MCNormalConfig) -> np.ndarray:
    """Generate correlated standard normals with correlation matrix corr."""
    corr = np.asarray(corr, dtype=float)
    if corr.ndim != 2 or corr.shape[0] != corr.shape[1]:
        raise ValueError("corr must be a square matrix")

    d = int(corr.shape[0])
    Z = standard_normals(n=n, d=d, cfg=cfg)
    L = np.linalg.cholesky(corr)
    return Z @ L.T
