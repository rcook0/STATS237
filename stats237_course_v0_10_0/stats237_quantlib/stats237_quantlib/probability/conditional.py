from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Hashable, Iterable, Tuple, Callable, Any
import numpy as np

def condexp_discrete(
    x: Dict[Hashable, float],
    p: Dict[Hashable, float],
    given: Dict[Hashable, Hashable],
) -> Dict[Hashable, float]:
    """
    Conditional expectation E[X | G] for a discrete finite probability space.

    Args:
        x: state -> X(state)
        p: state -> P(state), sums to 1
        given: state -> group label (sigma-algebra partition id)

    Returns:
        group_label -> E[X | group_label]
    """
    num = {}
    den = {}
    for s, xs in x.items():
        ps = p.get(s, 0.0)
        g = given[s]
        num[g] = num.get(g, 0.0) + xs * ps
        den[g] = den.get(g, 0.0) + ps
    out = {}
    for g in num:
        if den[g] <= 0:
            raise ValueError(f"Zero probability for group {g}")
        out[g] = num[g] / den[g]
    return out

def tower_property_check(
    x: Dict[Hashable, float],
    p: Dict[Hashable, float],
    g1: Dict[Hashable, Hashable],
    g2: Dict[Hashable, Hashable],
    atol: float = 1e-10,
) -> bool:
    """
    Check E[E[X|G1]|G2] == E[X|G2] when G2 is coarser than G1 (partition refinement).
    This is a pragmatic checker used for tests/examples.
    """
    ex_g1 = condexp_discrete(x, p, g1)
    # lift E[X|G1] back to states
    lifted = {s: ex_g1[g1[s]] for s in x}
    ex2_left = condexp_discrete(lifted, p, g2)
    ex2_right = condexp_discrete(x, p, g2)
    for k in ex2_right:
        if not np.isclose(ex2_left[k], ex2_right[k], atol=atol, rtol=0):
            return False
    return True
