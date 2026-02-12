from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app
from stats237_quantlib.pricing.black_scholes import bs_call


client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_meta() -> None:
    r = client.get("/meta")
    assert r.status_code == 200
    j = r.json()
    assert "api_version" in j
    assert "quantlib_version" in j
    assert "endpoints" in j


def test_black_scholes_price() -> None:
    payload = {"S0": 100.0, "K": 100.0, "r": 0.02, "T": 1.0, "sigma": 0.2, "is_call": True}
    r = client.post("/price/black_scholes", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert "provenance" in j and "result" in j
    assert j["provenance"]["seed_effective"] == 0
    args = dict(payload)
    args.pop("is_call", None)
    expected = bs_call(**args)
    assert abs(j["result"]["price"] - expected) < 1e-12


def test_asian_mc_provenance_seed() -> None:
    payload = {
        "S0": 100.0,
        "K": 100.0,
        "r": 0.02,
        "T": 1.0,
        "sigma": 0.2,
        "n_obs": 12,
        "n_paths": 2000,
        "seed": 777,
        "antithetic": True,
        "use_control_variate": True,
        "alpha": 0.05,
    }
    r = client.post("/mc/asian/arithmetic_call", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert j["provenance"]["seed_effective"] == 777
    # ensure shape of result
    assert "baseline" in j["result"]
