#!/usr/bin/env python3
"""
Generate a coverage matrix mapping problems -> candidate functions -> status.

Status is "stub" until a dedicated test is added. This is intentional:
the matrix is the planning surface.
"""
from __future__ import annotations
from pathlib import Path
import json, csv, datetime
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = ROOT / "problem_bank" / "problems.json"
CSV_OUT = ROOT / "coverage" / "coverage_matrix.csv"
MD_OUT = ROOT / "coverage" / "coverage_report.md"

TAG_TO_FUNCS = {
    "conditional_expectation": [
        "stats237_quantlib.probability.conditional.condexp_discrete",
        "stats237_quantlib.probability.conditional.tower_property_check",
    ],
    "no_arb": [
        "stats237_quantlib.pricing.no_arb.bounds_european_call_put",
        "stats237_quantlib.pricing.no_arb.put_call_parity_residual",
    ],
    "binomial": [
        "stats237_quantlib.pricing.binomial.crr_european",
        "stats237_quantlib.pricing.binomial.crr_american",
        "stats237_quantlib.pricing.binomial.one_step_replication",
    ],
    "black_scholes": [
        "stats237_quantlib.pricing.black_scholes.bs_call",
        "stats237_quantlib.pricing.black_scholes.bs_put",
        "stats237_quantlib.pricing.black_scholes.greeks_call_put",
        "stats237_quantlib.pricing.black_scholes.implied_vol",
    ],
    "monte_carlo": [
        "stats237_quantlib.mc.core.mc_mean_ci",
    ],
    "basket": [
        "stats237_quantlib.mc.basket.basket_call_mc",
    ],
    "asian": [
        "stats237_quantlib.mc.asian.geometric_asian_call_closed_form",
    ],
}

def main() -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pb = json.loads(PROBLEMS.read_text())
    rows=[]
    for p in pb["problems"]:
        funcs=[]
        for t in p["tags"]:
            funcs.extend(TAG_TO_FUNCS.get(t, []))
        funcs = sorted(dict.fromkeys(funcs))
        if not funcs:
            funcs = []
        for f in funcs:
            rows.append({
                "problem_id": p["id"],
                "source": p["source_filename"],
                "tags": ",".join(p["tags"]),
                "function": f,
                "status": "stub",
            })
        if not funcs:
            rows.append({
                "problem_id": p["id"],
                "source": p["source_filename"],
                "tags": ",".join(p["tags"]),
                "function": "",
                "status": "unmapped",
            })

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["problem_id","source","tags","function","status"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # markdown report summary
    total = len(pb["problems"])
    mapped = len({r["problem_id"] for r in rows if r["status"] != "unmapped"})
    unmapped = total - mapped
    md = [
        f"# Coverage report (generated {now})",
        "",
        f"- Problems total: **{total}**",
        f"- Problems mapped to ≥1 function: **{mapped}**",
        f"- Unmapped: **{unmapped}**",
        "",
        "## Next actions",
        "- Review `problem_bank/problems.json` for segmentation quality.",
        "- For each top problem, add a dedicated unit/property test and flip status from `stub` to `tested`.",
        "",
    ]
    MD_OUT.write_text("\n".join(md))
    print(f"Wrote {CSV_OUT} and {MD_OUT}")

if __name__ == "__main__":
    main()
