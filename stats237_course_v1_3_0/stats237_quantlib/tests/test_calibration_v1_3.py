from __future__ import annotations

import numpy as np

from stats237_quantlib.calibration.iv_curve import (
    SmileSlice,
    implied_vols_from_prices,
    fit_iv_smile_pchip,
    iv_surface_total_variance,
)
from stats237_quantlib.pricing.black_scholes import bs_call


def test_implied_vols_from_prices_recovers_flat_vol_with_dividend_yield():
    S0, r, q, T = 100.0, 0.02, 0.01, 0.5
    sigma = 0.2
    strikes = np.array([80, 90, 100, 110, 120], dtype=float)
    prices = np.array([bs_call(S0, K, r, T, sigma, q=q) for K in strikes], dtype=float)

    iv = implied_vols_from_prices(strikes=strikes, prices=prices, S0=S0, r=r, q=q, T=T, is_call=True)
    assert np.all(np.isfinite(iv))
    # implied vols should recover the generating sigma (within tight tolerance)
    assert float(np.max(np.abs(iv - sigma))) < 5e-6


def test_pchip_smile_interpolates_reasonably():
    strikes = np.array([90, 100, 110], dtype=float)
    vols = np.array([0.25, 0.20, 0.23], dtype=float)
    smile = fit_iv_smile_pchip(strikes=strikes, vols=vols)

    # exact at knots
    out = np.asarray(smile(strikes), dtype=float)
    assert float(np.max(np.abs(out - vols))) < 1e-12


def test_total_variance_surface_interpolation_matches_formula():
    S0, r, q = 100.0, 0.02, 0.01
    strikes = np.array([90, 100, 110], dtype=float)

    s0 = SmileSlice(T=0.5, strikes=strikes, vols=np.array([0.2, 0.2, 0.2], dtype=float))
    s1 = SmileSlice(T=1.0, strikes=strikes, vols=np.array([0.25, 0.25, 0.25], dtype=float))

    surf = iv_surface_total_variance(smiles=[s0, s1], S0=S0, r=r, q=q)

    Tq = np.array([0.75], dtype=float)
    Kq = np.array([100.0], dtype=float)

    vol = float(np.asarray(surf(Tq, Kq), dtype=float).reshape(-1)[0])

    # expected via linear interpolation in total variance
    w0 = (0.2**2) * 0.5
    w1 = (0.25**2) * 1.0
    lam = (0.75 - 0.5) / (1.0 - 0.5)
    w = (1.0 - lam) * w0 + lam * w1
    expected = float(np.sqrt(w / 0.75))

    assert abs(vol - expected) < 1e-10
