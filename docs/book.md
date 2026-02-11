# v0.8 Book Build

The **HTML reader** is built with MkDocs using `book/mkdocs.yml`.

Generated pages are written into `book/docs/_generated/`:
- materials index from `registry/materials_registry.json`
- function index by importing `stats237_quantlib`

## Commands

```bash
python scripts/build_chapter_registry.py
python scripts/build_book.py
mkdocs -f book/mkdocs.yml build
python scripts/export_reader_pdf.py
```

The PDF export is a **dependency-light fallback** that converts a subset of Markdown into a single printable document.
The primary reader remains the HTML site.
