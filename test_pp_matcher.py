# test_pp_matcher.py

import json
from rag.pp_matcher import tag_chunks_with_pp

# Load previously saved test data
with open("data/NatSec_DoD/opportunities/DHS_ICE_CALEA_T3ILU/tagged_chunks.json", "r") as f:
    chunks = json.load(f)

with open("data/NatSec_DoD/opportunities/DHS_ICE_CALEA_T3ILU/past_perf_projects.json", "r") as f:
    past_perf = json.load(f)

# Limit to a few for fast testing
chunks = chunks[:3]
past_perf = past_perf[:2]

# Run the matching
tagged_chunks = tag_chunks_with_pp(chunks, past_perf)

# Output results
print(json.dumps(tagged_chunks, indent=2))
