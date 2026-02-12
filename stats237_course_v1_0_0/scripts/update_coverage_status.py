#!/usr/bin/env python3
"""Update coverage_matrix.csv statuses based on test specs.

We keep `scripts/coverage_matrix.py` intentionally simple ("stub"/"unmapped").
This script upgrades statuses using `problem_bank/test_specs.yaml`:

- pending: spec exists but oracle.kind == pending
- ready: oracle.kind != pending and has callable + params

Note: "ready" does not mean it matches the true math yet — it means the test is
now executable and will either pass or fail.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "problem_bank" / "test_specs.yaml"
CSV_PATH = ROOT / "coverage" / "coverage_matrix.csv"


def main() -> None:
    if not (SPECS.exists() and CSV_PATH.exists()):
        raise SystemExit("Missing specs or coverage matrix. Run ingest/extract/problem_bank/coverage first.")

    data = yaml.safe_load(SPECS.read_text())
    spec_by_id = {p["id"]: p for p in data.get("problems", [])}

    rows = []
    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            pid = row["problem_id"]
            if row.get("status") == "unmapped":
                rows.append(row)
                continue

            spec = spec_by_id.get(pid)
            if not spec:
                row["status"] = "stub"
                rows.append(row)
                continue

            oracle = spec.get("oracle") or {}
            kind = oracle.get("kind", "pending")
            fn = spec.get("function")
            params = (spec.get("call") or {}).get("params") or {}

            if not fn:
                row["status"] = "unmapped"
            elif kind == "pending":
                row["status"] = "pending"
            elif params:
                row["status"] = "ready"
            else:
                row["status"] = "pending"

            rows.append(row)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["problem_id", "source", "tags", "function", "status"])
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"Updated statuses in {CSV_PATH}")


if __name__ == "__main__":
    main()
