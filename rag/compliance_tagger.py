# rag/compliance_tagger.py — rebuilt version

import json
import time
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

        print(f"\n🔍 [compliance_tagger] Processing chunk {chunk_id} ({i+1}/{len(chunks)})")

        start = 0
        while start < len(chunk_text):
            end = min(start + MAX_CHARS, len(chunk_text))
            sub_text = chunk_text[start:end]

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
                print("⏳ Sending to Claude...")
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
                print(f"⚠️ Error on chunk {chunk_id}: {e}")
                break

            if end == len(chunk_text):
                break
            start = end - OVERLAP
            time.sleep(0.5 if i % 2 == 0 else 1.0)

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
                print("⏳ Sending to Claude...")
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
                print(f"⚠️ Error on chunk {chunk_id}: {e}")
                continue

            time.sleep(0.5 if i % 2 == 0 else 1.0)  # alternate pacing

    return response_compliance, performance_compliance
