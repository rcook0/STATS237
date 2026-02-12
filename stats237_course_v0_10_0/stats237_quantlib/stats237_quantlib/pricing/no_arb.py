from __future__ import annotations
import numpy as np

def bounds_european_call_put(S0: float, K: float, r: float, T: float) -> dict:
    """
    Basic no-arbitrage bounds (no dividends):
    Call: max(0, S0 - K e^{-rT}) <= C <= S0
    Put : max(0, K e^{-rT} - S0) <= P <= K e^{-rT}
    """
    df = float(np.exp(-r * T))
    call_lb = max(0.0, S0 - K * df)
    call_ub = S0
    put_lb = max(0.0, K * df - S0)
    put_ub = K * df
    return {
        "call_lb": call_lb, "call_ub": call_ub,
        "put_lb": put_lb, "put_ub": put_ub,
        "df": df,
    }

def put_call_parity_residual(C: float, P: float, S0: float, K: float, r: float, T: float) -> float:
    """
    Residual of put-call parity (no dividends):
    C - P - (S0 - K e^{-rT}) = 0
    """
    df = float(np.exp(-r * T))
    return (C - P) - (S0 - K * df)
