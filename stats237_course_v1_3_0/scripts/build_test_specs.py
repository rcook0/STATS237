#!/usr/bin/env python3
"""Build editable test specs from the problem bank.

This is the bridge from *text problems* -> *executable tests*.

Design goals
------------
- Generate a stable, human-editable file (YAML) that can be gradually completed.
- Every problem becomes a test case immediately.
- Incomplete specs are marked as xfail until filled in.

The YAML format intentionally allows manual editing and incremental completion.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROBLEMS_JSON = ROOT / "problem_bank" / "problems.json"
TEST_SPECS_YAML = ROOT / "problem_bank" / "test_specs.yaml"


def _pick_primary_tag(tags: List[str]) -> str | None:
    # A tiny priority order to propose a default function when multiple tags exist.
    priority = [
        "black_scholes",
        "binomial",
        "asian",
        "basket",
        "monte_carlo",
        "no_arb",
        "conditional_expectation",
    ]
    for t in priority:
        if t in tags:
            return t
    return tags[0] if tags else None


def _suggest_function(tags: List[str]) -> str | None:
    # These should match `scripts/coverage_matrix.py` TAG_TO_FUNCS.
    tag_to_default = {
        "conditional_expectation": "stats237_quantlib.probability.conditional.condexp_discrete",
        "no_arb": "stats237_quantlib.pricing.no_arb.put_call_parity_residual",
        "binomial": "stats237_quantlib.pricing.binomial.crr_european",
        "black_scholes": "stats237_quantlib.pricing.black_scholes.bs_call",
        "monte_carlo": "stats237_quantlib.mc.core.mc_mean_ci",
        "basket": "stats237_quantlib.mc.basket.basket_call_mc_vr",
        "asian": "stats237_quantlib.mc.asian.arithmetic_asian_call_mc",
    }
    t = _pick_primary_tag(tags)
    return tag_to_default.get(t) if t else None


def _extract_hint_numbers(text: str) -> List[float]:
    # Heuristic: grab a few floats/ints as hints for later manual mapping.
    nums = re.findall(r"(?<![A-Za-z])(-?\d+\.?\d*)", text)
    out: List[float] = []
    for n in nums[:12]:
        try:
            out.append(float(n))
        except Exception:
            pass
    return out


def main() -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not PROBLEMS_JSON.exists():
        raise SystemExit(f"Missing {PROBLEMS_JSON}. Run scripts/problem_bank.py first.")

    pb = json.loads(PROBLEMS_JSON.read_text())
    problems = pb.get("problems", [])

    specs: Dict[str, Any] = {
        "generated_at": now,
        "schema_version": "1.0",
        "notes": "Fill in params/expected to turn xfails into real tests.",
        "problems": [],
    }

    for p in problems:
        tags = p.get("tags", [])
        suggested = _suggest_function(tags)
        hint_nums = _extract_hint_numbers(p.get("text", ""))
        specs["problems"].append(
            {
                "id": p["id"],
                "source": p.get("source_filename"),
                "tags": tags,
                "function": suggested,  # override as needed
                "call": {
                    "params": {},  # fill in to call the function
                },
                "oracle": {
                    "kind": "pending",  # pending | numeric | invariant
                    "expected": None,
                    "tolerance": {"rtol": 1e-6, "atol": 1e-9},
                },
                "hints": {
                    "page_start": p.get("page_start"),
                    "page_end": p.get("page_end"),
                    "numbers": hint_nums,
                },
                "text_excerpt": (p.get("text") or "")[:800],
            }
        )

    TEST_SPECS_YAML.parent.mkdir(parents=True, exist_ok=True)
    TEST_SPECS_YAML.write_text(yaml.safe_dump(specs, sort_keys=False, allow_unicode=True))
    print(f"Wrote {TEST_SPECS_YAML} ({len(specs['problems'])} specs)")


if __name__ == "__main__":
    main()
