from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Literal
import numpy as np

Payoff = Callable[[float], float]

@dataclass(frozen=True)
class CRRParams:
    S0: float
    K: float
    r: float
    T: float
    sigma: float
    n: int  # steps

def _crr_ud(params: CRRParams) -> tuple[float, float, float, float]:
    dt = params.T / params.n
    u = float(np.exp(params.sigma * np.sqrt(dt)))
    d = 1.0 / u
    df = float(np.exp(-params.r * dt))
    q = (np.exp(params.r * dt) - d) / (u - d)
    if not (0.0 < q < 1.0):
        raise ValueError(f"Risk-neutral prob q out of (0,1): {q}")
    return u, d, q, df

def crr_european(params: CRRParams, payoff: Payoff) -> float:
    u, d, q, df = _crr_ud(params)
    # terminal prices
    j = np.arange(params.n + 1)
    ST = params.S0 * (u ** j) * (d ** (params.n - j))
    pay = np.vectorize(payoff)(ST)
    # risk-neutral expectation
    # binomial probabilities
    from math import comb
    probs = np.array([comb(params.n, int(k)) * (q**k) * ((1-q)**(params.n-k)) for k in j], dtype=float)
    price = (df ** params.n) * float(np.sum(probs * pay))
    return price

def crr_american(params: CRRParams, payoff: Payoff) -> float:
    u, d, q, df = _crr_ud(params)
    # backward induction with early exercise
    # terminal
    j = np.arange(params.n + 1)
    ST = params.S0 * (u ** j) * (d ** (params.n - j))
    V = np.vectorize(payoff)(ST).astype(float)
    for step in range(params.n - 1, -1, -1):
        j = np.arange(step + 1)
        S = params.S0 * (u ** j) * (d ** (step - j))
        cont = df * (q * V[1:] + (1 - q) * V[:-1])
        exer = np.vectorize(payoff)(S).astype(float)
        V = np.maximum(exer, cont)
    return float(V[0])

def one_step_replication(S0: float, Su: float, Sd: float, Vu: float, Vd: float, r_dt: float) -> tuple[float, float]:
    """
    One-step replication:
      delta = (Vu - Vd) / (Su - Sd)
      B = e^{-r dt} (Vu - delta * Su) = e^{-r dt} (Vd - delta * Sd)
    Returns (delta, B)
    """
    if Su == Sd:
        raise ValueError("Su == Sd; cannot replicate.")
    delta = (Vu - Vd) / (Su - Sd)
    df = float(np.exp(-r_dt))
    B = df * (Vu - delta * Su)
    return float(delta), float(B)
