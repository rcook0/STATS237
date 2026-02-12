import numpy as np

from stats237_quantlib.mc.asian import arithmetic_asian_call_mc
from stats237_quantlib.mc.basket import basket_call_mc_vr


def test_asian_control_variate_reduces_sd():
    # Parameters chosen to make arithmetic and geometric payoffs highly correlated.
    res = arithmetic_asian_call_mc(
        S0=100.0,
        K=100.0,
        r=0.03,
        T=1.0,
        sigma=0.2,
        n_obs=50,
        n_paths=8000,
        seed=42,
        antithetic=True,
        use_control_variate=True,
    )
    sd_base = res["baseline"]["sd"]
    sd_cv = res["control_variate_result"]["sd"]
    assert sd_cv < 0.85 * sd_base


def test_basket_control_variate_reduces_sd():
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
    res = basket_call_mc_vr(
        S0=S0,
        w=w,
        K=100.0,
        r=0.02,
        T=1.0,
        vol=vol,
        corr=corr,
        n_paths=10000,
        seed=7,
        antithetic=True,
        lhs=False,
        use_control_variate=True,
    )
    sd_base = res["baseline"]["sd"]
    sd_cv = res["control_variate_result"]["sd"]
    assert sd_cv < 0.9 * sd_base
