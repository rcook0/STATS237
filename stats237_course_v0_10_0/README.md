# Stats237 — Executable Course Reader + Quant Library (v0.10.0)

This workspace turns **Stats 237** materials (slides, handwritten notes, HW + finals) into:

1) a **narrative course reader** (HTML site + PDF export), and
2) an **executable quant library** (pricing + Greeks + binomial + Monte Carlo exotics + variance reduction),

…with a **problem bank** + **coverage matrix** tying problems ↔ functions ↔ invariants.

## What’s new in v0.10.0 (pre-v1 ship gates)

This release adds the remaining pre-v1 “ship gates”:

1) **Problems → Tests** (editable spec → pytest)
2) **Public API freeze** + semantic version policy
3) **Calibration hooks** (IV curve + surface interpolation entrypoints)
4) **Golden runs** (deterministic regression guards)
5) **Distribution scaffolding** (Dockerfile + docker-compose)

The v0.9 Reading Edition pipeline remains:

- **Auto-crop** to the ink (remove margins)
- **Contrast normalization** (helps screen reading)
- Optional **two-up** rendering (two note pages per sheet for flow)

The core v0.8 “executable reader” remains:
- Book build (MkDocs) → `build/site/`
- Reader PDF export (ReportLab fallback) → `build/Stats237_Reader.pdf`
- Chapter registry + generated indices
- Notebooks (non-executing by default)

Still included:
- v0.6 exotics + variance reduction
- v0.7 API + reproducibility envelope

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

Outputs:
- `build/site/index.html` (if MkDocs installed)
- `build/Stats237_Reader.pdf` (always)
- `build/reading_edition/*.pdf` (if notes found + pymupdf/pillow installed)
- `registry/materials_registry.json`
- `problem_bank/problems.json`
- `coverage/coverage_matrix.csv` + `coverage/coverage_report.md`

## Reader (HTML)

Build explicitly:
```bash
python scripts/build_chapter_registry.py
python scripts/build_book.py
mkdocs -f book/mkdocs.yml build
```

## Reader (PDF)

Always available:
```bash
python scripts/export_reader_pdf.py
```

## API (v0.10)

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000/docs
```

Every endpoint returns `{ provenance, result }` for reproducibility.

## Pre-v1 gates (Step 1–5)

- Step 1 docs: `docs/problems_to_tests.md`
- Step 2 docs: `docs/public_api.md`
- Step 5 docs: `docs/deployment.md`

## Roadmap

See `docs/v1_roadmap.md`.

## Docker

```bash
docker compose up --build
```

## Reading Edition

Put your handwritten notes PDF/ZIP into `inputs/` (filenames containing `note` or `notes` are auto-detected).

Build only the reading edition:
```bash
python scripts/build_reading_edition.py
```

Manual run (advanced):
```bash
python scripts/reading_edition.py --in path/to/Notes.pdf --out build/reading_edition/Notes_ReadingEdition.pdf
```
