# rag/extract_capture_themes.py (Fast Hierarchical Version – DOCX only)

import os
import json
from pathlib import Path
from docx import Document
# from pptx import Presentation
import fitz  # PyMuPDF

SECTION_LABELS = {
    "win theme": "win_themes",
    "win themes": "win_themes",
    "hot button": "hot_buttons",
    "hot buttons": "hot_buttons",
    "discriminator": "discriminators",
    "discriminators": "discriminators"
}

def normalize_heading(text: str) -> str:
    lower = text.lower().strip()
    for label, tag in SECTION_LABELS.items():
        if label in lower:
            return tag
    return None

def parse_docx(path: Path) -> list:
    print(f"📄 Parsing DOCX: {path.name}")
    doc = Document(path)
    chunks = []
    current_section = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        section = normalize_heading(text)
        if section:
            current_section = section
            continue
        if current_section:
            chunks.append({"section": current_section, "text": text, "source_file": path.name})
    return chunks

# def parse_pptx(path: Path) -> list:
#     print(f"📊 Parsing PPTX: {path.name}")
#     prs = Presentation(path)
#     chunks = []
#     current_section = None
#     for slide in prs.slides:
#         for shape in slide.shapes:
#             if not hasattr(shape, "text"):
#                 continue
#             text = shape.text.strip()
#             if not text:
#                 continue
#             section = normalize_heading(text)
#             if section:
#                 current_section = section
#                 continue
#             if current_section:
#                 chunks.append({"section": current_section, "text": text, "source_file": path.name})
#     return chunks

def parse_pdf(path: Path) -> list:
    print(f"📄 Parsing PDF: {path.name}")
    doc = fitz.open(str(path))
    chunks = []
    current_section = None
    for page in doc:
        for line in page.get_text("text").splitlines():
            text = line.strip()
            if not text:
                continue
            section = normalize_heading(text)
            if section:
                current_section = section
                continue
            if current_section:
                chunks.append({"section": current_section, "text": text, "source_file": path.name})
    return chunks

def parse_all_capture_files(folder_path: str) -> list:
    folder = Path(folder_path)
    capture_files = [f for f in folder.glob("capture*.*") if f.suffix.lower() in [".docx", ".pdf"]]
    if not capture_files:
        print("⚠️ No capture*.{docx,pdf} files found.")
        return []

    all_chunks = []
    for file in capture_files:
        try:
            if file.suffix.lower() == ".docx":
                all_chunks.extend(parse_docx(file))
            # elif file.suffix.lower() in [".pptx", ".ppt"]:
            #     all_chunks.extend(parse_pptx(file))
            elif file.suffix.lower() == ".pdf":
                all_chunks.extend(parse_pdf(file))
            else:
                print(f"⚠️ Skipping unsupported file: {file.name}")
        except Exception as e:
            print(f"❌ Failed to parse {file.name}: {e}")
    return all_chunks

def save_capture_json(data: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved parsed capture chunks to: {output_path}")
