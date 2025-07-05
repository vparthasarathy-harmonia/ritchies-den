# rag/extract_past_performance.py

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from rag.project_paths import get_portfolio_past_perf_folder, get_past_perf_json_path
from rag.pipeline_utils import list_local_files, load_documents
from rag.llm_client_claude import invoke_claude

load_dotenv(dotenv_path=".env.local")

CHUNK_SIZE = 3000
OVERLAP = 200

def extract_project_metadata(full_text, filename):
    chunks = []
    start = 0
    while start < len(full_text):
        end = min(start + CHUNK_SIZE, len(full_text))
        chunks.append(full_text[start:end])
        start = end - OVERLAP  # allow some overlap

    merged_metadata = {}
    for i, chunk in enumerate(chunks):
        prompt = f"""
You are extracting structured metadata about a past performance project from a proposal document.
Return a JSON object with the following structure, including all nested sections and fields:

Include an additional field `period_of_performance` at the top level, with values like "Oct 2021 – Sep 2023".

{chunk}

---

Required top-level keys:
- period_of_performance (string)
- contract_identification
- client_and_agency
- scope_and_work_type
- financials_and_labor
- teaming_and_delivery
- performance_and_quality
- compliance_and_standards
- contract_strategy

Each section should include details such as: technologies used, delivery model, delivery locations, project headcount, resource roles, performance metrics, uptime %, sprint velocity, SLA adherence, compliance levels, etc.

Include the source filename under `sources` as a list.
If any section or field is unknown, use null, 0, false, or an empty list as appropriate.
Return only a valid JSON object.
"""
        try:
            response = invoke_claude(prompt)
            print(f"\n📄 [Chunk {i+1}] Metadata from {filename}:\n{response[:300]}...")
            json_start = response.find("{")
            result = json.loads(response[json_start:].strip())
            result["sources"] = [filename]
            merged_metadata = merge_projects(merged_metadata, result) if merged_metadata else result
        except Exception as e:
            print(f"❌ Error in chunk {i+1} of {filename}: {e}")
            continue

    return merged_metadata if merged_metadata else None

def merge_projects(existing, new):
    existing["sources"] = list(set(existing.get("sources", []) + new.get("sources", [])))
    for key in new:
        if key == "sources":
            continue
        if isinstance(new[key], dict):
            existing[key] = {**new[key], **existing.get(key, {})}
        elif isinstance(new[key], list):
            existing[key] = list(set(existing.get(key, []) + new[key]))
        else:
            if not existing.get(key):
                existing[key] = new[key]
    return existing

def infer_project_name(cid: dict, filename: str) -> str:
    for alt_key in ["project_name", "contract_name", "program_title", "reference_name", "name"]:
        pname = cid.get(alt_key)
        if pname and isinstance(pname, str) and len(pname.strip()) > 3:
            return pname.strip()
    return filename.split(".")[0]  # fallback to base filename

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_past_performance.py <portfolio> <opportunity>")
        sys.exit(1)

    portfolio = sys.argv[1]
    opportunity = sys.argv[2]

    folder = get_portfolio_past_perf_folder(portfolio)
    output_path = get_past_perf_json_path(portfolio, opportunity)

    print(f"\n📂 Loading past performance documents from: {folder}")
    supported_exts = (".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".rtf")
    file_paths = list_local_files(folder, extensions=supported_exts)
    docs = load_documents(file_paths)

    projects_by_name = {}

    for doc in docs:
        filename = Path(doc.metadata.get("source", "unknown")).name
        metadata = extract_project_metadata(doc.page_content, filename)

        if not metadata:
            print(f"⚠️ Skipping {filename}: no metadata returned")
            continue

        cid = metadata.get("contract_identification")
        if not cid or not isinstance(cid, dict):
            print(f"⚠️ Skipping {filename}: invalid or missing contract_identification")
            continue

        pname = infer_project_name(cid, filename)
        if not pname:
            print(f"⚠️ Skipping {filename}: could not infer project name")
            continue

        key = pname.strip().lower()
        if key in projects_by_name:
            projects_by_name[key] = merge_projects(projects_by_name[key], metadata)
        else:
            projects_by_name[key] = metadata

    all_projects = list(projects_by_name.values())
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_projects, f, indent=2)

    print(f"\n✅ Aggregated project metadata saved → {output_path}")
