from __future__ import annotations
import os, json, re
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load .env for local dev
load_dotenv()

# NEW Gemini API
from google import genai

# Configure API
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment variables.")

client = genai.Client(api_key=GEMINI_KEY)

MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.0-flash")

def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except:
                pass
    return {"matches": [], "raw_model_output": text[:300]}


def _slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    s = re.sub(r"\s+", "-", s)
    return s[:60]


def _make_link(job, city):
    job_q = quote_plus(job)
    city_q = quote_plus(city)
    return f"https://www.linkedin.com/jobs/search?keywords={job_q}&location={city_q}"


def match_jobs_with_gpt(resume_text, city, experience, domain):

    prompt = f"""
You are a job matching AI.

Return STRICT JSON with this format ONLY:

{{
  "summary": "...",
  "matches": [
    {{
      "job_title": "...",
      "match_score": 0-100,
      "matched_skills": [...],
      "missing_skills": [...],
      "job_link": "https://linkedin.com/jobs/..."
    }}
  ]
}}

Candidate:
Resume: {resume_text}
City: {city}
Experience: {experience}
Domain: {domain}

Return ONLY JSON.
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        text = response.text
        parsed = safe_json_parse(text)

        final_matches = []
        for m in parsed.get("matches", []):
            title = m.get("job_title", "Unknown Role")
            city_val = city or ""
            link = m.get("job_link") or _make_link(title, city_val)

            final_matches.append(
                {
                    "job_title": title,
                    "match_score": int(m.get("match_score", 0)),
                    "matched_skills": m.get("matched_skills", []),
                    "missing_skills": m.get("missing_skills", []),
                    "job_link": link,
                }
            )

        return {
            "summary": parsed.get("summary", ""),
            "matches": final_matches,
            "notes": "success_new_gemini_api"
        }

    except Exception as e:
        return {
            "summary": "",
            "matches": [],
            "error": str(e)
        }
