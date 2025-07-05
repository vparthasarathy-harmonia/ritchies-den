# run_solicitation_tagging.py

import os
import json
import sys
import argparse
from dotenv import load_dotenv
from pathlib import Path
from rag.project_paths import (
    get_s3_prefix, get_local_folder,
    get_eval_criteria_path, get_tagged_chunks_path,
    get_capture_json_path
)
from rag.pipeline_utils import (
    list_s3_files, download_s3_file,
    list_local_files, load_documents,
    chunk_documents
)
from rag.solicitation_tagging import (
    tag_expectation_identifier,
    tag_eval_criteria_chunks,
    tag_win_theme_mapper
)
from rag.extract_capture_themes import parse_all_capture_files, save_capture_json

load_dotenv(dotenv_path=".env.local")

parser = argparse.ArgumentParser()
parser.add_argument("portfolio", help="Portfolio name")
parser.add_argument("opportunity", help="Opportunity name")
parser.add_argument("--force-capture", action="store_true", help="Force reprocessing of capture files")
args = parser.parse_args()

portfolio = args.portfolio
opportunity = args.opportunity
force_capture = args.force_capture

bucket = os.getenv("S3_BUCKET")
s3_prefix = get_s3_prefix(portfolio, opportunity)
local_folder = get_local_folder(portfolio, opportunity)

# Step 1: Download solicitation files
print(f"\n🔍 Checking S3 for files in: {s3_prefix}")
s3_keys = list_s3_files(bucket, prefix=s3_prefix)
for key in s3_keys:
    filename = key.split("/")[-1]
    download_s3_file(bucket, key, os.path.join(local_folder, filename))

# Step 2: Load and chunk (exclude capture files)
print("\n📄 Loading and chunking documents...")
file_paths = [
    path for path in list_local_files(local_folder)
    if not Path(path).name.lower().startswith("capture")
]
docs = load_documents(file_paths)
chunks = chunk_documents(docs, opportunity_name=opportunity)
print(f"✅ Chunked {len(chunks)} chunks")

# Step 3: Tag expectation and evaluation criteria
print("\n🤖 Tagging: Expectation Identifier...")
tagged_chunks = tag_expectation_identifier(chunks)

print("\n🔍 Tagging: Evaluation Criteria Identifier...")
tagged_chunks = tag_eval_criteria_chunks(tagged_chunks)

criteria_chunks = [
    {"chunk_id": c["chunk_id"], "text": c["text"]}
    for c in tagged_chunks
    if c["metadata"]["agent_tags"].get("eval_criteria_identifier", 0.0) >= 0.7
]
criteria_text = "\n\n".join([c["text"] for c in criteria_chunks])

# Step 3.5: Save evaluation criteria chunks
eval_criteria_path = get_eval_criteria_path(portfolio, opportunity)
os.makedirs(os.path.dirname(eval_criteria_path), exist_ok=True)
with open(eval_criteria_path, "w", encoding="utf-8") as f:
    json.dump({"criteria_chunks": criteria_chunks}, f, indent=2)
print(f"📂 Evaluation criteria saved to: {eval_criteria_path}")

# Step 4: Load or generate capture_parsed.json
capture_path = get_capture_json_path(portfolio, opportunity)
if force_capture or not os.path.exists(capture_path):
    print("\n🔄 Generating capture_parsed.json...")
    capture_data = parse_all_capture_files(local_folder)
    if capture_data:
        save_capture_json(capture_data, capture_path)
    else:
        capture_data = {}
else:
    with open(capture_path, "r", encoding="utf-8") as f:
        capture_data = json.load(f)
    print("📖 Loaded structured capture data.")

# Step 5: Run win theme mapper
if capture_data:
    print("\n🏷️ Tagging: Win Theme Mapper with structured capture context...")
    tagged_chunks = tag_win_theme_mapper(tagged_chunks, capture_data, criteria_text)
else:
    print("⚠️ No capture data available — skipping win theme mapping.")

# Step 6: Save tagged output
output_path = get_tagged_chunks_path(portfolio, opportunity)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(tagged_chunks, f, indent=2)

print(f"\n✅ Tagged chunks saved to: {output_path}")
print(f"🧱 Example tags: {tagged_chunks[0]['metadata']['agent_tags']}")
