# test_metadata_extraction.py

from pathlib import Path
from rag.pipeline_utils import load_documents
from rag.llm_client_claude import invoke_claude
import json

def extract_single_project(doc_text, filename="DHS ICE ERO for Adapts_03-2025.docx"):
    prompt = f"""
You are extracting structured metadata about a past performance project from a proposal document.

Return a JSON object with the following keys:
- period_of_performance
- contract_identification
- client_and_agency
- scope_and_work_type
- financials_and_labor
- teaming_and_delivery
- performance_and_quality
- compliance_and_standards
- contract_strategy

If anything is unknown, use null or an empty list. Only return valid JSON.
The filename is: {filename}

---
{doc_text[:3000]}
---
"""
    print("🧠 Sending to Claude...")
    response = invoke_claude(prompt)
    print("✅ Response:\n", response[:500], "...\n")

if __name__ == "__main__":
    file_path = Path("data/NatSec_DoD/opportunities/DHS_ICE_CALEA_T3ILU/past_performance/DHS ICE ERO for Adapts_03-2025.docx")
    print(f"📂 Loading: {file_path}")
    docs = load_documents([str(file_path)])

    if not docs:
        print("❌ Failed to read document.")
    else:
        content = docs[0].page_content
        print(f"📏 Content length: {len(content)}")
        extract_single_project(content, file_path.name)
