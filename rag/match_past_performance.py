# rag/match_past_performance.py

import json
import os
import sys
from rag.project_paths import get_tagged_chunks_path, get_past_perf_json_path
from rag.llm_client_claude import invoke_claude

def tag_chunks_with_pp(chunks, past_perf_projects):
    tagged_chunks = []

    for chunk in chunks:
        relevant_projects = []
        chunk_text = chunk["text"]

        for project in past_perf_projects:
            project_name = project.get("contract_identification", {}).get("program_title") or \
                           project.get("contract_identification", {}).get("contract_name") or \
                           project.get("contract_identification", {}).get("name") or \
                           "Unnamed Project"

            prompt = f"""
You are a past performance relevance assessor.

A proposal chunk is shown below. Determine whether the chunk is relevant to the past performance project described.
Return a JSON object with these fields:
- relevant: true | false
- confidence: float between 0 and 1
- matched_fields: list of matching themes or fields from the past performance

---
Chunk:
{chunk_text[:2500]}

---
Project Metadata:
{json.dumps(project)[:2500]}

Return only a JSON object.
"""
            try:
                response = invoke_claude(prompt)
                result = json.loads(response[response.find("{"):])
                if result.get("relevant"):
                    relevant_projects.append({
                        "project_name": project_name,
                        "source": project.get("sources", ["unknown"])[0],
                        "confidence": result.get("confidence", 0),
                        "matched_fields": result.get("matched_fields", [])
                    })
            except Exception as e:
                print(f"⚠️ Skipping project due to error: {e}")
                continue

        if relevant_projects:
            chunk["metadata"].setdefault("agent_tags", {})["pp_matcher"] = relevant_projects

        tagged_chunks.append(chunk)

    return tagged_chunks

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python match_past_performance.py <portfolio> <opportunity>")
        sys.exit(1)

    portfolio = sys.argv[1]
    opportunity = sys.argv[2]

    chunk_path = get_tagged_chunks_path(portfolio, opportunity)
    pp_json_path = get_past_perf_json_path(portfolio, opportunity)

    with open(chunk_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(pp_json_path, "r", encoding="utf-8") as f:
        past_perf_projects = json.load(f)

    print(f"🔍 Tagging {len(chunks)} chunks using {len(past_perf_projects)} past performance projects...")
    tagged = tag_chunks_with_pp(chunks, past_perf_projects)

    with open(chunk_path, "w", encoding="utf-8") as f:
        json.dump(tagged, f, indent=2)

    print(f"✅ Past performance tags added to {chunk_path}")
