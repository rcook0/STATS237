#!/usr/bin/env python3
"""Variance reduction demo for v0.6.

Runs a small set of Monte Carlo estimations and writes a short markdown report
under reports/.

This is intentionally independent of the ingestion pipeline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from stats237_quantlib.mc.asian import arithmetic_asian_call_mc
from stats237_quantlib.mc.basket import basket_call_mc_vr


def fmt_ci(d: dict) -> str:
    return f"{d['mean']:.6f}  (CI: [{d['ci_low']:.6f}, {d['ci_high']:.6f}], sd={d['sd']:.6f}, n={d['n']})"


def main() -> None:
    lines: list[str] = []
    lines.append("# Stats237 v0.6 — Variance Reduction Demo\n")

    # Asian
    res_asian = arithmetic_asian_call_mc(
        S0=100.0,
        K=100.0,
        r=0.03,
        T=1.0,
        sigma=0.2,
        n_obs=50,
        n_paths=20000,
        seed=42,
        antithetic=True,
        use_control_variate=True,
    )
    lines.append("## Arithmetic Asian call (MC)\n")
    lines.append("Baseline:")
    lines.append(f"- {fmt_ci(res_asian['baseline'])}")
    cv = res_asian["control_variate_result"]
    lines.append("Control variate (geometric Asian closed form):")
    lines.append(f"- {fmt_ci(cv)}")
    lines.append(f"- beta={cv['beta']:.6f}, control_price={cv['control_price']:.6f}\n")

    # Basket
    S0 = np.array([100.0, 95.0, 105.0])
    w = np.array([0.5, 0.3, 0.2])
    vol = np.array([0.2, 0.25, 0.18])
    corr = np.array(
        [
            [1.0, 0.4, 0.3],
            [0.4, 1.0, 0.2],
            [0.3, 0.2, 1.0],
        ]
    )
    res_b = basket_call_mc_vr(
        S0=S0,
        w=w,
        K=100.0,
        r=0.02,
        T=1.0,
        vol=vol,
        corr=corr,
        n_paths=20000,
        seed=7,
        antithetic=True,
        lhs=False,
        use_control_variate=True,
    )

    lines.append("## Basket call (MC)\n")
    lines.append("Baseline:")
    lines.append(f"- {fmt_ci(res_b['baseline'])}")
    cvb = res_b["control_variate_result"]
    lines.append("Control variate (geometric basket closed form):")
    lines.append(f"- {fmt_ci(cvb)}")
    lines.append(f"- beta={cvb['beta']:.6f}, control_price={cvb['control_price']:.6f}\n")

    out = Path("reports") / "vr_demo.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
