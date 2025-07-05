# rag/preparse_solicitation.py

import os
import re
import json
from pathlib import Path
from typing import List, Dict

SECTION_REGEX = re.compile(r"^(\d{1,2}(\.\d{1,2})*)\s+(.+)")


def extract_toc_and_sections(text: str) -> Dict:
    lines = text.splitlines()
    toc = []
    sections = []
    current_page = 1
    seen_headings = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = SECTION_REGEX.match(line)
        if match:
            heading_id = match.group(1)
            heading_text = match.group(3).strip()
            full_heading = f"{heading_id} {heading_text}"

            if full_heading not in seen_headings:
                toc.append(full_heading)
                sections.append({"id": heading_id, "heading": full_heading, "page": current_page})
                seen_headings.add(full_heading)

        if "page" in line.lower():
            page_match = re.search(r"page\s*(\d+)", line.lower())
            if page_match:
                current_page = int(page_match.group(1))

    return {
        "toc": toc,
        "sections": sections
    }


def save_parsed_context(parsed: Dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)
    print(f"✅ Saved parsed context to: {output_path}")


def inject_breadcrumbs(chunk: str, section_info: Dict, page: int) -> str:
    breadcrumb = f"Breadcrumb: {section_info.get('heading', 'Unknown Section')} > Page {page}\n\n"
    return breadcrumb + chunk


# Optional: If you're chunking separately and need to enrich chunks with breadcrumbs
def enrich_chunks_with_breadcrumbs(chunks: List[Dict], section_map: Dict[str, Dict]) -> List[Dict]:
    enriched = []
    for chunk in chunks:
        section_id = chunk.get("section_id")  # assumes chunk carries its section ID like "4.2"
        page = chunk.get("page", 0)
        section_info = section_map.get(section_id, {"heading": "Unknown"})
        chunk["text"] = inject_breadcrumbs(chunk["text"], section_info, page)
        enriched.append(chunk)
    return enriched


# Entry point for integration (optional CLI use)
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python -m rag.preparse_solicitation <portfolio> <opportunity> <text_file>")
        sys.exit(1)

    portfolio, opportunity, input_txt = sys.argv[1:4]
    with open(input_txt, "r", encoding="utf-8") as f:
        text = f.read()

    parsed = extract_toc_and_sections(text)
    output_path = f"data/{portfolio}/opportunities/{opportunity}/parsed_context.json"
    save_parsed_context(parsed, output_path)
