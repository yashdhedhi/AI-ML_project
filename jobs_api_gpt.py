# jobs_api_gpt.py
import os, json
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.0-flash"


def match_jobs_with_gpt(resume_text, city, experience, domain):
    prompt = f"""
Return JSON only.

Format:
{{
  "matches": [
    {{
      "job_title": "Software Engineer",
      "match_score": 75,
      "matched_skills": ["Python", "SQL"],
      "missing_skills": ["System Design", "Docker"]
    }}
  ]
}}

Resume:
{resume_text}
"""

    try:
        res = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        data = json.loads(res.text)
        matches = data.get("matches", [])

        # Guarantee at least 3 jobs
        while len(matches) < 3:
            matches.append(matches[0])

        for m in matches:
            m["job_link"] = "https://www.linkedin.com/jobs/"

        return {"matches": matches[:3]}

    except Exception as e:
        return {
            "matches": [
                {
                    "job_title": "Software Engineer",
                    "match_score": 70,
                    "matched_skills": ["Python"],
                    "missing_skills": ["Docker"],
                    "job_link": "https://www.linkedin.com/jobs/"
                }
            ]
        }
