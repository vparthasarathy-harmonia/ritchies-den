# test_docx_read.py

import sys
from pathlib import Path
from rag.pipeline_utils import load_documents

if len(sys.argv) != 2:
    print("Usage: python test_docx_read.py <path_to_docx_file>")
    sys.exit(1)

file_path = Path(sys.argv[1])
if not file_path.exists():
    print(f"❌ File does not exist: {file_path}")
    sys.exit(1)

print(f"\n📂 Loading file: {file_path}")
docs = load_documents([str(file_path)])

if not docs:
    print("❌ No documents loaded. The parser may have failed silently.")
    sys.exit(1)

doc = docs[0]
content = doc.page_content
print(f"✅ Loaded content from: {doc.metadata.get('source', 'unknown')}")
print(f"📏 Length: {len(content)} characters")

# Show preview
print("\n📄 First 500 characters:\n" + content[:500])
