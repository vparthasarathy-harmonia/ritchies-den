# rag/pp_matcher.py — tag solicitation chunks with relevant past performance references

import json
import os
from pathlib import Path
from rag.llm_client_claude import invoke_claude


def tag_chunks_with_pp(chunks, past_perf_projects):
    tagged_chunks = []

    for chunk in chunks:
        relevant_projects = []
        chunk_text = chunk["text"]

        for project in past_perf_projects:
            # Safe extraction of project_name
            cid = project.get("contract_identification")
            project_name = None

            if isinstance(cid, dict):
                project_name = cid.get("program_title") or \
                               cid.get("contract_name") or \
                               cid.get("project_name")

            if not project_name:
                project_name = project.get("sources", ["Unnamed Project"])[0]

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
                print(f"⚠️ Skipping project '{project_name}' due to error: {e}")
                continue

        if relevant_projects:
            chunk.setdefault("metadata", {}).setdefault("agent_tags", {})["pp_matcher"] = relevant_projects

        tagged_chunks.append(chunk)

    return tagged_chunks


if __name__ == "__main__":
    opportunity = "VALGY"
    base_path = f"data/opportunities/{opportunity}"
    chunk_path = os.path.join(base_path, "tagged_chunks.json")
    pp_json_path = os.path.join(base_path, "past_perf_projects.json")

    with open(chunk_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(pp_json_path, "r", encoding="utf-8") as f:
        past_perf_projects = json.load(f)

    print(f"🔍 Tagging {len(chunks)} chunks using {len(past_perf_projects)} past performance projects...")
    tagged = tag_chunks_with_pp(chunks, past_perf_projects)

    with open(chunk_path, "w", encoding="utf-8") as f:
        json.dump(tagged, f, indent=2)

    print(f"✅ pp_matcher tags added to {chunk_path}")
