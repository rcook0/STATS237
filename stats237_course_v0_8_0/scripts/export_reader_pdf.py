"""PDF export fallback using ReportLab.

This is intentionally dependency-light: it converts a subset of Markdown to a readable PDF.
Primary publishing target remains the MkDocs HTML site (research-grade navigation + notebooks).

Output: build/Stats237_Reader.pdf
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Preformatted, PageBreak

ROOT = Path(__file__).resolve().parents[1]
BOOK_DOCS = ROOT / "book" / "docs"
OUT = ROOT / "build" / "Stats237_Reader.pdf"


def md_to_flowables(md: str):
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], leading=14)
    code_style = ParagraphStyle("code", parent=styles["Code"], leading=11)

    flow = []

    lines = md.splitlines()
    in_code = False
    code_buf = []

    def flush_para(buf):
        txt = "\n".join(buf).strip()
        if not txt:
            return
        # basic escaping
        txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        flow.append(Paragraph(txt, body))
        flow.append(Spacer(1, 8))

    para_buf = []

    for ln in lines:
        if ln.strip().startswith("```"):
            if not in_code:
                flush_para(para_buf)
                para_buf = []
                in_code = True
                code_buf = []
            else:
                in_code = False
                flow.append(Preformatted("\n".join(code_buf), code_style))
                flow.append(Spacer(1, 10))
            continue

        if in_code:
            code_buf.append(ln)
            continue

        m1 = re.match(r"^#\s+(.*)", ln)
        m2 = re.match(r"^##\s+(.*)", ln)
        if m1:
            flush_para(para_buf)
            para_buf = []
            flow.append(Paragraph(m1.group(1), h1))
            flow.append(Spacer(1, 10))
            continue
        if m2:
            flush_para(para_buf)
            para_buf = []
            flow.append(Paragraph(m2.group(1), h2))
            flow.append(Spacer(1, 8))
            continue

        if ln.strip() == "":
            flush_para(para_buf)
            para_buf = []
        else:
            # bullets: keep simple
            if ln.lstrip().startswith("- "):
                flush_para(para_buf)
                para_buf = []
                bullet = ln.lstrip()[2:]
                bullet = bullet.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                flow.append(Paragraph(f"• {bullet}", body))
                flow.append(Spacer(1, 4))
            else:
                para_buf.append(ln)

    flush_para(para_buf)
    return flow


def main() -> None:
    parts = []

    # Prefer the synced book docs if present
    for rel in [
        "index.md",
        "course_story.md",
        "chapters/index.md",
        "chapters/01_probability.md",
        "chapters/02_no_arb.md",
        "chapters/03_binomial.md",
        "chapters/04_black_scholes.md",
        "chapters/05_mc_vr.md",
        "api.md",
        "reproducibility.md",
        "_generated/materials_index.md",
        "_generated/function_index.md",
    ]:
        p = BOOK_DOCS / rel
        if p.exists():
            parts.append((rel, p.read_text(encoding="utf-8")))

    doc = SimpleDocTemplate(str(OUT), pagesize=letter, title="Stats237 Reader")
    story = []
    for i, (name, md) in enumerate(parts):
        story += md_to_flowables(md)
        if i != len(parts) - 1:
            story.append(PageBreak())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)


if __name__ == "__main__":
    main()
