from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .core import mc_mean_ci

@dataclass(frozen=True)
class VRDiagnostics:
    label: str
    baseline: dict
    adjusted: dict | None
    beta: list[float] | None
    variance_reduction_factor: float | None


def summarize_vr(
    label: str,
    baseline_samples: np.ndarray,
    adjusted_samples: np.ndarray | None,
    beta: np.ndarray | None,
    alpha: float = 0.05,
) -> VRDiagnostics:
    base = mc_mean_ci(baseline_samples, alpha=alpha)
    if adjusted_samples is None:
        return VRDiagnostics(label=label, baseline=base, adjusted=None, beta=None, variance_reduction_factor=None)

    adj = mc_mean_ci(adjusted_samples, alpha=alpha)
    vrf = float("inf") if adj["sd"] == 0 else float(base["sd"] / adj["sd"])
    b = beta.tolist() if beta is not None else None
    return VRDiagnostics(label=label, baseline=base, adjusted=adj, beta=b, variance_reduction_factor=vrf)
