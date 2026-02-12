from __future__ import annotations

import numpy as np

from stats237_quantlib.mc.asian import arithmetic_asian_call_mc
from stats237_quantlib.mc.basket import basket_call_mc_vr


def test_seed_reproducibility_asian():
    a = arithmetic_asian_call_mc(S0=100, K=100, r=0.01, T=1.0, sigma=0.2, n_obs=12, n_paths=5000, seed=42, method="lhs")
    b = arithmetic_asian_call_mc(S0=100, K=100, r=0.01, T=1.0, sigma=0.2, n_obs=12, n_paths=5000, seed=42, method="lhs")
    assert a["baseline"]["mean"] == b["baseline"]["mean"]
    if "control_variate" in a:
        assert a["control_variate"]["adjusted"]["mean"] == b["control_variate"]["adjusted"]["mean"]


def test_seed_reproducibility_basket_qmc():
    S0 = np.array([100.0, 100.0])
    w = np.array([0.5, 0.5])
    vol = np.array([0.2, 0.2])
    corr = np.array([[1.0, 0.3],[0.3, 1.0]])
    a = basket_call_mc_vr(S0, w, 100, 0.01, 1.0, vol, corr, n_paths=4096, seed=7, method="sobol")
    b = basket_call_mc_vr(S0, w, 100, 0.01, 1.0, vol, corr, n_paths=4096, seed=7, method="sobol")
    assert a["baseline"]["mean"] == b["baseline"]["mean"]
