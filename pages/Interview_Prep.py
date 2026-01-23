import streamlit as st
from urllib.parse import quote_plus
import os, time

from ui import render_topbar
from dotenv import load_dotenv

# ================= SAFE GEMINI IMPORT =================
Client = None
genai = None

try:
    from google.genai import Client
except Exception:
    try:
        import google.generativeai as genai
    except Exception:
        pass


# ================= RATE LIMIT (ANTI 429) =================
def gemini_rate_limit(seconds: int = 25):
    last = st.session_state.get("_last_gemini_call", 0)
    now = time.time()

    if now - last < seconds:
        wait = int(seconds - (now - last))
        st.warning(f"⏳ Please wait {wait}s before next request")
        return False

    st.session_state["_last_gemini_call"] = now
    return True


# ================= ENV =================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.0-flash")

client = None
GEMINI_ERROR = None

if GEMINI_API_KEY:
    try:
        if Client:
            client = Client(api_key=GEMINI_API_KEY)
        elif genai:
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai
        else:
            GEMINI_ERROR = "Gemini SDK missing"
    except Exception as e:
        GEMINI_ERROR = str(e)
else:
    GEMINI_ERROR = "GEMINI_API_KEY not set"


# ================= CACHED GEMINI =================
@st.cache_data(ttl=600)
def cached_generate(prompt: str):
    if Client:
        r = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return r.text
    else:
        model = client.GenerativeModel(GEMINI_MODEL)
        return model.generate_content(prompt).text


# ================= GEMINI FUNCTION =================
def generate_interview_questions(company, role, skills, resume_text, difficulty, num_questions):

    if GEMINI_ERROR or not client:
        return f"❌ {GEMINI_ERROR}"

    skills_str = ", ".join(skills) if skills else "General"

    resume_text = (resume_text or "")[:1500]  # reduce tokens

    prompt = f"""
Create {num_questions} interview questions.

Role: {role}
Company: {company}
Difficulty: {difficulty}
Skills: {skills_str}

Resume:
{resume_text}

Markdown only.
"""

    try:
        return cached_generate(prompt)
    except Exception as e:
        return f"❌ API Error: {e}"


# ================= PAGE =================
def main():
    st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

    render_topbar(active="Interview")
    st.title("🎤 AI Interview Preparation")

    last_search = st.session_state.get("last_search") or {}
    result = last_search.get("result") or {}
    matches = result.get("matches") or []

    resume_text = last_search.get("resume_text", "")

    skills = {
        s
        for j in matches
        for s in (j.get("matched_skills", []) + j.get("missing_skills", []))
    }

    company = st.text_input("Company")
    role = st.text_input("Role", value="Software Engineer")

    difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"])
    num_questions = st.slider("Questions", 5, 25, 10)

    selected_skills = st.multiselect("Skills", sorted(skills), default=sorted(skills))

    if st.button("🎯 Generate Interview Questions"):

        if not gemini_rate_limit():
            return

        with st.spinner("Generating..."):
            output = generate_interview_questions(
                company, role, selected_skills, resume_text, difficulty, num_questions
            )

        st.markdown(output)


if __name__ == "__main__":
    main()
