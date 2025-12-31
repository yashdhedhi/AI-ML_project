from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer, util 
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def semantic_similarity_pct(text1: str, text2: str) -> float:
    model = _load_model()
    emb1 = model.encode(text1 or "", convert_to_tensor=True)
    emb2 = model.encode(text2 or "", convert_to_tensor=True)
    score = float(util.cos_sim(emb1, emb2).item())  # -1..1
    pct = (score + 1) * 50.0  # map to 0..100
    return max(0.0, min(100.0, pct))

def _skill_overlap_pct(resume_skills: List[str], job_skills: List[str]) -> float:
    s1 = set(x.lower() for x in resume_skills or [])
    s2 = set(x.lower() for x in job_skills or [])
    if not s1 and not s2:
        return 0.0
    inter = len(s1 & s2)
    union = len(s1 | s2)
    jacc = inter / union if union else 0.0
    return round(jacc * 100.0, 4)

def final_combine(skill_pct: float, semantic_pct: float, w_skill: float = 0.6, w_sem: float = 0.4) -> float:
    return float(w_skill * skill_pct + w_sem * semantic_pct)

def compute_scores(resume_text: str, resume_skills: List[str], job: Dict) -> Dict:
    title = job.get("title", "") or ""
    desc = job.get("description", "") or ""
    company = (job.get("company") or {}).get("display_name", "") or ""
    job_text = f"{title}\n{company}\n{desc}"

    # naive job skill extraction: reuse title+desc token scan against resume skills for display
    # In a real setup, use the same extractor against a full skills vocabulary.
    job_tokens = set(t.strip().lower() for t in (title + " " + desc).split())
    job_skills = [s for s in resume_skills if s.lower().replace(" ", "") in "".join(job_tokens)]

    matched = sorted(set([s for s in resume_skills if s in job_skills]))
    missing = sorted([s for s in resume_skills if s not in matched])

    skill_pct = _skill_overlap_pct(resume_skills, job_skills)
    semantic_pct = semantic_similarity_pct(resume_text, job_text)
    final_score = final_combine(skill_pct, semantic_pct)

    return {
        "skill_pct": float(skill_pct),
        "semantic_pct": float(semantic_pct),
        "final_score": float(final_score),
        "matched_skills": matched,
        "missing_skills": missing
    }
