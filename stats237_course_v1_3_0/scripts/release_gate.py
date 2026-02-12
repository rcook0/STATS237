"""Release gates for v1+.

This is intentionally boring: deterministic checks that prevent accidental
breakage of the public surface.

Checks:
- OpenAPI snapshot matches current FastAPI app
- Public API surface imports cleanly
- (Optional) Coverage threshold: % of problems marked `ready` (or higher)

Usage:
  python scripts/release_gate.py --strict
  python scripts/release_gate.py --coverage-threshold 0.70

Env:
  STATS237_COVERAGE_THRESHOLD (default: 0.70)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


def _add_sys_path(root: Path) -> None:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    ql = root / "stats237_quantlib"
    if ql.exists() and str(ql) not in sys.path:
        sys.path.insert(0, str(ql))


def check_openapi_snapshot(root: Path, strict: bool) -> None:
    snap_path = root / "api" / "openapi_snapshot.json"
    if not snap_path.exists():
        msg = "Missing api/openapi_snapshot.json — run scripts/snapshot_openapi.py"
        if strict:
            raise SystemExit(msg)
        print("(warn)", msg)
        return

    snap = json.loads(snap_path.read_text(encoding="utf-8"))

    from api.app import app

    cur = app.openapi()
    if json.dumps(snap, sort_keys=True) != json.dumps(cur, sort_keys=True):
        raise SystemExit(
            "OpenAPI snapshot drift — review changes; run scripts/snapshot_openapi.py if intentional"
        )


def check_public_api(root: Path) -> None:
    from stats237_quantlib import public_api

    missing = [name for name in public_api.__all__ if not hasattr(public_api, name)]
    if missing:
        raise SystemExit(f"Public API missing symbols: {missing}")


def check_coverage(root: Path, threshold: float, strict: bool) -> None:
    csv_path = root / "coverage" / "coverage_matrix.csv"
    if not csv_path.exists():
        msg = "No coverage/coverage_matrix.csv present (no inputs ingested yet)"
        if strict:
            raise SystemExit(msg)
        print("(warn)", msg)
        return

    # Distinct problems and which are ready/passed gating.
    total: set[str] = set()
    ready: set[str] = set()

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            pid = row.get("problem_id") or ""
            if not pid:
                continue
            total.add(pid)
            status = (row.get("status") or "").strip().lower()
            if status in {"ready", "tested", "pass", "passed"}:
                ready.add(pid)

    if not total:
        msg = "Coverage matrix is empty"
        if strict:
            raise SystemExit(msg)
        print("(warn)", msg)
        return

    ratio = len(ready) / len(total)
    print(f"Coverage: {len(ready)}/{len(total)} = {ratio:.1%} (threshold {threshold:.0%})")
    if ratio < threshold:
        raise SystemExit(
            f"Coverage below threshold: {ratio:.1%} < {threshold:.0%}. "
            "Promote problem specs from pending -> ready in problem_bank/test_specs.yaml."
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--strict", action="store_true", help="Fail if inputs/coverage missing")
    p.add_argument(
        "--coverage-threshold",
        type=float,
        default=float(os.environ.get("STATS237_COVERAGE_THRESHOLD", "0.70")),
    )
    p.add_argument("--skip-coverage", action="store_true")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    _add_sys_path(root)

    check_public_api(root)
    check_openapi_snapshot(root, strict=args.strict)

    if not args.skip_coverage:
        check_coverage(root, threshold=args.coverage_threshold, strict=args.strict)

    print("Release gates: OK")


if __name__ == "__main__":
    main()
