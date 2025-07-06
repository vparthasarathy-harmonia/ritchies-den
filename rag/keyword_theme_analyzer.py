# rag/keyword_theme_analyzer.py — Hybrid strategy with batching

import json
import re
import string
from collections import Counter, defaultdict
from itertools import islice
from rag.llm_client_claude import invoke_claude
from difflib import SequenceMatcher

STOPWORDS = set("""
a an and are as at be but by for if in into is it no not of on or such that the their then there these they this to was will with you your we our from under above over within without shall should must can may
""".split())


def extract_terms(text, max_vocab=500):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    unigrams = [w for w in words if w not in STOPWORDS and len(w) > 2]

    bigrams = [f"{w1} {w2}" for w1, w2 in zip(words, words[1:]) if w1 not in STOPWORDS and w2 not in STOPWORDS]
    trigrams = [f"{w1} {w2} {w3}" for w1, w2, w3 in zip(words, words[1:], words[2:]) if all(w not in STOPWORDS for w in (w1, w2, w3))]

    counter = Counter(unigrams + bigrams + trigrams)
    return counter


def clean_malformed_json(text):
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def merge_similar_themes(themes, similarity_threshold=0.75):
    merged = []
    used = set()

    def similar(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= similarity_threshold

    for i, base in enumerate(themes):
        if i in used:
            continue
        base_keywords = set(base["keywords"])
        new_theme = base["theme"]

        for j, candidate in enumerate(themes[i + 1:], start=i + 1):
            if j in used:
                continue
            if similar(base["theme"], candidate["theme"]):
                base_keywords.update(candidate["keywords"])
                used.add(j)
        merged.append({
            "theme": new_theme,
            "keywords": sorted([
                {"term": k, "frequency": term_counter.get(k, 0)} for k in base_keywords
            ], key=lambda x: x["frequency"], reverse=True)
        })
    return merged


def analyze_keywords_from_chunks(chunks, portfolio=None, opportunity=None):
    print("\n🔍 [keyword_theme_analyzer] Extracting frequent terms in batches...")

    MAX_CHARS_PER_BATCH = 100_000
    current_text = ""
    term_counter = Counter()

    for chunk in chunks:
        text = chunk.get("text", "")
        if len(current_text) + len(text) > MAX_CHARS_PER_BATCH:
            counter = extract_terms(current_text)
            term_counter.update(counter)
            current_text = text
        else:
            current_text += "\n\n" + text

    if current_text:
        counter = extract_terms(current_text)
        term_counter.update(counter)

    top_terms = term_counter.most_common(250)
    with open("keyword_frequencies.json", "w", encoding="utf-8") as freq_file:
        json.dump(dict(top_terms), freq_file, indent=2)
    print(f"📊 Saved term frequencies to: keyword_frequencies.json")

    top_words = [w for w, _ in top_terms]
    print(f"🧠 Found {len(top_terms)} high-frequency terms")

    prompt = f"""
You are a theme mapping analyst.
Given the following list of frequently used terms from a government solicitation, group them into logical themes.

Return a JSON object with:
- theme: the name of the theme (e.g., Cybersecurity, Data Management)
- keywords: the list of related terms under that theme

Terms:
{json.dumps(top_words, indent=2)}

Only return valid JSON:
{{
  "themes": [
    {{ "theme": "...", "keywords": ["...", "..."] }},
    ...
  ]
}}
"""

    try:
        print("⏳ Sending terms to Claude...")
        result = invoke_claude(prompt)
        with open("keyword_themes_response.txt", "w", encoding="utf-8") as rf:
            rf.write(result)
        print("✅ Response received")

        with open("keyword_themes_raw.json", "w", encoding="utf-8") as raw_file:
            raw_file.write(result)

        start = result.find('{')
        end = result.rfind('}') + 1
        cleaned = clean_malformed_json(result[start:end])
        try:
            parsed = json.loads(cleaned)
            parsed["frequencies"] = dict(term_counter)

            if "themes" in parsed:
                for theme_obj in parsed["themes"]:
                    keywords = theme_obj.get("keywords", [])
                    cleaned_keywords = set(
                        k.strip().replace("•", "")
                        for k in keywords
                        if k and k.strip() and k.strip() != "•"
                    )
                    theme_obj["keywords"] = sorted([
                        {"term": k, "frequency": term_counter.get(k, 0)} for k in cleaned_keywords
                    ], key=lambda x: x["frequency"], reverse=True)
                parsed["themes"] = merge_similar_themes(parsed["themes"])
        except json.JSONDecodeError as e:
            with open(f"data/{portfolio}/opportunities/{opportunity}/keyword_themes_cleaned.json", "w", encoding="utf-8") as cf:
                cf.write(cleaned)
            print(f"⚠️ Cleaned JSON also failed: {e}")
            return {"error": "Failed to parse cleaned JSON", "details": str(e)}
        print("✅ Keyword theme analysis complete")
        return parsed
    except Exception as e:
        print(f"⚠️ Keyword theme analysis failed: {e}")
        return {}


if __name__ == "__main__":
    import sys
    portfolio = sys.argv[1]
    opportunity = sys.argv[2]
    chunk_path = f"data/{portfolio}/opportunities/{opportunity}/tagged_chunks.json"
    output_path = f"data/{portfolio}/opportunities/{opportunity}/keyword_themes.json"

    with open(chunk_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    result = analyze_keywords_from_chunks(chunks, portfolio, opportunity)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"📄 Saved keyword themes to: {output_path}")
