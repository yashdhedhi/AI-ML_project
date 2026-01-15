# pages/5_Learning_Path.py

import streamlit as st
from urllib.parse import quote_plus
from datetime import datetime
import os

from ui import render_topbar
from db import get_collection

from dotenv import load_dotenv
from google import genai   # ✅ NEW Gemini SDK

# ================= ENV SETUP =================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-1.5-flash")

if not GEMINI_API_KEY:
    GEMINI_ERROR = "GEMINI_API_KEY not set in environment variables."
else:
    GEMINI_ERROR = None
    client = genai.Client(api_key=GEMINI_API_KEY)

# ================= GEMINI FUNCTION =================

def generate_learning_path(missing_skills, target_role, experience, resume_text):
    """
    Generate a structured learning roadmap using Gemini.
    Returns Markdown text.
    """

    if GEMINI_ERROR:
        return f"**[Configuration Error]** {GEMINI_ERROR}"

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

Missing skills to learn:
{skills_list}

Your task:
1. Create a **phase-wise learning roadmap** (Phase 1, Phase 2, Phase 3, ...)
2. For each phase:
   - Skills to focus on
   - 3–6 concrete topics per skill
   - 1–3 mini-project ideas
3. Keep explanations clear and encouraging
4. Use **Markdown only**
5. Do NOT return JSON

Guidelines:
- Assume basic programming knowledge
- Order phases from fundamentals → advanced
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        # Safe text extraction
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return response.candidates[0].content.parts[0].text.strip()

    except Exception as e:
        return f"❌ Error while generating learning path: {e}"

# ================= STREAMLIT PAGE =================

def main():
    st.set_page_config(page_title="Learning Path", page_icon="📚", layout="wide")

    render_topbar(active="Learning Path")
    st.title("📚 Personalized Learning Path")

    user = st.session_state.get("user")
    user_email = user.get("email") if user else None

    st.markdown(
        """
This page creates a **personalized learning roadmap** from the skills
you were missing in your last job search.

**Steps:**
1. Run a job search on the Home page
2. Come here to generate your learning path
        """
    )

    if user_email:
        st.caption(f"👤 Logged in as **{user_email}**")
    else:
        st.warning("You are not logged in. You can generate a roadmap, but it won’t be saved.")

    # ================= LOAD LAST SEARCH =================

    last_search = st.session_state.get("last_search")
    if not last_search:
        st.warning("No job search found. Please run a job search on the Home page first.")
        return

    result = last_search.get("result", {})
    matches = result.get("matches", [])
    resume_text = last_search.get("resume_text", "")
    experience = last_search.get("experience", "")
    default_domain = last_search.get("domain", "")

    # ================= COLLECT MISSING SKILLS =================

    missing_skills_set = set()
    for job in matches:
        for s in job.get("missing_skills") or []:
            if s:
                missing_skills_set.add(s.strip())

    missing_skills_list = sorted(missing_skills_set, key=str.lower)

    if not missing_skills_list:
        st.info("No missing skills detected from the last search.")
        return

    st.subheader("🧩 Missing Skills Detected")
    st.write(", ".join(missing_skills_list))

    # ================= SKILL SELECTION =================

    st.subheader("🎯 Choose skills to focus on")
    selected_skills = st.multiselect(
        "Select skills:",
        options=missing_skills_list,
        default=missing_skills_list,
    )

    extra_skill = st.text_input("Add extra skill (optional)")
    if extra_skill and extra_skill not in selected_skills:
        selected_skills.append(extra_skill.strip())

    # ================= TARGET ROLE =================

    st.subheader("👨‍💻 Target Role")
    target_role = st.text_input(
        "Target role",
        value=default_domain or "Software Engineer",
    )

    # ================= YOUTUBE LINKS =================

    st.subheader("▶️ YouTube Tutorials")
    st.caption("Click a skill to open YouTube tutorials.")

    for skill in selected_skills:
        yt_query = quote_plus(f"{skill} tutorial for beginners")
        yt_url = f"https://www.youtube.com/results?search_query={yt_query}"
        st.link_button(skill, yt_url)

    st.markdown("---")

    # ================= GENERATE LEARNING PATH =================

    st.subheader("📘 Generate Learning Path")

    if GEMINI_ERROR:
        st.error(GEMINI_ERROR)
        return

    if st.button("✨ Generate Learning Path with AI"):
        if not selected_skills:
            st.error("Please select at least one skill.")
            return

        with st.spinner("Generating your personalized learning roadmap..."):
            roadmap_md = generate_learning_path(
                missing_skills=selected_skills,
                target_role=target_role,
                experience=experience,
                resume_text=resume_text,
            )

        st.markdown("---")
        st.subheader("🛣️ Your Learning Path")
        st.markdown(roadmap_md)

        # ================= SAVE TO MONGODB =================

        if user_email:
            try:
                col = get_collection("learning_paths")
                col.insert_one(
                    {
                        "user_email": user_email,
                        "skills": selected_skills,
                        "target_role": target_role,
                        "experience": experience,
                        "resume_excerpt": resume_text[:1000],
                        "roadmap_md": roadmap_md,
                        "created_at": datetime.utcnow(),
                    }
                )
                st.success("Learning path saved! Check **My Learning Paths**.")
            except Exception as e:
                st.error(f"Failed to save learning path: {e}")
        else:
            st.info("Login to save this learning path.")

# ================= ENTRY =================

if __name__ == "__main__":
    main()
