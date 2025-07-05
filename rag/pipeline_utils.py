# ritchies-den/rag/rag_pipeline.py

import os
import re
import uuid
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.local")

import boto3
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.schema import Document

# === Load environment variables ===
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
BEDROCK_REGION = os.getenv("BEDROCK_REGION")
BEDROCK_ACCESS_KEY_ID = os.getenv("BEDROCK_ACCESS_KEY_ID")

# === Setup S3 client ===
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION
)

# === Chunking parameters ===
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100

# === S3 file listing ===
def list_s3_files(bucket: str, prefix: str = "") -> list:
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [
        item["Key"]
        for item in response.get("Contents", [])
        if not item["Key"].endswith("/")
    ]

# === S3 download ===
def download_s3_file(bucket: str, key: str, dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    s3.download_file(bucket, key, dest_path)

# === Local file listing ===
def list_local_files(folder_path: str, extensions=(".pdf", ".docx", ".pptx", ".xlsx")) -> List[str]:
    return [
        str(path)
        for path in Path(folder_path).rglob("*")
        if path.suffix.lower() in extensions
    ]

# === Document loading ===
def load_documents(file_paths: List[str]) -> List[Document]:
    docs = []
    for file_path in file_paths:
        try:
            loader = UnstructuredFileLoader(file_path)
            docs.extend(loader.load())
        except Exception as e:
            print(f"Failed to load {file_path}: {e}")
    return docs

# === Hierarchical chunking ===
def hierarchical_chunk(text: str, max_chunk_size=CHUNK_SIZE) -> List[str]:
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []
    buffer = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(buffer) + len(para) < max_chunk_size:
            buffer += "\n\n" + para
        else:
            chunks.append(buffer.strip())
            buffer = para

    if buffer:
        chunks.append(buffer.strip())

    return chunks

# === Chunk documents and enrich metadata ===
def chunk_documents(documents: List[Document], opportunity_name: str) -> List[Dict]:
    all_chunks = []

    for doc in documents:
        raw_text = doc.page_content
        source = doc.metadata.get("source", "unknown")

        split_chunks = hierarchical_chunk(raw_text)

        for chunk_text in split_chunks:
            chunk = {
                "chunk_id": f"{uuid.uuid4().hex[:8]}",
                "text": chunk_text,
                "metadata": {
                    "opportunity_name": opportunity_name,
                    "source_document": source,
                    "contains_bullets": bool(re.search(r'[-•*]\s+', chunk_text)),
                    "agent_tags": {}
                }
            }
            all_chunks.append(chunk)

    return all_chunks

# === Read Capture file(s) ===
from langchain_community.document_loaders import UnstructuredFileLoader  # make sure to use new path

def load_capture_file(folder_path: str) -> str:
    # Accepts .pptx, .ppt, .docx, .pdf
    for ext in [".pptx", ".ppt", ".docx", ".pdf"]:
        capture_path = Path(folder_path) / f"capture{ext}"
        if capture_path.exists():
            try:
                print(f"📥 Found capture file: {capture_path}")
                loader = UnstructuredFileLoader(str(capture_path))
                docs = loader.load()
                return "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                print(f"❌ Failed to load capture file: {capture_path} - {e}")
    print("⚠️ No capture file found.")
    return ""
