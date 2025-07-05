# ritchies-den/rag/parse_capture_file.py

import os
import json
from pathlib import Path
from langchain_community.document_loaders import UnstructuredFileLoader
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

# === Step 1: Load and parse all capture* files ===
def parse_all_capture_files(folder_path: str) -> dict:
    """
    Loads all files starting with capture.* from the folder,
    concatenates their text, and returns structured win theme data.
    """
    combined_text = ""
    folder = Path(folder_path)
    capture_files = [f for f in folder.glob("capture*.*") if f.suffix.lower() in [".pptx", ".ppt", ".docx", ".pdf"]]

    if not capture_files:
        print("⚠️ No capture* files found.")
        return {}

    for capture_path in capture_files:
        try:
            print(f"📥 Found capture file: {capture_path}")
            loader = UnstructuredFileLoader(str(capture_path))
            docs = loader.load()
            combined_text += "\n\n".join([d.page_content for d in docs]) + "\n\n"
        except Exception as e:
            print(f"❌ Failed to load {capture_path} - {e}")

    if not combined_text.strip():
        print("⚠️ No text extracted from capture files.")
        return {}

    return extract_win_themes(combined_text)


# === Step 2: Extract pain points, win themes, differentiators ===
def extract_win_themes(text: str) -> dict:
    from rag.llm_client import invoke_claude

    prompt = f"""
You are a proposal strategist.

Below is a combined text from one or more capture planning documents (PowerPoint, Word, or PDF).
Your task is to extract and organize the following into structured bullet lists:

- Pain Points
- Win Themes
- Differentiators

Only include items actually present in the text.
Return your answer in this JSON format:
{{
  "pain_points": [...],
  "win_themes": [...],
  "differentiators": [...]
}}

---

Text:
{text.strip()[:6000]}
"""
    try:
        response = invoke_claude(prompt)
        print("\n🧠 Claude response:\n", response)
        json_start = response.find("{")
        json_part = response[json_start:].strip()
        return json.loads(json_part)
    except Exception as e:
        print(f"❌ Claude extraction failed: {e}")
        return {}


# === Step 3: Save to disk ===
def save_capture_json(data: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved parsed capture to {output_path}")


# === Entry point ===
if __name__ == "__main__":
    opportunity = "VALGY"
    folder = f"data/opportunities/{opportunity}/solicitation/"
    output_file = f"data/opportunities/{opportunity}/capture_parsed.json"

    structured = parse_all_capture_files(folder)
    if structured:
        save_capture_json(structured, output_file)
