# Release process (v1.0+)

This project tries to be *research-grade* without becoming *ceremonial*. The
release process is therefore a small set of deterministic gates that keep the
public surface stable.

## One-command dev build

```bash
./run_all.sh
# Windows: .\run_all.ps1
```

This:
- ingests `inputs/` (if present)
- builds the problem bank + coverage matrix
- runs tests
- builds the HTML reader (if mkdocs is installed)
- exports the PDF reader
- optionally produces a Reading Edition for handwritten notes

## v1+ gates

Run:

```bash
python scripts/release_gate.py --strict
```

Gates:
1) **Public API** imports cleanly (`stats237_quantlib.public_api`)
2) **OpenAPI schema freeze** matches `api/openapi_snapshot.json`
3) **Coverage threshold**: by default, at least **70%** of problems are marked
   `ready` (or higher) in `coverage/coverage_matrix.csv`

Tweak coverage threshold:

```bash
STATS237_COVERAGE_THRESHOLD=0.80 python scripts/release_gate.py --strict
```

## Updating the OpenAPI snapshot

If you intentionally changed request/response models:

```bash
python scripts/snapshot_openapi.py
```

Then rerun tests.

## Recommended “dist” build

This repo keeps dist simple. A typical release workflow is:

1) `./run_all.sh`
2) `python scripts/release_gate.py --strict`
3) commit
4) tag `v1.x.y`

(You can add wheels/docker pushes later once you care about distribution.)
