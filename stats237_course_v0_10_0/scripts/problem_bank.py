#!/usr/bin/env python3
"""
Build a problem bank from extracted text JSONs (typically HW + finals).

Heuristics:
- split on lines matching 'Problem', 'Exercise', 'Question'
- fallback: split on numbered headings when density suggests problem statements
"""
from __future__ import annotations
from pathlib import Path
import json, re, datetime
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
TEXTDIR = ROOT / "materials" / "text"
OUT = ROOT / "problem_bank" / "problems.json"

SPLIT_RX = re.compile(r"(?im)^(problem|exercise|question)\s*\d+[\:\.\)]\s*")
NUM_RX = re.compile(r"(?m)^\s*(\d{1,2})\s*[\.\)]\s+")

def tag(text: str) -> List[str]:
    t = text.lower()
    tags = set()
    if "conditional expectation" in t or "tower" in t or "given" in t:
        tags.add("conditional_expectation")
    if "binomial" in t or "crr" in t or "u=" in t and "d=" in t:
        tags.add("binomial")
    if "black-scholes" in t or "black scholes" in t or "d1" in t or "d2" in t:
        tags.add("black_scholes")
    if "monte carlo" in t or "simulation" in t or "variance" in t:
        tags.add("monte_carlo")
    if "basket" in t:
        tags.add("basket")
    if "asian" in t:
        tags.add("asian")
    if "put-call" in t or "parity" in t:
        tags.add("no_arb")
    return sorted(tags)

def chunk_text(pages: List[Dict[str, Any]]) -> str:
    # join with page separators
    parts=[]
    for p in pages:
        parts.append(f"\n\n--- PAGE {p['page_index']+1} ---\n")
        parts.append(p.get("text",""))
    return "".join(parts)

def split_problems(fulltext: str) -> List[Tuple[str, str, int, int]]:
    # returns list of (title, body, start_pos, end_pos) in character indices
    matches=list(SPLIT_RX.finditer(fulltext))
    if not matches:
        # fallback: use numbered headings at start of lines if plentiful
        nums=list(NUM_RX.finditer(fulltext))
        if len(nums) < 5:
            return []
        # treat each numbered heading as a problem start
        matches=nums
    spans=[]
    for i, m in enumerate(matches):
        start=m.start()
        end=matches[i+1].start() if i+1 < len(matches) else len(fulltext)
        header=fulltext[m.start():m.end()].strip()
        body=fulltext[m.end():end].strip()
        spans.append((header, body, start, end))
    return spans

def guess_page_range(fulltext: str, start_pos: int, end_pos: int) -> Tuple[int|None,int|None]:
    # naive: search PAGE markers within span
    seg = fulltext[start_pos:end_pos]
    pages = re.findall(r"--- PAGE (\d+) ---", seg)
    if not pages:
        return None, None
    pnums = [int(x) for x in pages]
    return min(pnums), max(pnums)

def main() -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    problems=[]
    for jpath in sorted(TEXTDIR.glob("*.json")):
        doc=json.loads(jpath.read_text())
        if doc["kind"] not in ["hw","final","handout","slides","unknown"]:
            continue
        # Only hw/final/handout are likely; slides sometimes have exercises
        full=chunk_text(doc["pages"])
        spans=split_problems(full)
        for idx,(hdr, body, s, e) in enumerate(spans, start=1):
            pstart, pend = guess_page_range(full, s, e)
            text = (hdr + "\n" + body).strip()
            prob_id = f"{doc['kind']}-{doc['material_id']}-{idx:03d}"
            problems.append({
                "id": prob_id,
                "material_id": doc["material_id"],
                "source_filename": doc["filename"],
                "source_kind": doc["kind"],
                "page_start": pstart,
                "page_end": pend,
                "header": hdr,
                "tags": tag(text),
                "text": text[:4000],  # cap for portability
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": now, "problems": problems}, indent=2))
    print(f"Wrote {OUT} ({len(problems)} problems)")

if __name__ == "__main__":
    main()
