# rag/past_perf_utils.py

import json
from rag.llm_client_claude import invoke_claude

def extract_project_metadata(full_text, filename):
    print(f"📏 full_text length: {len(full_text)}")
    from rag.pipeline_utils import hierarchical_chunk
    chunks = hierarchical_chunk(full_text, max_chunk_size=3000)

    merged_metadata = {}

    for i, chunk in enumerate(chunks):
        prompt = f"""
You are extracting structured metadata about a past performance project from a proposal document.

Return a JSON object with the following keys:
- period_of_performance
- contract_identification
- client_and_agency
- scope_and_work_type
- financials_and_labor
- teaming_and_delivery
- performance_and_quality
- compliance_and_standards
- contract_strategy

If anything is unknown, use null or an empty list. Only return valid JSON.
The filename is: {filename}

---
{chunk}
---
"""
        try:
            print(f"🧠 Sending chunk {i+1}/{len(chunks)} to Claude...")
            response = invoke_claude(prompt)
            print("✅ Response received")
            json_start = response.find("{")
            result = json.loads(response[json_start:].strip())
            result["sources"] = [filename]
            merged_metadata = merge_projects(merged_metadata, result) if merged_metadata else result
        except Exception as e:
            print(f"❌ Error in chunk {i+1} for {filename}: {e}")
            continue

    return merged_metadata if merged_metadata else None

def merge_projects(existing, new):
    def safe_merge_dicts(a, b):
        if not isinstance(a, dict): a = {}
        if not isinstance(b, dict): b = {}
        return {**a, **b}

    def safe_merge_lists(a, b):
        if not isinstance(a, list): a = []
        if not isinstance(b, list): b = []
        return list(set(a + b))

    existing["sources"] = safe_merge_lists(existing.get("sources"), new.get("sources"))

    for key in new:
        if key == "sources":
            continue

        new_val = new[key]
        existing_val = existing.get(key)

        if isinstance(new_val, dict):
            existing[key] = safe_merge_dicts(existing_val, new_val)
        elif isinstance(new_val, list):
            existing[key] = safe_merge_lists(existing_val, new_val)
        elif isinstance(new_val, str):
            if not existing_val:
                existing[key] = new_val
        elif new_val is not None:
            existing[key] = new_val

    return existing

def infer_project_name(cid: dict, filename: str) -> str:
    if not isinstance(cid, dict):
        print(f"⚠️ contract_identification is not a dict in {filename}, skipping...")
        return filename.split(".")[0]
    for alt_key in ["project_name", "contract_name", "program_title", "reference_name", "name"]:
        pname = cid.get(alt_key)
        if pname and isinstance(pname, str) and len(pname.strip()) > 3:
            return pname.strip()
    return filename.split(".")[0]  # fallback to base filename
