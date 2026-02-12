import numpy as np
from stats237_quantlib.pricing.black_scholes import bs_call, bs_put, implied_vol
from stats237_quantlib.pricing.no_arb import put_call_parity_residual, bounds_european_call_put
from stats237_quantlib.pricing.binomial import CRRParams, crr_european

def test_put_call_parity_zero_rate():
    S0=100.0; K=100.0; r=0.0; T=1.0; sigma=0.2
    C=bs_call(S0,K,r,T,sigma)
    P=bs_put(S0,K,r,T,sigma)
    res=put_call_parity_residual(C,P,S0,K,r,T)
    assert abs(res) < 1e-10

def test_bs_implied_vol_roundtrip():
    S0=100.0; K=110.0; r=0.03; T=0.7; sigma=0.35
    C=bs_call(S0,K,r,T,sigma)
    iv=implied_vol(C, True, S0,K,r,T)
    assert abs(iv - sigma) < 1e-8

def test_no_arb_bounds_hold_for_bs():
    S0=100.0; K=120.0; r=0.01; T=2.0; sigma=0.25
    C=bs_call(S0,K,r,T,sigma)
    P=bs_put(S0,K,r,T,sigma)
    b=bounds_european_call_put(S0,K,r,T)
    assert b["call_lb"] <= C <= b["call_ub"]
    assert b["put_lb"] <= P <= b["put_ub"]

def test_binomial_converges_reasonably():
    # basic sanity: binomial price should be close to BS for enough steps (call)
    S0=100.0; K=100.0; r=0.01; T=1.0; sigma=0.2
    from stats237_quantlib.pricing.black_scholes import bs_call
    bs=bs_call(S0,K,r,T,sigma)
    params=CRRParams(S0=S0,K=K,r=r,T=T,sigma=sigma,n=400)
    payoff=lambda s: max(s-K,0.0)
    crr=crr_european(params,payoff)
    assert abs(crr - bs) / bs < 0.01
