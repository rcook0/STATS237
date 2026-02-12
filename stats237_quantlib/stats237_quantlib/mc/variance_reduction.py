from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class ControlVariateResult:
    beta: np.ndarray
    adjusted_samples: np.ndarray
    baseline_sd: float
    adjusted_sd: float
    variance_reduction_factor: float


def control_variate_adjust(x: np.ndarray, y: np.ndarray, y_mean: float) -> ControlVariateResult:
    """Back-compat single-control wrapper."""
    res = control_variate_adjust_multi(x=x, Y=np.asarray(y, dtype=float).reshape(-1, 1), y_means=np.asarray([y_mean], dtype=float))
    return res


def control_variate_adjust_multi(
    x: np.ndarray,
    Y: np.ndarray,
    y_means: np.ndarray,
    ridge: float = 1e-12,
) -> ControlVariateResult:
    """Apply optimal linear control variates (multi-control).

    We observe target samples x (n,) and controls Y (n, k) with known expectations y_means (k,).
    Construct:
        x' = x + (y_means - Y) @ beta
    where beta solves the least-variance problem:
        beta* = argmin Var(x + (y_means - Y) @ beta)

    Closed form:
        beta* = Var(Y)^{-1} Cov(Y, x)

    ridge:
      small diagonal regularization for numerical stability when controls are collinear.
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    Y = np.asarray(Y, dtype=float)
    y_means = np.asarray(y_means, dtype=float).reshape(-1)

    if Y.ndim != 2:
        raise ValueError("Y must be 2D (n, k)")
    n = int(x.size)
    if n != int(Y.shape[0]):
        raise ValueError("x and Y must have same number of rows")
    k = int(Y.shape[1])
    if k != int(y_means.size):
        raise ValueError("y_means must have length k")
    if n < 2:
        raise ValueError("need at least 2 samples")

    baseline_sd = float(np.std(x, ddof=1))

    # Centered
    Yc = Y - np.mean(Y, axis=0, keepdims=True)
    xc = x - float(np.mean(x))

    # Cov(Y) and Cov(Y, x)
    covYY = (Yc.T @ Yc) / float(n - 1)
    covYx = (Yc.T @ xc) / float(n - 1)

    covYY = covYY + float(ridge) * np.eye(k)

    try:
        beta = np.linalg.solve(covYY, covYx)
    except np.linalg.LinAlgError:
        beta = np.zeros(k, dtype=float)

    adj = x + (y_means - Y) @ beta

    adjusted_sd = float(np.std(adj, ddof=1))
    vrf = float("inf") if adjusted_sd == 0 else float(baseline_sd / adjusted_sd)

    return ControlVariateResult(
        beta=np.asarray(beta, dtype=float),
        adjusted_samples=np.asarray(adj, dtype=float),
        baseline_sd=baseline_sd,
        adjusted_sd=adjusted_sd,
        variance_reduction_factor=vrf,
    )
