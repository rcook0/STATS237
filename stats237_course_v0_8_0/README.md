# Stats237 — Executable Course Reader + Quant Library (v0.8.0)

This workspace turns **Stats 237** materials (slides, handwritten notes, HW + finals) into:

1) a **narrative course reader** (HTML site + PDF export), and
2) an **executable quant library** (pricing + Greeks + binomial + Monte Carlo exotics + variance reduction),

…with a **problem bank** + **coverage matrix** tying problems ↔ functions ↔ invariants.

## What’s new in v0.8.0 (research-grade “executable reader”)

- **Book build** (MkDocs): `book/` → `build/site/` HTML
- **Reader PDF export** (ReportLab fallback): `build/Stats237_Reader.pdf`
- **Chapter registry**: `chapters/chapters.yaml` drives generated indices
- **Notebooks** (non-executing by default) embedded in the HTML reader

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

## API (v0.7)

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000/docs
```

Every endpoint returns `{ provenance, result }` for reproducibility.

## Roadmap

- v0.9 — Reading Edition rendering (crop/deskew/contrast) for handwritten notes
- v1.0 — problem bank → test completion push + calibration hooks (implied vol surface)
