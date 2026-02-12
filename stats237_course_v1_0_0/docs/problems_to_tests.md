# Problems → Tests (Step 1)

This repo treats **homework + finals** as an *executable spec*.

Pipeline
--------

1. `scripts/problem_bank.py` builds `problem_bank/problems.json` from extracted PDF text.
2. `scripts/build_test_specs.py` creates `problem_bank/test_specs.yaml` (editable).
3. `scripts/generate_problem_tests.py` writes pytest cases under:
   `stats237_quantlib/tests/spec/test_problem_specs_generated.py`
4. `scripts/update_coverage_status.py` upgrades `coverage/coverage_matrix.csv` statuses.

Editing workflow
----------------

Open `problem_bank/test_specs.yaml` and complete cases incrementally:

- Set `function` to the callable you want to test.
- Fill `call.params` so the function call is runnable.
- Set `oracle.kind`:
  - `numeric`: provide a scalar expected value (or `{field,value}` for dict outputs)
  - `invariant`: provide boolean expressions in `oracle.assertions`
  - `pending`: leaves the test as xfail

As soon as a spec is no longer `pending`, the corresponding test becomes **active**.

Why xfail?
----------

Early on, you want **full coverage without red CI**. xfail gives you:

- Every problem has a test case.
- CI stays green until you decide a case is ready.
- You can flip individual problems “on” by filling in params/expected.
