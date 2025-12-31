import json
import re
from typing import List, Set
from rapidfuzz import fuzz

def load_skills(path: str = "skills.json") -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Accept either list or dict with "skills"
    if isinstance(data, dict) and "skills" in data:
        data = data["skills"]
    if isinstance(data, list):
        return [s.strip() for s in data if s and isinstance(s, str)]
    # If someone saved it as a single comma string, split
    if isinstance(data, str):
        return [s.strip() for s in data.split(",") if s.strip()]
    return []

def extract_skills_from_text(text: str, skills_list: List[str], fuzzy_cutoff: int = 85) -> List[str]:
    text_lower = (text or "").lower()
    found: Set[str] = set()

    # Exact whole-word match first
    for s in skills_list:
        slow = s.lower()
        pattern = r"\b" + re.escape(slow) + r"\b"
        if re.search(pattern, text_lower):
            found.add(s)

    # Fuzzy if few found
    if len(found) < 5:
        for s in skills_list:
            if s in found:
                continue
            score = fuzz.partial_ratio(s.lower(), text_lower)
            if score >= fuzzy_cutoff:
                found.add(s)

    return sorted(found)
