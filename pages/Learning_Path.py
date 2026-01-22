import streamlit as st
from urllib.parse import quote_plus
from datetime import datetime
import os

from ui import render_topbar
from db import get_collection
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
def generate_learning_path(missing_skills, target_role, experience, resume_text):
    if GEMINI_ERROR or not client:
        return f"❌ Gemini error: {GEMINI_ERROR}"

    if not missing_skills:
        return "No missing skills selected."

    resume_text = (resume_text or "")[:3000]
    skills_list = ", ".join(missing_skills)

    prompt = f"""
You are a senior technical mentor.

Target role: {target_role or "Software Engineer"}
Experience level: {experience or "Fresher"}

Candidate resume:
{resume_text}

Missing skills:
{skills_list}

Create a PHASE-WISE learning roadmap.
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
        return f"❌ Error while generating learning path: {e}"

# ================= STREAMLIT PAGE =================
def main():
    st.set_page_config(page_title="Learning Path", page_icon="📚", layout="wide")

    render_topbar(active="Learning Path")
    st.title("📚 Personalized Learning Path")

    user = st.session_state.get("user")
    user_email = user.get("email") if user else None

    last_search = st.session_state.get("last_search") or {}
    result = last_search.get("result") or {}
    matches = result.get("matches") or []

    resume_text = last_search.get("resume_text", "")
    experience = last_search.get("experience", "")
    default_domain = last_search.get("domain", "")

    if not matches:
        st.warning("Run a job search first.")
        return

    missing_skills = sorted(
        {s.strip() for j in matches for s in (j.get("missing_skills") or []) if s}
    )

    selected_skills = st.multiselect(
        "Missing skills",
        options=missing_skills,
        default=missing_skills,
    )

    target_role = st.text_input(
        "Target role",
        value=default_domain or "Software Engineer",
    )

    if st.button("✨ Generate Learning Path"):
        with st.spinner("Generating roadmap..."):
            roadmap_md = generate_learning_path(
                selected_skills,
                target_role,
                experience,
                resume_text,
            )

        st.markdown("---")
        st.markdown(roadmap_md)

        if user_email:
            try:
                get_collection("learning_paths").insert_one(
                    {
                        "user_email": user_email,
                        "skills": selected_skills,
                        "target_role": target_role,
                        "experience": experience,
                        "roadmap_md": roadmap_md,
                        "created_at": datetime.utcnow(),
                    }
                )
                st.success("Learning path saved.")
            except Exception as e:
                st.error(e)

if __name__ == "__main__":
    main()
