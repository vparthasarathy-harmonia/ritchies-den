# tag_past_performance.py (patched: robust JSON parsing with regex fallback)

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from rag.project_paths import (
    get_past_perf_folder, get_past_perf_json_path, get_s3_past_perf_prefix
)
from rag.pipeline_utils import list_local_files, list_s3_files, download_s3_file
from rag.llm_client_claude import invoke_claude

load_dotenv(dotenv_path=".env.local")

portfolio = sys.argv[1]
opportunity = sys.argv[2]

bucket = os.getenv("S3_BUCKET")
s3_prefix = get_s3_past_perf_prefix(portfolio, opportunity)
local_folder = get_past_perf_folder(portfolio, opportunity)

# Step 1: Download past performance files from S3
print(f"📦 Syncing past performance files from S3: {s3_prefix}")
os.makedirs(local_folder, exist_ok=True)
s3_keys = list_s3_files(bucket, s3_prefix)
for key in s3_keys:
    filename = key.split("/")[-1]
    download_s3_file(bucket, key, os.path.join(local_folder, filename))

# Step 2: Parse each document and extract metadata
print("🔍 Parsing past performance documents for structured metadata...")
files = list_local_files(local_folder)
projects = []

def extract_json_from_response(response: str) -> dict:
    try:
        json_start = response.find("{")
        json_like = response[json_start:]
        match = re.search(r"\{.*\}", json_like, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            raise ValueError("No valid JSON object found.")
    except Exception as e:
        print(f"❌ JSON parsing error: {e}")
        return None

for path in files:
    try:
        print(f"📄 Extracting: {path}")
        with open(path, "rb") as f:
            content = f.read()
        prompt = f"""
You are a government contract analyst. Extract key past performance information from the following document:

File: {Path(path).name}

Return JSON with fields:
- contract_identification
- client_and_agency
- scope_and_work_type
- period_of_performance
- financials_and_labor

Respond in pure JSON only.
"""
        response = invoke_claude(prompt + "\n\nTEXT:\n" + content.decode("utf-8", errors="ignore")[:7000])
        project_data = extract_json_from_response(response)
        if project_data:
            project_data["sources"] = [Path(path).name]
            projects.append(project_data)
        else:
            print(f"⚠️ Skipping file due to bad JSON: {path}")
    except Exception as e:
        print(f"❌ Failed to extract {path}: {e}")

# Step 3: Save output
output_path = get_past_perf_json_path(portfolio, opportunity)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(projects, f, indent=2)
print(f"✅ Saved past performance metadata to: {output_path}")
