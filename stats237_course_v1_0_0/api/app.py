from __future__ import annotations

from fastapi import FastAPI, Header
from fastapi.encoders import jsonable_encoder

from stats237_quantlib.meta import get_package_version
from stats237_quantlib.pricing.black_scholes import bs_call, bs_put, greeks_call_put, implied_vol
from stats237_quantlib.pricing.binomial import CRRParams, crr_american, crr_european
from stats237_quantlib.mc.asian import arithmetic_asian_call_mc
from stats237_quantlib.mc.basket import basket_call_mc_vr

from .models import BSRequest, ImpliedVolRequest, BinomialRequest, AsianMCRequest, BasketMCRequest
from .provenance import make_provenance, provenance_to_dict

API_VERSION = "1.0.0"

app = FastAPI(title="Stats237 Quant API", version=API_VERSION)


def envelope(payload: dict, result: object, seed_effective: int, request_id: str | None) -> dict:
    prov = make_provenance(payload=payload, seed_effective=seed_effective, request_id=request_id)
    return {
        "provenance": provenance_to_dict(prov),
        "result": jsonable_encoder(result),
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/meta")
def meta() -> dict:
    return {
        "api_version": API_VERSION,
        "quantlib_version": get_package_version(),
        "endpoints": [
            "GET /health",
            "GET /meta",
            "POST /price/black_scholes",
            "POST /greeks/black_scholes",
            "POST /implied_vol",
            "POST /price/binomial",
            "POST /mc/asian/arithmetic_call",
            "POST /mc/basket/call",
        ],
    }


@app.post("/price/black_scholes")
def price_black_scholes(req: BSRequest, x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> dict:
    payload = req.model_dump()
    args = dict(payload)
    args.pop("is_call", None)
    price = bs_call(**args) if req.is_call else bs_put(**args)
    return envelope(payload, {"price": float(price)}, seed_effective=0, request_id=x_request_id)


@app.post("/greeks/black_scholes")
def greeks_black_scholes(req: BSRequest, x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> dict:
    payload = req.model_dump()
    args = dict(payload)
    args.pop("is_call", None)
    g = greeks_call_put(**args)
    return envelope(payload, g, seed_effective=0, request_id=x_request_id)


@app.post("/implied_vol")
def implied_vol_endpoint(req: ImpliedVolRequest, x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> dict:
    payload = req.model_dump()
    vol = implied_vol(**payload)
    return envelope(payload, {"implied_vol": float(vol)}, seed_effective=0, request_id=x_request_id)


@app.post("/price/binomial")
def price_binomial(req: BinomialRequest, x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> dict:
    payload = req.model_dump()

    params = CRRParams(S0=req.S0, K=req.K, r=req.r, T=req.T, sigma=req.sigma, n=req.n)
    K = req.K
    if req.is_call:
        payoff = lambda ST: max(ST - K, 0.0)
    else:
        payoff = lambda ST: max(K - ST, 0.0)

    if req.exercise == "american":
        price = crr_american(params, payoff)
    else:
        price = crr_european(params, payoff)

    result = {"price": float(price), "exercise": req.exercise, "is_call": bool(req.is_call)}
    return envelope(payload, result, seed_effective=0, request_id=x_request_id)


@app.post("/mc/asian/arithmetic_call")
def mc_asian_arithmetic_call(req: AsianMCRequest, x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> dict:
    payload = req.model_dump()
    result = arithmetic_asian_call_mc(**payload)
    return envelope(payload, result, seed_effective=req.seed, request_id=x_request_id)


@app.post("/mc/basket/call")
def mc_basket_call(req: BasketMCRequest, x_request_id: str | None = Header(default=None, alias="X-Request-Id")) -> dict:
    payload = req.model_dump()
    result = basket_call_mc_vr(
        S0=payload["S0"],
        w=payload["w"],
        K=payload["K"],
        r=payload["r"],
        T=payload["T"],
        vol=payload["vol"],
        corr=payload["corr"],
        n_paths=payload["n_paths"],
        seed=payload["seed"],
        antithetic=payload["antithetic"],
        lhs=payload["lhs"],
        use_control_variate=payload["use_control_variate"],
        alpha=payload["alpha"],
    )
    return envelope(payload, result, seed_effective=req.seed, request_id=x_request_id)
