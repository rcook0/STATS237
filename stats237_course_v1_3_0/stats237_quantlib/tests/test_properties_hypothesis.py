from __future__ import annotations

import math

import pytest

try:
    from hypothesis import given, settings, strategies as st  # type: ignore
except Exception:  # pragma: no cover
    pytest.skip("hypothesis is not installed; skipping property-based tests", allow_module_level=True)

from stats237_quantlib.pricing.black_scholes import bs_call, bs_put


@settings(max_examples=200, deadline=None)
@given(
    S0=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    K=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    r=st.floats(min_value=-0.05, max_value=0.10, allow_nan=False, allow_infinity=False),
    T=st.floats(min_value=1e-3, max_value=5.0, allow_nan=False, allow_infinity=False),
    sigma=st.floats(min_value=1e-3, max_value=2.0, allow_nan=False, allow_infinity=False),
)
def test_put_call_parity(S0, K, r, T, sigma):
    c = bs_call(S0, K, r, T, sigma)
    p = bs_put(S0, K, r, T, sigma)
    df = math.exp(-r * T)
    # parity: C - P = S0 - K*df
    assert math.isfinite(c) and math.isfinite(p)
    assert abs((c - p) - (S0 - K * df)) <= 1e-6 * (1.0 + abs(S0) + abs(K))


@settings(max_examples=200, deadline=None)
@given(
    S0=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    K=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    r=st.floats(min_value=-0.05, max_value=0.10, allow_nan=False, allow_infinity=False),
    T=st.floats(min_value=1e-3, max_value=5.0, allow_nan=False, allow_infinity=False),
    sigma=st.floats(min_value=1e-3, max_value=2.0, allow_nan=False, allow_infinity=False),
)
def test_bounds_call_put(S0, K, r, T, sigma):
    c = bs_call(S0, K, r, T, sigma)
    p = bs_put(S0, K, r, T, sigma)
    df = math.exp(-r * T)

    # Bounds:
    assert 0.0 <= c <= S0 + 1e-9
    assert 0.0 <= p <= K * df + 1e-9

    # Intrinsic lower bounds:
    assert c + 1e-9 >= max(S0 - K * df, 0.0)
    assert p + 1e-9 >= max(K * df - S0, 0.0)


@settings(max_examples=200, deadline=None)
@given(
    K=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    r=st.floats(min_value=-0.05, max_value=0.10, allow_nan=False, allow_infinity=False),
    T=st.floats(min_value=1e-3, max_value=5.0, allow_nan=False, allow_infinity=False),
    sigma=st.floats(min_value=1e-3, max_value=2.0, allow_nan=False, allow_infinity=False),
    S_low=st.floats(min_value=1.0, max_value=250.0, allow_nan=False, allow_infinity=False),
    S_high=st.floats(min_value=251.0, max_value=500.0, allow_nan=False, allow_infinity=False),
)
def test_monotonicity_in_spot(K, r, T, sigma, S_low, S_high):
    c1 = bs_call(S_low, K, r, T, sigma)
    c2 = bs_call(S_high, K, r, T, sigma)
    p1 = bs_put(S_low, K, r, T, sigma)
    p2 = bs_put(S_high, K, r, T, sigma)

    assert c2 >= c1 - 1e-9
    assert p2 <= p1 + 1e-9
