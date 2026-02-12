# Stats237 — Executable Course Reader + Quant Library (v1.0.0)

This repo turns **Stats 237** materials (slides, handwritten notes, HW + finals) into:

1) a **course reader** (HTML site + PDF export), and
2) an **executable quant library** (pricing, Greeks, binomial, Monte Carlo exotics, variance reduction),

…with a **problem bank** + **coverage matrix** tying problems ↔ functions ↔ tests.

## v1.0.0 definition

v1.0.0 is the first **publishable + stable + reproducible** baseline.

- **Stable import surface:** `stats237_quantlib.public_api`
- **Stable REST surface:** FastAPI schemas are snapshotted + gated
- **Reproducible numerics:** seeded MC + golden runs
- **Reader artifacts:** one-command build generates HTML/PDF (+ Reading Edition when notes exist)

## Quickstart

### 1) Put source PDFs/ZIPs into `inputs/`
Drop your PDFs / ZIPs into `inputs/`. Supported:
- PDFs directly
- ZIPs containing PDFs (recursively extracted)

### 2) Create environment (Python 3.11+)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e stats237_quantlib
python -m pip install -r requirements.txt
```

Optional (build HTML reader):
```bash
python -m pip install -r requirements-docs.txt
```

### 3) One-command build
```bash
./run_all.sh
# Windows: .\run_all.ps1
```

Outputs (when inputs are present):
- `registry/materials_registry.json`
- `problem_bank/problems.json`
- `coverage/coverage_matrix.csv` + `coverage/coverage_report.md`

Reader outputs:
- `build/site/index.html` (if MkDocs installed)
- `build/Stats237_Reader.pdf` (always)
- `build/reading_edition/*.pdf` (if notes detected + deps installed)

## API

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000/docs
```

Every endpoint returns `{ provenance, result }`.

## Releases

- Release gates + how-to: `docs/release.md`
- v1.x plan: `docs/v1_roadmap.md`

## Docker

```bash
docker compose up --build
```
