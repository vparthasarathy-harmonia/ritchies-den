# rag/project_paths.py

def get_s3_prefix(portfolio: str, opportunity: str, subfolder: str = "solicitation") -> str:
    return f"{portfolio}/opportunities/{opportunity}/{subfolder}/"

def get_local_folder(portfolio: str, opportunity: str, subfolder: str = "solicitation") -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/{subfolder}/"

def get_eval_criteria_path(portfolio: str, opportunity: str) -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/eval_criteria.json"

def get_tagged_chunks_path(portfolio: str, opportunity: str) -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/tagged_chunks.json"

def get_capture_json_path(portfolio: str, opportunity: str) -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/capture_parsed.json"

def get_past_perf_json_path(portfolio: str, opportunity: str) -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/past_perf_projects.json"

def get_past_perf_folder(portfolio: str, opportunity: str) -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/past_performance/"

def get_capture_folder(portfolio: str, opportunity: str) -> str:
    return f"data/{portfolio}/opportunities/{opportunity}/solicitation/"

def get_s3_past_perf_prefix(portfolio: str, opportunity: str) -> str:
    return f"{portfolio}/opportunities/{opportunity}/past_performance/"
