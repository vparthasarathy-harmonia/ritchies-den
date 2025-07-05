# demo_solicitation_pipeline.py

import os
from rag.project_paths import get_s3_prefix, get_local_folder
from rag.pipeline_utils import (
    list_s3_files, download_s3_file,
    list_local_files, load_documents, chunk_documents
)
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

portfolio = "demo"
opportunity = "sample"

bucket = os.getenv("S3_BUCKET")
s3_prefix = get_s3_prefix(portfolio, opportunity)
local_folder = get_local_folder(portfolio, opportunity)

# Step 1: Download files from S3
print(f"\n🔍 Listing files in S3 under: {s3_prefix}")
s3_keys = list_s3_files(bucket, prefix=s3_prefix)
print(f"✅ Found {len(s3_keys)} files")

for key in s3_keys:
    filename = key.split("/")[-1]
    dest_path = os.path.join(local_folder, filename)
    download_s3_file(bucket, key, dest_path)
    print(f"⬇️ Downloaded {key} → {dest_path}")

# Step 2: Load and chunk
print("\n📄 Loading documents...")
file_paths = list_local_files(local_folder)
docs = load_documents(file_paths)
print(f"✅ Loaded {len(docs)} documents")

print("🔪 Chunking...")
chunks = chunk_documents(docs, opportunity_name=opportunity)
print(f"✅ Generated {len(chunks)} chunks")

# Step 3: Display a sample
if chunks:
    print("\n🧱 Sample chunk:")
    print(chunks[0])
else:
    print("⚠️ No chunks generated. Check if input files exist and contain readable content.")
