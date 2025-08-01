# run_solicitation_analysis.py — End-to-End Orchestrator for Phase 1: Solicitation Analysis

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

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
from rag.pp_matcher import tag_chunks_with_pp
from rag.compliance_tagger import tag_compliance_chunks
from rag.keyword_theme_analyzer import analyze_keywords_from_chunks

load_dotenv(dotenv_path=".env.local")

start_time = time.time()

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

print(f"\n🗓️ Downloading S3 files for {portfolio}/{opportunity} ...")
s3_keys = list_s3_files(bucket, prefix=s3_prefix)
for key in s3_keys:
    filename = key.split("/")[-1]
    download_s3_file(bucket, key, os.path.join(local_folder, filename))

print("\n📄 Loading and chunking solicitation documents...")
file_paths = [p for p in list_local_files(local_folder) if not Path(p).name.lower().startswith("capture")]
docs = load_documents(file_paths)
chunks = chunk_documents(docs, opportunity_name=opportunity)

print("\n📚 Extracting TOC/sections and enriching chunks with breadcrumbs...")
full_text = "\n\n".join([doc.page_content for doc in docs])
parsed_context = extract_toc_and_sections(full_text)
parsed_context_path = f"data/{portfolio}/opportunities/{opportunity}/parsed_context.json"
save_parsed_context(parsed_context, parsed_context_path)
section_map = {s["id"]: s for s in parsed_context["sections"] if "id" in s}
chunks = enrich_chunks_with_breadcrumbs(chunks, section_map)
if args.test_limit:
    chunks = chunks[:args.test_limit]

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

print("\n📂 Extracting past performance metadata...")
pp_folder = f"data/{portfolio}/opportunities/{opportunity}/past_performance/"
pp_output_path = get_past_perf_json_path(portfolio, opportunity)
pp_docs = load_documents(list_local_files(pp_folder))
projects_by_name = {}
for doc in pp_docs:
    fname = Path(doc.metadata.get("source", "unknown")).name
    metadata = extract_project_metadata(doc.page_content, fname)
    if not metadata:
        continue
    cid = metadata.get("contract_identification")
    if not cid:
        continue
    pname = infer_project_name(cid, fname)
    key = pname.strip().lower()
    projects_by_name[key] = merge_projects(projects_by_name.get(key, {}), metadata)
with open(pp_output_path, "w", encoding="utf-8") as f:
    json.dump(list(projects_by_name.values()), f, indent=2)

print("\n🤖 Running taggers sequentially...")
t0 = time.time()
chunks1 = tag_expectation_identifier(chunks, capture_context=grouped_capture_data)
chunks2 = tag_eval_criteria_chunks(chunks)
criteria_text = "\n\n".join([c["text"] for c in chunks2 if c["metadata"]["agent_tags"].get("eval_criteria_identifier", 0.0) >= 0.7])
chunks3 = tag_win_theme_mapper(chunks, grouped_capture_data, criteria_text)
chunks4 = tag_chunks_with_pp(chunks, list(projects_by_name.values()))
compliance_response, compliance_performance = tag_compliance_chunks(chunks)

output_dir = f"data/{portfolio}/opportunities/{opportunity}"
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, "compliance_response.json"), "w") as f:
    json.dump(compliance_response, f, indent=2)
with open(os.path.join(output_dir, "compliance_performance.json"), "w") as f:
    json.dump(compliance_performance, f, indent=2)

print("\n\n🔧 Merging agent outputs...")
merged_by_id = defaultdict(dict)
for chunk_list in [chunks1, chunks2, chunks3, chunks4]:
    for chunk in chunk_list:
        merged_by_id[chunk["chunk_id"]].update(chunk)

tagged_chunks = list(merged_by_id.values())

print("\n🔁 Matching past performance to solicitation chunks...")
tagged_chunks = tag_chunks_with_pp(tagged_chunks, list(projects_by_name.values()))

print("\n📌 Step 8: Section coverage analysis...")
def perform_section_coverage_analysis(tagged_chunks, parsed_context, portfolio, opportunity):
    print("\n🔍 Analyzing section coverage gaps...")
    covered_section_ids = set()

    for chunk in tagged_chunks:
        section_id = chunk.get("section_id") or ""
        tags = chunk.get("metadata", {}).get("agent_tags", {})

        if (
            tags.get("expectation_identifier", 0.0) > 0.6
            or tags.get("eval_criteria_identifier", 0.0) > 0.6
            or (isinstance(tags.get("win_theme_mapper"), dict) and tags["win_theme_mapper"].get("score", 0.0) > 0.6)
            or "pp_matcher" in tags
        ):
            if section_id:
                covered_section_ids.add(section_id)

    uncovered_sections = [s for s in parsed_context["sections"] if s["id"] not in covered_section_ids]

    print("\n🔹 Uncovered Sections:")
    for s in uncovered_sections:
        print(f" - {s['id']} {s['heading']}")

    gap_report_path = f"data/{portfolio}/opportunities/{opportunity}/coverage_gaps.json"
    os.makedirs(os.path.dirname(gap_report_path), exist_ok=True)
    with open(gap_report_path, "w", encoding="utf-8") as f:
        json.dump(uncovered_sections, f, indent=2)
    print(f"\n📅 Coverage gap report saved to: {gap_report_path}")

perform_section_coverage_analysis(tagged_chunks, parsed_context, portfolio, opportunity)

tagged_output_path = get_tagged_chunks_path(portfolio, opportunity)
os.makedirs(os.path.dirname(tagged_output_path), exist_ok=True)
with open(tagged_output_path, "w", encoding="utf-8") as f:
    json.dump(tagged_chunks, f, indent=2)

print("\n📌 [TODO] Scoring rubric mapping – NOT IMPLEMENTED YET")
print("\n📌 [TODO] Tone & style profiling – NOT IMPLEMENTED YET")

print("\n📌 Step 13: Keyword/Theme Frequency Analysis...")
keyword_result = analyze_keywords_from_chunks(tagged_chunks, portfolio, opportunity)
keyword_path = os.path.join(output_dir, "keyword_themes.json")
with open(keyword_path, "w", encoding="utf-8") as f:
    json.dump(keyword_result, f, indent=2)
print(f"📊 Saved keyword themes to: {keyword_path}")

end_time = time.time()
total_time = round(end_time - start_time, 2)
print(f"\n📅 Phase 1: Solicitation Analysis complete in {total_time} seconds.")
