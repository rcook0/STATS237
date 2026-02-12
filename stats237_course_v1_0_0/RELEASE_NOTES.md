# Release Notes

## v1.0.0 — GA baseline

This is the first **stable + reproducible** release line.

Key changes (vs the v0.x build-ups):

- **Problems → Tests harness**: editable `problem_bank/test_specs.yaml` drives pytest generation
- **Public API freeze**: stable import surface via `stats237_quantlib.public_api`
- **API reproducibility**: `{provenance, result}` envelope everywhere
- **OpenAPI snapshot**: schema freeze gate via `api/openapi_snapshot.json`
- **Golden runs**: deterministic regression checks in CI
- **Reader artifacts**: HTML reader (MkDocs) + PDF reader export (ReportLab)
- **Reading Edition**: crop/contrast workflow for handwriting scans
- **Docker scaffolding**: `docker compose up --build` runs the API

See `docs/release.md` for how to run the release gates.
