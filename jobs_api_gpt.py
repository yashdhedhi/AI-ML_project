# jobs_api_gpt.py — Gemini-backed job matcher (auto-loads .env)
from __future__ import annotations

import os
import json
import re
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Load .env so GOOGLE_API_KEY is available automatically
load_dotenv()

import google.generativeai as genai

# Configure Gemini client using environment variable (loaded above)
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
    except Exception as e:
        GENAI_CONFIG_ERROR = str(e)
    else:
        GENAI_CONFIG_ERROR = None
else:
    GENAI_CONFIG_ERROR = "GOOGLE_API_KEY environment variable is not set."

# Default model (change via env var GOOGLE_GEMINI_MODEL if needed)
MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "models/gemini-2.5-flash")


def safe_json_parse(text: str):
    """Try to parse JSON, with a best-effort substring fallback."""
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
    return {"matches": [], "notes": "could_not_parse_model_output", "raw": text[:800]}


def _list_available_models():
    """Return a short list of available models (strings) or error string."""
    try:
        models = genai.list_models()
        model_ids = []
        for m in models:
            try:
                if hasattr(m, "name"):
                    model_ids.append(m.name)
                elif hasattr(m, "model"):
                    model_ids.append(m.model)
                else:
                    model_ids.append(str(m))
            except Exception:
                model_ids.append(str(m))
        return model_ids[:30]
    except Exception as e:
        return f"error_listing_models: {e}"


def _slugify(text: str) -> str:
    """Create a short safe slug from text suitable for a URL/query."""
    text = text or ""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:80]


def _make_synthetic_job_link(job_title: str, city: str) -> str:
    """
    Return a synthetic, non-deceptive example job link.

    Instead of example.com, we build a generic LinkedIn jobs SEARCH URL.
    It may not be a single posting, but it will open LinkedIn Jobs with
    relevant keywords, which is much closer to what you want.
    """
    title_slug = _slugify(job_title or "job")
    city_slug = _slugify(city or "")
    q_title = quote_plus(title_slug)
    q_city = quote_plus(city_slug)

    # Generic LinkedIn job search URL
    base = "https://www.linkedin.com/jobs/search"
    if q_city:
        return f"{base}?keywords={q_title}&location={q_city}"
    else:
        return f"{base}?keywords={q_title}"


def match_jobs_with_gpt(resume_text, city, experience, domain):
    """
    Gemini-based job matcher.

    Returns a dict with at least 'matches': [] on any failure.

    Structure:
    {
      "candidate_id": null,
      "summary": "short summary",
      "matches": [
        {
          "job_title": "...",
          "match_score": 0-100 (int),
          "matched_skills": [...],
          "missing_skills": [...],
          "job_link": "https://...",
          "explain": "..."
        },
        ...
      ],
      "notes": "optional"
    }
    """
    # Config check
    if GENAI_CONFIG_ERROR:
        return {
            "candidate_id": None,
            "summary": "",
            "matches": [],
            "notes": "gemini_config_error",
            "error_details": GENAI_CONFIG_ERROR,
        }

    # Attempt to instantiate model wrapper
    try:
        model = genai.GenerativeModel(MODEL)
    except Exception as e:
        models_list = _list_available_models()
        return {
            "candidate_id": None,
            "summary": "",
            "matches": [],
            "notes": "gemini_model_init_error",
            "error_details": str(e),
            "available_models_sample": models_list,
        }

    # Strong instruction to include LinkedIn/Glassdoor-style job_link and return strict JSON
    prompt = f"""
You are a job recommendation assistant.

Given the candidate resume and preferences below, suggest 3–5 job roles that match best.

For each suggestion include:
  - job_title (string)
  - match_score (0-100, integer)
  - matched_skills (list of strings)
  - missing_skills (list of strings)
  - job_link (string URL)

About job_link:
- Prefer realistic links that LOOK like real job postings on sites such as:
  - https://www.linkedin.com/jobs/...
  - https://www.glassdoor.com/Job/...
- If you are not sure of an exact job posting URL, you can provide a generic
  LinkedIn jobs SEARCH URL using the job title and city (e.g. a URL with
  /jobs/search?keywords=...&location=...).
- The important part is that job_link is a string that looks like a real job search/posting URL.
- Do NOT leave job_link empty.

**Important**: Return exactly ONE JSON object and nothing else.
The JSON must have a top-level "matches" key which is a list.

Example shape:
{{
  "candidate_id": null,
  "summary": "short summary",
  "matches": [
    {{
      "job_title": "Machine Learning Engineer Intern",
      "match_score": 92,
      "matched_skills": ["Python","TensorFlow"],
      "missing_skills": ["MLOps"],
      "job_link": "https://www.linkedin.com/jobs/view/123456789/"
    }}
  ],
  "notes": ""
}}

Resume:
{resume_text}

City: {city}
Experience: {experience}
Domain: {domain}
"""

    try:
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or str(response)
        parsed = safe_json_parse(text.strip())

        # Ensure matches is present and a list
        if "matches" not in parsed or not isinstance(parsed.get("matches"), list):
            parsed["matches"] = []

        # Normalize matches and ensure job_link exists (fallback to synthetic LinkedIn search URL)
        safe_matches = []
        for m in parsed.get("matches", []):
            if not isinstance(m, dict):
                continue

            job_title = m.get("job_title", "") or ""
            try:
                score = int(round(float(m.get("match_score", 0))))
            except Exception:
                score = 0

            matched_skills = m.get("matched_skills", [])
            if not isinstance(matched_skills, list):
                matched_skills = []

            missing_skills = m.get("missing_skills", [])
            if not isinstance(missing_skills, list):
                missing_skills = []

            job_link = m.get("job_link", "") or ""
            if not isinstance(job_link, str) or not job_link.strip():
                # Fallback: build a LinkedIn jobs search URL using title+city
                job_link = _make_synthetic_job_link(job_title, city)

            safe_matches.append(
                {
                    "job_title": job_title,
                    "match_score": max(0, min(100, score)),
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "job_link": job_link,
                    "explain": m.get("explain", "") or "",
                }
            )

        parsed["matches"] = safe_matches
        if "candidate_id" not in parsed:
            parsed["candidate_id"] = None
        if "summary" not in parsed:
            parsed["summary"] = ""
        if "notes" not in parsed:
            parsed["notes"] = ""

        return parsed

    except Exception as e:
        err_text = str(e)
        if "not found" in err_text or "unsupported" in err_text:
            models = _list_available_models()
            return {
                "candidate_id": None,
                "summary": "",
                "matches": [],
                "notes": "gemini_model_not_found",
                "error_details": err_text,
                "available_models_sample": models,
            }
        return {
            "candidate_id": None,
            "summary": "",
            "matches": [],
            "notes": "gemini_api_error",
            "error_details": err_text,
        }
