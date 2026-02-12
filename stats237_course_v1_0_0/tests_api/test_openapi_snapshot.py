from __future__ import annotations

import json
from pathlib import Path


def test_openapi_snapshot_matches_current_app() -> None:
    """Schema-freeze gate.

    If this test fails:
      - Review the OpenAPI diff (usually means you changed request/response models)
      - If intentional, run: python scripts/snapshot_openapi.py
    """

    from api.app import app

    root = Path(__file__).resolve().parents[1]
    snap_path = root / "api" / "openapi_snapshot.json"
    assert snap_path.exists(), "Missing api/openapi_snapshot.json; run scripts/snapshot_openapi.py"

    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    cur = app.openapi()

    # json.dumps with sort_keys gives stable comparison + readable diffs in pytest output.
    snap_s = json.dumps(snap, sort_keys=True)
    cur_s = json.dumps(cur, sort_keys=True)
    assert snap_s == cur_s, "OpenAPI snapshot drift — run scripts/snapshot_openapi.py if intentional"
