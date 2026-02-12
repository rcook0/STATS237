#!/usr/bin/env python3
"""Golden runs (Step 4).

Golden runs are small deterministic reference computations that guard against
silent regressions.

Two modes:

1) Generate/update expected values:

   python scripts/golden.py generate

2) Verify against committed expected values:

   python scripts/golden.py verify

Expected values are stored in `golden/expected.json`.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import numpy as np

# Allow running from the repo without `pip install -e stats237_quantlib`
ROOT_IMPORT = Path(__file__).resolve().parents[1] / "stats237_quantlib"
if str(ROOT_IMPORT) not in sys.path:
    sys.path.insert(0, str(ROOT_IMPORT))

from stats237_quantlib.public_api import (
    CRRParams,
    arithmetic_asian_call_mc,
    basket_call_mc_vr,
    bs_call,
    bs_put,
    implied_vol,
    crr_american,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "golden" / "expected.json"


def _case_outputs() -> Dict[str, Any]:
    # Keep outputs compact and stable across json encoders.
    out: Dict[str, Any] = {}

    # Black–Scholes
    bs_params = dict(S0=100.0, K=100.0, r=0.01, T=1.0, sigma=0.2)
    c = float(bs_call(**bs_params))
    p = float(bs_put(**bs_params))
    out["bs_call_price"] = c
    out["bs_put_price"] = p
    out["implied_vol_call"] = float(implied_vol(price=c, is_call=True, S0=bs_params["S0"], K=bs_params["K"], r=bs_params["r"], T=bs_params["T"]))

    # Binomial (American put)
    params = CRRParams(S0=100.0, K=100.0, r=0.03, T=1.0, sigma=0.25, n=200)
    K = params.K
    put_payoff = lambda ST: max(K - ST, 0.0)
    out["crr_american_put"] = float(crr_american(params, put_payoff))

    # Monte Carlo (Asian arithmetic call)
    asian = arithmetic_asian_call_mc(
        S0=100.0,
        K=100.0,
        r=0.03,
        T=1.0,
        sigma=0.2,
        n_obs=50,
        n_paths=20000,
        seed=123,
        antithetic=True,
        use_control_variate=True,
        alpha=0.05,
    )
    cv = asian["control_variate_result"]
    out["asian_mc_price_cv"] = float(cv["mean"])
    out["asian_mc_ci_hw_cv"] = float(0.5 * (cv["ci_high"] - cv["ci_low"]))

    # Monte Carlo (Basket call)
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
    basket = basket_call_mc_vr(
        S0=S0,
        w=w,
        K=100.0,
        r=0.02,
        T=1.0,
        vol=vol,
        corr=corr,
        n_paths=30000,
        seed=321,
        antithetic=True,
        lhs=True,
        use_control_variate=True,
        alpha=0.05,
    )
    bcv = basket["control_variate_result"]
    out["basket_mc_price_cv"] = float(bcv["mean"])
    out["basket_mc_ci_hw_cv"] = float(0.5 * (bcv["ci_high"] - bcv["ci_low"]))

    return out


def generate() -> None:
    expected = _case_outputs()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(expected, indent=2, sort_keys=True))
    print(f"Wrote {OUT}")


def verify() -> None:
    if not OUT.exists():
        raise SystemExit(f"Missing {OUT}. Run 'python scripts/golden.py generate'.")
    expected = json.loads(OUT.read_text())
    got = _case_outputs()

    # tolerances: MC is noisy (though deterministic under seeded RNG), keep small but nonzero.
    tol = {
        "default": dict(rtol=0.0, atol=0.0),
        "asian_mc_price_cv": dict(rtol=0.0, atol=1e-10),
        "asian_mc_ci_hw_cv": dict(rtol=0.0, atol=1e-10),
        "basket_mc_price_cv": dict(rtol=0.0, atol=1e-10),
        "basket_mc_ci_hw_cv": dict(rtol=0.0, atol=1e-10),
    }

    mismatches = []
    for k, exp in expected.items():
        if k not in got:
            mismatches.append((k, exp, None))
            continue
        g = got[k]
        t = tol.get(k, tol["default"])
        if not np.isclose(float(g), float(exp), rtol=t["rtol"], atol=t["atol"]):
            mismatches.append((k, exp, g))

    if mismatches:
        for k, exp, g in mismatches:
            print(f"MISMATCH {k}: expected={exp} got={g}")
        raise SystemExit(2)

    print("Golden verification OK")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"generate", "verify"}:
        raise SystemExit("Usage: python scripts/golden.py [generate|verify]")
    if sys.argv[1] == "generate":
        generate()
    else:
        verify()


if __name__ == "__main__":
    main()
