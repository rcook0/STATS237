from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BSRequest(BaseModel):
    S0: float = Field(..., gt=0)
    K: float = Field(..., gt=0)
    r: float
    T: float = Field(..., gt=0)
    sigma: float = Field(..., gt=0)
    is_call: bool = True


class ImpliedVolRequest(BaseModel):
    price: float = Field(..., gt=0)
    is_call: bool = True
    S0: float = Field(..., gt=0)
    K: float = Field(..., gt=0)
    r: float
    T: float = Field(..., gt=0)
    vol_low: float = 1e-6
    vol_high: float = 5.0
    tol: float = 1e-10
    max_iter: int = 200


class BinomialRequest(BaseModel):
    S0: float = Field(..., gt=0)
    K: float = Field(..., gt=0)
    r: float
    T: float = Field(..., gt=0)
    sigma: float = Field(..., gt=0)
    n: int = Field(100, ge=1, le=10000)
    is_call: bool = True
    exercise: Literal["european", "american"] = "european"


MCMethod = Literal["plain", "lhs", "sobol", "halton"]


class AsianMCRequest(BaseModel):
    S0: float = Field(..., gt=0)
    K: float = Field(..., gt=0)
    r: float
    T: float = Field(..., gt=0)
    sigma: float = Field(..., gt=0)
    n_obs: int = Field(50, ge=1, le=5000)
    n_paths: int = Field(20000, ge=1000, le=5_000_000)
    seed: int = 123

    # Variance reduction / sampling
    method: MCMethod = "plain"
    qmc_scramble: bool = True
    antithetic: bool = True
    use_control_variate: bool = True
    use_extra_control: bool = True

    alpha: float = 0.05


class BasketMCRequest(BaseModel):
    S0: list[float]
    w: list[float]
    K: float = Field(..., gt=0)
    r: float
    T: float = Field(..., gt=0)
    vol: list[float]
    corr: list[list[float]]
    n_paths: int = Field(20000, ge=1000, le=5_000_000)
    seed: int = 123

    # Back-compat: lhs flag (if True, method is forced to "lhs")
    lhs: bool = False

    # Variance reduction / sampling
    method: MCMethod = "plain"
    qmc_scramble: bool = True
    antithetic: bool = True
    use_control_variate: bool = True
    use_extra_control: bool = True

    alpha: float = 0.05
