"""
run_solicitation_analysis.py — End-to-End Orchestrator for Phase 1: Solicitation Analysis

Steps included:
1. Download files from S3
2. Chunk solicitation documents (excluding capture)
3. Parse document structure (TOC, sections) and enrich chunks with breadcrumbs
4. Parse capture documents and build grouped win themes, pain points, differentiators
5. Run tagging agents:
   - Expectation Identifier
   - Evaluation Criteria Identifier
   - Win Theme Mapper
6. Extract past performance metadata
7. Match past performance to solicitation chunks
8. [Placeholder] Coverage gap analysis (based on TOC vs tagged chunks)
9. [Placeholder] Compliance checklist extraction
10. [Placeholder] Risk identification
11. [Placeholder] Tone & style profiling
12. [Placeholder] Scoring rubric mapping
13. [Placeholder] Keyword/theme frequency analysis
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# === Load utility modules ===
from rag.project_paths import (
    get_s3_prefix, get_local_folder, get_eval_criteria_path,
    get_tagged_chunks_path, get_capture_json_path, get_past_perf_json_path
)
from rag.pipeline_utils import (
    list_s3_files, download_s3_file, list_local_files,
    load_documents, chunk_documents
)
from rag.solicitation_tagging import (
    tag_expectation_identifier, tag_eval_criteria_chunks, tag_win_theme_mapper
)
from rag.extract_capture_themes import parse_all_capture_files, save_capture_json
from rag.preparse_solicitation import extract_toc_and_sections, save_parsed_context, enrich_chunks_with_breadcrumbs
from rag.extract_past_performance import extract_project_metadata, infer_project_name, merge_projects
from rag.match_past_performance import tag_chunks_with_pp

load_dotenv(dotenv_path=".env.local")

parser = argparse.ArgumentParser()
parser.add_argument("portfolio")
parser.add_argument("opportunity")
parser.add_argument("--force-capture", action="store_true")
parser.add_argument("--test-limit", type=int, default=None)
args = parser.parse_args()

portfolio = args.portfolio
opportunity = args.opportunity
local_folder = get_local_folder(portfolio, opportunity)
s3_prefix = get_s3_prefix(portfolio, opportunity)
bucket = os.getenv("S3_BUCKET")

# === Step 1: Download files ===
print(f"🗓️ Downloading S3 files for {portfolio}/{opportunity} ...")
s3_keys = list_s3_files(bucket, prefix=s3_prefix)
for key in s3_keys:
    filename = key.split("/")[-1]
    download_s3_file(bucket, key, os.path.join(local_folder, filename))

# === Step 2: Chunk solicitation documents (excluding capture) ===
print("\n📄 Loading and chunking solicitation documents...")
file_paths = [p for p in list_local_files(local_folder) if not Path(p).name.lower().startswith("capture")]
docs = load_documents(file_paths)
chunks = chunk_documents(docs, opportunity_name=opportunity)

# === Step 3: Parse document structure & enrich chunks ===
print("\n📚 Extracting TOC/sections and enriching chunks with breadcrumbs...")
full_text = "\n\n".join([doc.page_content for doc in docs])
parsed_context = extract_toc_and_sections(full_text)
parsed_context_path = f"data/{portfolio}/opportunities/{opportunity}/parsed_context.json"
save_parsed_context(parsed_context, parsed_context_path)
section_map = {s["id"]: s for s in parsed_context["sections"] if "id" in s}
chunks = enrich_chunks_with_breadcrumbs(chunks, section_map)
if args.test_limit:
    chunks = chunks[:args.test_limit]

# === Step 4: Parse capture files ===
print("\n🎯 Parsing capture files...")
capture_path = get_capture_json_path(portfolio, opportunity)
if args.force_capture or not os.path.exists(capture_path):
    capture_data = parse_all_capture_files(local_folder)
    save_capture_json(capture_data, capture_path)
else:
    with open(capture_path, "r", encoding="utf-8") as f:
        capture_data = json.load(f)

grouped_capture_data = {
    "pain_points": [c["text"] for c in capture_data if c["section"] == "pain_points"],
    "win_themes": [c["text"] for c in capture_data if c["section"] == "win_themes"],
    "differentiators": [c["text"] for c in capture_data if c["section"] == "discriminators"]
} if isinstance(capture_data, list) else capture_data

# === Step 5: Tag solicitation chunks ===
print("\n🤖 Tagging expectation identifiers...")
tagged_chunks = tag_expectation_identifier(chunks, capture_context=grouped_capture_data)

print("\n🔍 Tagging evaluation criteria...")
tagged_chunks = tag_eval_criteria_chunks(tagged_chunks)

criteria_chunks = [
    {"chunk_id": c["chunk_id"], "text": c["text"]}
    for c in tagged_chunks
    if c["metadata"]["agent_tags"].get("eval_criteria_identifier", 0.0) >= 0.7
]
criteria_text = "\n\n".join([c["text"] for c in criteria_chunks])
eval_criteria_path = get_eval_criteria_path(portfolio, opportunity)
os.makedirs(os.path.dirname(eval_criteria_path), exist_ok=True)
with open(eval_criteria_path, "w", encoding="utf-8") as f:
    json.dump({"criteria_chunks": criteria_chunks}, f, indent=2)

print("\n🏷️ Tagging win theme mapping...")
tagged_chunks = tag_win_theme_mapper(tagged_chunks, grouped_capture_data, criteria_text)

# === Step 6: Extract past performance ===
print("\n📂 Extracting past performance metadata...")
pp_folder = f"data/{portfolio}/opportunities/{opportunity}/past_performance/"
pp_output_path = get_past_perf_json_path(portfolio, opportunity)
pp_docs = load_documents(list_local_files(pp_folder))
projects_by_name = {}
for doc in pp_docs:
    fname = Path(doc.metadata.get("source", "unknown")).name
    metadata = extract_project_metadata(doc.page_content, fname)
    if not metadata: continue
    cid = metadata.get("contract_identification")
    if not cid: continue
    pname = infer_project_name(cid, fname)
    key = pname.strip().lower()
    projects_by_name[key] = merge_projects(projects_by_name.get(key, {}), metadata)
with open(pp_output_path, "w", encoding="utf-8") as f:
    json.dump(list(projects_by_name.values()), f, indent=2)

# === Step 7: Match past performance to chunks ===
print("\n🔀 Matching past performance...")
tagged_chunks = tag_chunks_with_pp(tagged_chunks, list(projects_by_name.values()))

# === Save final tagged chunks ===
tagged_output_path = get_tagged_chunks_path(portfolio, opportunity)
os.makedirs(os.path.dirname(tagged_output_path), exist_ok=True)
with open(tagged_output_path, "w", encoding="utf-8") as f:
    json.dump(tagged_chunks, f, indent=2)

# === Step 8–13: Placeholders ===
print("\n📌 [TODO] Section coverage analysis – NOT IMPLEMENTED YET")
print("\n📌 [TODO] Compliance checklist extraction – NOT IMPLEMENTED YET")
print("\n📌 [TODO] Risk identification – NOT IMPLEMENTED YET")
print("\n📌 [TODO] Tone & style profiling – NOT IMPLEMENTED YET")
print("\n📌 [TODO] Scoring rubric mapping – NOT IMPLEMENTED YET")
print("\n📌 [TODO] Keyword/theme frequency analysis – NOT IMPLEMENTED YET")

print("\n📅 Phase 1: Solicitation Analysis complete.")
