"""Create/update an OpenAPI snapshot for schema-freeze gating.

Usage:
  python scripts/snapshot_openapi.py

Writes: api/openapi_snapshot.json

Note: This script modifies sys.path so it works from a fresh checkout
without requiring `pip install -e stats237_quantlib`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    ql = root / "stats237_quantlib"
    if ql.exists() and str(ql) not in sys.path:
        sys.path.insert(0, str(ql))

    from api.app import app

    out_path = root / "api" / "openapi_snapshot.json"
    snapshot = app.openapi()
    out_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
