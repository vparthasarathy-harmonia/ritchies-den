# ritchies-den/rag/tag_past_performance.py — now aggregates by project

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from rag.rag_pipeline import list_local_files, load_documents
from rag.llm_client import invoke_claude

load_dotenv(dotenv_path=".env.local")


def extract_project_metadata(doc_text, filename):
    prompt = f"""
You are extracting structured metadata about a past performance project from a proposal document.
Return a JSON object with the following structure, including all nested sections and fields:

Include an additional field `period_of_performance` at the top level, with values like "Oct 2021 – Sep 2023".

{doc_text[:3000]}

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
        print(f"\n📄 [Project Metadata Extracted from {filename}]\n{response[:300]}...")
        start = response.find("{")
        json_part = response[start:].strip()
        parsed = json.loads(json_part)
        parsed["sources"] = [filename]  # track original file
        return parsed
    except Exception as e:
        print(f"❌ Error extracting metadata from {filename}: {e}")
        return None


def merge_projects(existing, new):
    # Merge flat and nested project metadata
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
    opportunity = "VALGY"
    folder = f"data/opportunities/{opportunity}/past_performance/"
    output_path = f"data/opportunities/{opportunity}/past_perf_projects.json"

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
