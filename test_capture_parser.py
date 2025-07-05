# test_capture_parser.py

import os
import sys
import json
from rag.project_paths import get_capture_json_path, get_local_folder
from rag.extract_capture_themes import parse_all_capture_files, save_capture_json

if len(sys.argv) != 3:
    print("Usage: python test_capture_parser.py <portfolio> <opportunity>")
    sys.exit(1)

portfolio = sys.argv[1]
opportunity = sys.argv[2]

# Paths
folder = get_local_folder(portfolio, opportunity)
output_path = get_capture_json_path(portfolio, opportunity)

# Run parsing
print(f"\n🔍 Parsing capture files in: {folder}")
capture_chunks = parse_all_capture_files(folder)

if capture_chunks:
    save_capture_json(capture_chunks, output_path)
    print(f"✅ Parsed {len(capture_chunks)} capture chunks.")
else:
    print("⚠️ No valid capture data found.")
