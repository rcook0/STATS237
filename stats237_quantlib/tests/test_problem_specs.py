from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml


def _resolve(dotted: str):
    mod, _, name = dotted.rpartition(".")
    if not mod:
        raise ValueError(f"Bad dotted path: {dotted}")
    m = importlib.import_module(mod)
    return getattr(m, name)


def _repo_root() -> Path:
    # stats237_quantlib/tests/<this_file> -> repo root
    return Path(__file__).resolve().parents[3]


def _load_specs():
    specs_path = _repo_root() / "problem_bank" / "test_specs.yaml"
    if not specs_path.exists():
        pytest.skip("No problem_bank/test_specs.yaml yet (run build_all with inputs/)", allow_module_level=True)
    data = yaml.safe_load(specs_path.read_text())
    return data.get("problems", [])


@pytest.mark.parametrize("spec", _load_specs(), ids=lambda s: s.get("id", "unknown"))
def test_problem_spec(spec):
    pid = spec.get("id")
    fn = spec.get("function")
    params = (spec.get("call") or {}).get("params") or {}
    oracle = spec.get("oracle") or {}
    kind = oracle.get("kind", "pending")

    if not fn:
        pytest.xfail(f"{pid}: no function mapped yet")
    if kind == "pending":
        pytest.xfail(f"{pid}: spec pending (fill oracle.kind/expected/params)")

    f = _resolve(fn)
    try:
        out = f(**params)
    except TypeError as e:
        pytest.xfail(f"{pid}: params don't match callable yet: {e}")

    if kind == "numeric":
        expected = oracle.get("expected")
        if expected is None:
            pytest.xfail(f"{pid}: missing oracle.expected")
        tol = oracle.get("tolerance") or {}
        rtol = float(tol.get("rtol", 1e-6))
        atol = float(tol.get("atol", 1e-9))

        if isinstance(expected, dict) and "field" in expected and "value" in expected:
            field = expected["field"]
            exp = float(expected["value"])
            if isinstance(out, dict):
                got = float(out[field])
            else:
                pytest.fail(f"{pid}: expected dict output to select field '{field}'")
        else:
            exp = float(expected)
            got = float(out)

        assert got == pytest.approx(exp, rel=rtol, abs=atol)

    elif kind == "invariant":
        assertions = oracle.get("assertions") or []
        if not assertions:
            pytest.xfail(f"{pid}: invariant oracle missing oracle.assertions")
        env = {"out": out, "params": params}
        for expr in assertions:
            assert bool(eval(expr, {}, env)), f"{pid}: invariant failed: {expr}"
    else:
        pytest.xfail(f"{pid}: unknown oracle kind '{kind}'")
