# test_agents.py

import os
import json
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from rag.solicitation_tagging import (
    tag_expectation_identifier, tag_eval_criteria_chunks, tag_win_theme_mapper
)
from rag.pp_matcher import tag_chunks_with_pp
from rag.compliance_tagger import tag_compliance_chunks
from rag.project_paths import (
    get_tagged_chunks_path, get_eval_criteria_path,
    get_capture_json_path, get_past_perf_json_path, get_local_folder
)

load_dotenv(dotenv_path=".env.local")

parser = argparse.ArgumentParser()
parser.add_argument("portfolio")
parser.add_argument("opportunity")
parser.add_argument("--parallel", action="store_true", help="Run agents in parallel")
parser.add_argument("--limit", type=int, default=None, help="Number of chunks to test")
args = parser.parse_args()

portfolio = args.portfolio
opportunity = args.opportunity
base_path = get_local_folder(portfolio, opportunity)

# === Load chunks ===
with open(get_tagged_chunks_path(portfolio, opportunity), "r", encoding="utf-8") as f:
    chunks = json.load(f)
if args.limit:
    chunks = chunks[:args.limit]

# === Load capture data ===
with open(get_capture_json_path(portfolio, opportunity), "r", encoding="utf-8") as f:
    capture_data = json.load(f)
if isinstance(capture_data, list):
    capture_context = {
        "pain_points": [c["text"] for c in capture_data if c["section"] == "pain_points"],
        "win_themes": [c["text"] for c in capture_data if c["section"] == "win_themes"],
        "differentiators": [c["text"] for c in capture_data if c["section"] == "discriminators"]
    }
else:
    capture_context = capture_data

# === Load past performance ===
with open(get_past_perf_json_path(portfolio, opportunity), "r", encoding="utf-8") as f:
    past_perf_projects = json.load(f)

# === Load eval criteria text ===
eval_criteria_path = get_eval_criteria_path(portfolio, opportunity)
if os.path.exists(eval_criteria_path):
    with open(eval_criteria_path, "r", encoding="utf-8") as f:
        eval_json = json.load(f)
    criteria_text = "\n\n".join([c["text"] for c in eval_json.get("criteria_chunks", [])])
else:
    criteria_text = "\n\n".join([c["text"] for c in chunks if "evaluation" in c["text"].lower()])

# === Agent runner ===

def run_agents(chunks):
    agent_timings = {}
    t0 = time.time()
    chunks1 = tag_expectation_identifier(chunks, capture_context=capture_context)
    agent_timings["expectation_identifier"] = round(time.time() - t0, 2)

    t0 = time.time()
    chunks2 = tag_eval_criteria_chunks(chunks)
    agent_timings["eval_criteria_identifier"] = round(time.time() - t0, 2)

    t0 = time.time()
    chunks3 = tag_win_theme_mapper(chunks, capture_context, criteria_text)
    agent_timings["win_theme_mapper"] = round(time.time() - t0, 2)

    t0 = time.time()
    chunks4 = tag_chunks_with_pp(chunks, past_perf_projects)
    agent_timings["pp_matcher"] = round(time.time() - t0, 2)

    t0 = time.time()
    compliance_response, compliance_performance = tag_compliance_chunks(chunks)
    agent_timings["compliance_tagger"] = round(time.time() - t0, 2)

    return [chunks1, chunks2, chunks3, chunks4], compliance_response, compliance_performance, agent_timings


def run_agents_parallel(chunks):
    agent_timings = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        def timed(name, fn):
            t0 = time.time()
            result = fn()
            agent_timings[name] = round(time.time() - t0, 2)
            time.sleep(0.5 if len(agent_timings) % 2 == 0 else 1.0)
            return result

        f1 = executor.submit(lambda: timed("expectation_identifier", lambda: tag_expectation_identifier(chunks, capture_context=capture_context)))
        f2 = executor.submit(lambda: timed("eval_criteria_identifier", lambda: tag_eval_criteria_chunks(chunks)))
        f3 = executor.submit(lambda: timed("win_theme_mapper", lambda: tag_win_theme_mapper(chunks, capture_context, criteria_text)))
        f4 = executor.submit(lambda: timed("pp_matcher", lambda: tag_chunks_with_pp(chunks, past_perf_projects)))
        f5 = executor.submit(lambda: timed("compliance_tagger", lambda: tag_compliance_chunks(chunks)))

        chunks1 = f1.result()
        chunks2 = f2.result()
        chunks3 = f3.result()
        chunks4 = f4.result()
        compliance_response, compliance_performance = f5.result()

    return [chunks1, chunks2, chunks3, chunks4], compliance_response, compliance_performance, agent_timings

# === Run ===
print("\n🚀 Testing agents...\n")
start_time = time.time()
if args.parallel:
    all_chunks, compliance_response, compliance_performance, timings = run_agents_parallel(chunks)
else:
    all_chunks, compliance_response, compliance_performance, timings = run_agents(chunks)

# === Merge chunks ===
merged = defaultdict(dict)
for chunk_list in all_chunks:
    for chunk in chunk_list:
        merged[chunk["chunk_id"]].update(chunk)

# === Save ===
with open(get_tagged_chunks_path(portfolio, opportunity), "w", encoding="utf-8") as f:
    json.dump(list(merged.values()), f, indent=2)

print("\n⏱️ Agent Timing Summary:")
for name, sec in sorted(timings.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {name}: {sec} seconds")

elapsed = round(time.time() - start_time, 2)
print(f"\n✅ Agent test complete in {elapsed} seconds\n")
