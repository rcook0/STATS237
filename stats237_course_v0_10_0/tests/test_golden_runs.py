from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def test_golden_runs_match_expected():
    # Import the computation function from the golden script.
    from scripts.golden import _case_outputs

    root = Path(__file__).resolve().parents[1]
    expected_path = root / "golden" / "expected.json"
    assert expected_path.exists(), "golden/expected.json missing"

    expected = json.loads(expected_path.read_text())
    got = _case_outputs()

    for k, exp in expected.items():
        assert k in got, f"missing key in golden outputs: {k}"
        assert np.isclose(float(got[k]), float(exp), rtol=0.0, atol=1e-10), f"mismatch for {k}"
