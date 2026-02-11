# Stats 237 — Executable Course Reader (v0.8)

This project merges **slides**, **handwritten notes**, **homeworks**, and **finals** into a navigable discourse **and** an executable quant library.

**Two outputs** are produced:

1. **HTML reader** (MkDocs site): `build/site/index.html`
2. **PDF reader** (ReportLab fallback): `build/Stats237_Reader.pdf`

## One-command build

- macOS/Linux: `./run_all.sh`
- Windows: `./run_all.ps1`

That runs:
- ingestion (if you placed materials in `inputs/`)
- problem bank + coverage matrix
- unit tests
- book build (HTML + PDF)

## Materials

Place PDFs/ZIPs in `inputs/` and rerun `run_all`.

The reader pages link to generated indices:
- **Materials Index** (what you provided)
- **Function Index** (what the quant library exposes)
