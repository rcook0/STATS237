from __future__ import annotations

import os
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

from stats237_quantlib.mc.asian import arithmetic_asian_call_mc
from stats237_quantlib.mc.basket import basket_call_mc_vr

OUT_DIR = Path("reports/vr_pro")
FIG_DIR = OUT_DIR / "figures"

def _ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

def _convergence_series(estimates):
    ns = [e["n"] for e in estimates]
    mus = [e["mean"] for e in estimates]
    lo = [e["ci_low"] for e in estimates]
    hi = [e["ci_high"] for e in estimates]
    return np.array(ns), np.array(mus), np.array(lo), np.array(hi)

def _plot_convergence(title: str, estimates: list[dict], path: Path):
    ns, mus, lo, hi = _convergence_series(estimates)
    plt.figure()
    plt.plot(ns, mus)
    plt.fill_between(ns, lo, hi, alpha=0.2)
    plt.xlabel("n_paths")
    plt.ylabel("estimate")
    plt.title(title)
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()

def run():
    _ensure_dirs()

    # Scenarios
    asian_params = dict(S0=100, K=100, r=0.01, T=1.0, sigma=0.2, n_obs=12, seed=123, alpha=0.05)
    basket_params = dict(
        S0=np.array([100.0, 100.0, 100.0]),
        w=np.array([1/3, 1/3, 1/3]),
        K=100.0,
        r=0.01,
        T=1.0,
        vol=np.array([0.2, 0.25, 0.3]),
        corr=np.array([[1.0, 0.2, 0.1],[0.2, 1.0, 0.3],[0.1, 0.3, 1.0]]),
        seed=5,
        alpha=0.05,
    )

    methods = [
        ("plain", dict(method="plain", antithetic=False, use_control_variate=False)),
        ("antithetic", dict(method="plain", antithetic=True, use_control_variate=False)),
        ("lhs+cv", dict(method="lhs", antithetic=True, use_control_variate=True)),
        ("sobol+cv", dict(method="sobol", antithetic=False, use_control_variate=True)),
    ]

    # Convergence grids
    grid = [1000, 2000, 4000, 8000, 16000]

    report = {"asian": {}, "basket": {}}

    # Asian
    for label, cfg in methods:
        series = []
        for n in grid:
            res = arithmetic_asian_call_mc(**asian_params, n_paths=int(n), **cfg)
            series.append(res["control_variate"]["adjusted"] if cfg.get("use_control_variate") else res["baseline"])
        report["asian"][label] = series
        _plot_convergence(f"Asian arithmetic call — {label}", series, FIG_DIR / f"asian_{label}.png")

    # Basket
    for label, cfg in methods:
        series = []
        for n in grid:
            res = basket_call_mc_vr(**basket_params, n_paths=int(n), **cfg)
            series.append(res["control_variate"]["adjusted"] if cfg.get("use_control_variate") else res["baseline"])
        report["basket"][label] = series
        _plot_convergence(f"Basket call — {label}", series, FIG_DIR / f"basket_{label}.png")

    (OUT_DIR / "vr_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Markdown summary
    md = []
    md.append("# Variance Reduction Pro Pack Report (v1.2)\n")
    md.append("This report compares estimator stability across methods and sample sizes.\n")
    md.append("## Figures\n")
    for label, _ in methods:
        md.append(f"### Asian — {label}\n")
        md.append(f"![](figures/asian_{label}.png)\n")
    for label, _ in methods:
        md.append(f"### Basket — {label}\n")
        md.append(f"![](figures/basket_{label}.png)\n")
    (OUT_DIR / "vr_report.md").write_text("\n".join(md), encoding="utf-8")

if __name__ == "__main__":
    run()
