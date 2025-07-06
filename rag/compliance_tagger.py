# rag/compliance_tagger.py — Extracts compliance requirements

import json
import time
from pathlib import Path
from rag.llm_client_claude import invoke_claude

def tag_compliance_chunks(chunks):
    response_compliance = []
    performance_compliance = []
    MAX_CHARS = 3000
    OVERLAP = 200

    for i, chunk in enumerate(chunks):
        chunk_text = chunk.get("text", "")
        chunk_id = chunk.get("chunk_id")
        source = chunk.get("metadata", {}).get("source_document", "unknown")

        start = 0
        while start < len(chunk_text):
            end = min(start + MAX_CHARS, len(chunk_text))
            sub_text = chunk_text[start:end]
            print(f"📏 Sub-chunk from {start} to {end} (len={len(sub_text)})")

            prompt_template = """
You are a compliance auditor helping extract mandatory requirements from a government solicitation.

Given the following solicitation excerpt, identify:
1. Proposal Response Compliance (formatting, submission instructions, page limits, etc.)
2. Project Performance Compliance (anything the contractor must do post-award: SLAs, standards, deliverables, etc.)

Return two lists of JSON objects, each with:
- type: one-word category (e.g., "formatting", "sla", "security", "submission")
- requirement: short plain-English statement of what's required
- source: cite this as "{source}"

---
{text}
---

Respond with this JSON format:
{{
  "proposal_response": [...],
  "project_performance": [...]
}}
Only return valid JSON.
"""
            prompt = prompt_template.format(source=source, text=sub_text)

            try:
                print(f"⏳ [compliance_tagger] Sending chunk {chunk_id} to Claude...")
                result_text = invoke_claude(prompt)
                print("✅ Response received")
                parsed = json.loads(result_text[result_text.find("{"):])

                for item in parsed.get("proposal_response", []):
                    item["source"] = source
                    item["chunk_id"] = chunk_id
                    response_compliance.append(item)

                for item in parsed.get("project_performance", []):
                    item["source"] = source
                    item["chunk_id"] = chunk_id
                    performance_compliance.append(item)

            except Exception as e:
                print(f"⚠️ Error parsing compliance from chunk {chunk_id}: {e}")
                break

            if end == len(chunk_text):
                break
            start = end - OVERLAP if end - OVERLAP > start else end
            time.sleep(0.5 if i % 2 == 0 else 1.0)

    return response_compliance, performance_compliance

if __name__ == "__main__":
    import sys
    portfolio = sys.argv[1]
    opportunity = sys.argv[2]
    base = f"data/{portfolio}/opportunities/{opportunity}"
    chunk_path = f"{base}/tagged_chunks.json"
    out_response = f"{base}/compliance_response.json"
    out_performance = f"{base}/compliance_performance.json"

    with open(chunk_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"📂 Running compliance tagger for {portfolio}/{opportunity}...")
    r_comp, p_comp = tag_compliance_chunks(chunks)

    Path(base).mkdir(parents=True, exist_ok=True)
    with open(out_response, "w", encoding="utf-8") as f:
        json.dump(r_comp, f, indent=2)
    with open(out_performance, "w", encoding="utf-8") as f:
        json.dump(p_comp, f, indent=2)

    print(f"✅ Extracted {len(r_comp)} proposal compliance and {len(p_comp)} performance compliance requirements.")
    print(f"📄 Saved to: {out_response} and {out_performance}")
