from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ControlVariateResult:
    beta: float
    adjusted_samples: np.ndarray


def control_variate_adjust(x: np.ndarray, y: np.ndarray, y_mean: float) -> ControlVariateResult:
    """Apply an (optimal) linear control variate.

    We observe samples (x_i, y_i) where E[y] is known (y_mean). Construct
    x'_i = x_i + beta * (y_mean - y_i) with beta chosen to minimize Var(x').

    beta* = Cov(x, y) / Var(y)

    Args:
        x: target sample values
        y: control sample values
        y_mean: known expected value of y

    Returns:
        ControlVariateResult with beta and adjusted samples.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        raise ValueError("x and y must have same shape")
    if x.size < 2:
        raise ValueError("need at least 2 samples")

    y_var = float(np.var(y, ddof=1))
    if y_var <= 0:
        # Degenerate control: no adjustment.
        beta = 0.0
        adj = x.copy()
        return ControlVariateResult(beta=beta, adjusted_samples=adj)

    cov = float(np.cov(x, y, ddof=1)[0, 1])
    beta = cov / y_var
    adj = x + beta * (float(y_mean) - y)
    return ControlVariateResult(beta=float(beta), adjusted_samples=np.asarray(adj, dtype=float))
