import streamlit as st
from urllib.parse import quote_plus
import os

from ui import render_topbar
from dotenv import load_dotenv

# ================= SAFE GEMINI IMPORT =================
Client = None
genai = None

try:
    from google.genai import Client  # NEW SDK
except Exception:
    try:
        import google.generativeai as genai  # OLD SDK
    except Exception:
        pass

# ================= ENV SETUP =================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ✅ RENDER-SAFE MODEL
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-1.0-pro")

client = None
GEMINI_ERROR = None

if not GEMINI_API_KEY:
    GEMINI_ERROR = "GEMINI_API_KEY not set in environment variables."
else:
    try:
        if Client:
            client = Client(api_key=GEMINI_API_KEY)
        elif genai:
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai
        else:
            GEMINI_ERROR = "No Gemini SDK available"
    except Exception as e:
        GEMINI_ERROR = str(e)

# ================= GEMINI FUNCTION =================
def generate_interview_questions(
    company,
    role,
    skills,
    resume_text,
    difficulty,
    num_questions,
):
    if GEMINI_ERROR or not client:
        return f"❌ Gemini error: {GEMINI_ERROR}"

    skills_str = ", ".join(skills) if skills else "General programming"
    resume_text = (resume_text or "")[:3000]

    prompt = f"""
You are an experienced technical interviewer.

Create {num_questions} interview questions.

Company: {company or "Tech Company"}
Role: {role or "Software Engineer"}
Difficulty: {difficulty}
Skills: {skills_str}

Candidate resume:
{resume_text}

FORMAT IN MARKDOWN ONLY.
"""

    try:
        if Client:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()
        else:
            model = client.GenerativeModel(GEMINI_MODEL)
            return model.generate_content(prompt).text.strip()

    except Exception as e:
        return f"❌ Error while generating questions: {e}"

# ================= STREAMLIT PAGE =================
def main():
    st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

    render_topbar(active="Interview")
    st.title("🎤 AI Interview Preparation")

    last_search = st.session_state.get("last_search") or {}
    resume_text = last_search.get("resume_text", "")
    result = last_search.get("result") or {}
    matches = result.get("matches") or []

    collected_skills = set()
    for job in matches:
        collected_skills.update(job.get("matched_skills", []))
        collected_skills.update(job.get("missing_skills", []))

    if not matches:
        st.info("Run a job search on the Home page to personalize interview questions.")

    company = st.text_input("Company")
    role = st.text_input("Role", value="Software Engineer")

    difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"])
    num_questions = st.slider("Questions", 5, 25, 10)

    selected_skills = st.multiselect(
        "Skills",
        options=sorted(collected_skills),
        default=sorted(collected_skills),
    )

    if st.button("🎯 Generate Interview Questions"):
        with st.spinner("Generating interview questions..."):
            output = generate_interview_questions(
                company,
                role,
                selected_skills,
                resume_text,
                difficulty,
                num_questions,
            )
        st.markdown("---")
        st.markdown(output)

if __name__ == "__main__":
    main()
