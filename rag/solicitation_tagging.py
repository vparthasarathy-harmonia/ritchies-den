# rag/solicitation_tagging.py

from typing import List, Dict
from rag.llm_client_claude import invoke_claude

# === 1. Expectation Identifier ===
def build_expectation_prompt(text: str) -> str:
    return f"""
You are a proposal analyst. Read the text below and decide whether it contains any explicit or implicit expectations from the client in an RFP.

Respond with a confidence score from 0.0 to 1.0, and explain briefly.

### Example output:
Expectation Identifier: 0.87 - Mentions of submission deadlines and response format

### Text:
{text.strip()}
"""

def tag_expectation_identifier(chunks: List[Dict]) -> List[Dict]:
    for chunk in chunks:
        prompt = build_expectation_prompt(chunk["text"])
        try:
            response = invoke_claude(prompt)
            print(f"\n🔍 [expectation_identifier] Chunk {chunk['chunk_id']}:\n{response}")
            match = next((s for s in response.split() if s.replace(".", "", 1).isdigit()), "0.0")
            score = round(float(match), 2)
        except Exception as e:
            print(f"❌ Claude call failed: {e}")
            score = 0.0

        chunk["metadata"].setdefault("agent_tags", {})["expectation_identifier"] = score
    return chunks

# === 2. Evaluation Criteria Identifier ===
def tag_eval_criteria_chunks(chunks: List[Dict]) -> List[Dict]:
    for chunk in chunks:
        prompt = f"""
You are analyzing a government RFP.

Read the chunk of text below and determine whether it describes **evaluation criteria**, **basis for award**, **technical scoring factors**, or **proposal evaluation methods**.

---

### Chunk:
{chunk['text'].strip()}

---

### Instructions:
1. Respond in the format:
    eval_criteria_identifier: <confidence score> - <1-line rationale>
2. Score 0.0 if nothing evaluation-related is found.
3. Score 1.0 if the chunk clearly contains evaluation factors or scoring instructions.

Only respond in this format.
"""
        try:
            response = invoke_claude(prompt)
            print(f"\n🔍 [eval_criteria_identifier] Chunk {chunk['chunk_id']}:\n{response}")
            score = 0.0
            if ":" in response:
                parts = response.split(":")[1].strip().split("-", 1)
                score = round(float(parts[0]), 2)

            chunk["metadata"].setdefault("agent_tags", {})["eval_criteria_identifier"] = score

        except Exception as e:
            print(f"❌ Claude failed for eval_criteria_identifier: {e}")
            chunk["metadata"].setdefault("agent_tags", {})["eval_criteria_identifier"] = 0.0

    return chunks

# === 3. Win Theme Mapper using structured capture JSON ===
def tag_win_theme_mapper(chunks: List[Dict], capture_data: dict, criteria_text: str) -> List[Dict]:
    pain_points = "\n- ".join(capture_data.get("pain_points", []))
    win_themes = "\n- ".join(capture_data.get("win_themes", []))
    differentiators = "\n- ".join(capture_data.get("differentiators", []))

    for chunk in chunks:
        prompt = f"""
You are a proposal strategist helping analyze a government RFP.

Your goal is to tag each chunk of the solicitation based on how well it aligns with the win themes, pain points, and differentiators captured by the team and what the client is actually scoring.

---

### Pain Points:
{pain_points[:1000]}

### Win Themes:
{win_themes[:1000]}

### Differentiators:
{differentiators[:1000]}

### Evaluation Criteria (from RFP):
{criteria_text.strip()[:3000]}

### Chunk:
{chunk['text'].strip()}

---

### Instructions:
1. Determine if this chunk expresses or implies a **pain point**, a **win theme**, or a **differentiator**.
2. Respond in the format:
    win_theme_mapper: <confidence score> - <classification> - <1-line rationale>

Example:
win_theme_mapper: 0.85 - differentiator - Highlights our rapid deployment capability vs. industry average

Only respond in this format.
"""
        try:
            response = invoke_claude(prompt)
            print(f"\n🔍 [win_theme_mapper] Chunk {chunk['chunk_id']}:\n{response}")
            score = 0.0
            label = "none"
            if ":" in response:
                parts = response.split(":")[1].strip().split("-", 2)
                score = round(float(parts[0]), 2)
                label = parts[1].strip().lower()

            chunk["metadata"].setdefault("agent_tags", {})["win_theme_mapper"] = {
                "score": score,
                "label": label
            }

        except Exception as e:
            print(f"❌ Claude failed for win_theme_mapper: {e}")
            chunk["metadata"].setdefault("agent_tags", {})["win_theme_mapper"] = {
                "score": 0.0,
                "label": "error"
            }

    return chunks
