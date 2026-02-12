from __future__ import annotations

import numpy as np

from stats237_quantlib.mc.asian import arithmetic_asian_call_mc
from stats237_quantlib.mc.basket import basket_call_mc_vr


def test_vr_reduces_sd_asian_typical():
    res_plain = arithmetic_asian_call_mc(S0=100, K=100, r=0.01, T=1.0, sigma=0.2, n_obs=12, n_paths=8000, seed=123, antithetic=False, use_control_variate=False, method="plain")
    res_vr = arithmetic_asian_call_mc(S0=100, K=100, r=0.01, T=1.0, sigma=0.2, n_obs=12, n_paths=8000, seed=123, antithetic=True, use_control_variate=True, method="lhs")
    assert res_vr["control_variate"]["adjusted"]["sd"] <= res_plain["baseline"]["sd"]


def test_vr_reduces_sd_basket_typical():
    S0 = np.array([100.0, 100.0, 100.0])
    w = np.array([1/3, 1/3, 1/3])
    vol = np.array([0.2, 0.25, 0.3])
    corr = np.array([[1.0, 0.2, 0.1],[0.2, 1.0, 0.3],[0.1, 0.3, 1.0]])

    plain = basket_call_mc_vr(S0, w, 100, 0.01, 1.0, vol, corr, n_paths=12000, seed=5, antithetic=False, use_control_variate=False, method="plain")
    vr = basket_call_mc_vr(S0, w, 100, 0.01, 1.0, vol, corr, n_paths=12000, seed=5, antithetic=True, use_control_variate=True, method="sobol")
    assert vr["control_variate"]["adjusted"]["sd"] <= plain["baseline"]["sd"]
