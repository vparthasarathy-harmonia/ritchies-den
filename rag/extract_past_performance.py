# rag/extract_past_performance.py

import os
import json
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

from rag.project_paths import get_past_perf_json_path, get_s3_prefix
from rag.pipeline_utils import list_s3_files, download_s3_file, list_local_files, load_documents
from rag.past_perf_utils import extract_project_metadata, infer_project_name, merge_projects

load_dotenv(dotenv_path=".env.local")

def run_past_perf_extraction(portfolio: str, opportunity: str):
    print(f"\n📂 Extracting past performance for {portfolio}/{opportunity}")

    bucket = os.getenv("S3_BUCKET")
    pp_folder = f"data/{portfolio}/opportunities/{opportunity}/past_performance/"
    pp_output_path = get_past_perf_json_path(portfolio, opportunity)

    # Download files from S3 (if present)
    pp_s3_prefix = get_s3_prefix(portfolio, opportunity, subfolder="past_performance")
    pp_keys = list_s3_files(bucket, prefix=pp_s3_prefix)
    for key in pp_keys:
        filename = key.split("/")[-1]
        dest_path = os.path.join(pp_folder, filename)
        download_s3_file(bucket, key, dest_path)

    # Load documents
    docs = load_documents(list_local_files(pp_folder))
    projects_by_name = {}

    for i, doc in enumerate(docs):
        fname = Path(doc.metadata.get("source", "unknown")).name
        print(f"\n   🔄 [{i+1}/{len(docs)}] Processing {fname}...")
        try:
            t0 = time.time()
            metadata = extract_project_metadata(doc.page_content, fname)
            t1 = time.time()
            print(f"      ⏱️ Done in {round(t1 - t0, 2)}s")
        except Exception as e:
            print(f"      ❌ Error extracting metadata from {fname}: {e}")
            continue

        if not metadata:
            print(f"      ⚠️ No metadata returned for {fname}")
            continue

        cid = metadata.get("contract_identification")
        if not cid:
            print(f"      ⚠️ No contract_identification in {fname}")
            continue

        pname = infer_project_name(cid, fname)
        key = pname.strip().lower()
        projects_by_name[key] = merge_projects(projects_by_name.get(key, {}), metadata)

    # Save final output
    os.makedirs(os.path.dirname(pp_output_path), exist_ok=True)
    with open(pp_output_path, "w", encoding="utf-8") as f:
        json.dump(list(projects_by_name.values()), f, indent=2)

    print(f"\n✅ Saved structured past performance to: {pp_output_path}")

# CLI usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m rag.extract_past_performance <portfolio> <opportunity>")
        sys.exit(1)

    run_past_perf_extraction(sys.argv[1], sys.argv[2])
