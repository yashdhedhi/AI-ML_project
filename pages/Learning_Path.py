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
    from google.genai import Client  # New SDK
except Exception:
    try:
        import google.generativeai as genai  # Old SDK fallback
    except Exception:
        pass

# ================= ENV SETUP =================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.0-flash")

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

FORMAT STRICTLY IN MARKDOWN.
NO JSON.
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
        st.warning("Run a job search on the Home page first.")
        return

    # -------- MISSING SKILLS --------
    missing_skills = sorted({
        s.strip()
        for job in matches
        for s in (job.get("missing_skills") or [])
        if s
    })

    st.subheader("🧩 Missing Skills")
    st.write(", ".join(missing_skills))

    selected_skills = st.multiselect(
        "Select skills to learn",
        options=missing_skills,
        default=missing_skills,
    )

    target_role = st.text_input("Target role", value=default_domain or "Software Engineer")

    st.subheader("▶️ YouTube Tutorials")
    for skill in selected_skills:
        yt_url = f"https://www.youtube.com/results?search_query={quote_plus(skill + ' tutorial')}"
        st.link_button(skill, yt_url)

    st.markdown("---")

    if st.button("✨ Generate Learning Path"):
        with st.spinner("Generating learning path..."):
            roadmap = generate_learning_path(
                selected_skills,
                target_role,
                experience,
                resume_text,
            )

        st.markdown("---")
        st.markdown(roadmap)

        if user_email:
            try:
                col = get_collection("learning_paths")
                col.insert_one({
                    "user_email": user_email,
                    "skills": selected_skills,
                    "target_role": target_role,
                    "experience": experience,
                    "roadmap_md": roadmap,
                    "created_at": datetime.utcnow(),
                })
                st.success("Learning path saved!")
            except Exception as e:
                st.error(f"Save failed: {e}")


if __name__ == "__main__":
    main()
