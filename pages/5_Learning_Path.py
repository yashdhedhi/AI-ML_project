# pages/5_Learning_Path.py

import streamlit as st
from urllib.parse import quote_plus
from datetime import datetime
import os

from ui import render_topbar
from db import get_collection  # 👈 NEW: for MongoDB

# Gemini (google.generativeai) like in jobs_api_gpt.py
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "models/gemini-2.5-flash")

if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_ERROR = None
    except Exception as e:
        GEMINI_ERROR = str(e)
else:
    GEMINI_ERROR = "GOOGLE_API_KEY not set in environment variables (.env)."


def generate_learning_path(missing_skills, target_role, experience, resume_text):
    """
    Ask Gemini to create a structured learning roadmap based on missing skills.
    Returns markdown text.
    """
    if GEMINI_ERROR:
        return f"**[Config error]** Gemini is not configured: {GEMINI_ERROR}"

    if not missing_skills:
        return "No missing skills selected. Please choose at least one skill."

    skills_list = ", ".join(missing_skills)
    prompt = f"""
You are a senior technical mentor.

The user is aiming for this target role: "{target_role or "Software Engineer"}"
Experience level: "{experience or "Fresher"}"

Here is their resume (possibly partial or rough):
{resume_text}

Here are the key MISSING SKILLS that job postings are asking for:
{skills_list}

Your task:
1. Create a **phase-wise learning roadmap** (Phase 1, Phase 2, Phase 3, ...) to cover these missing skills.
2. For each phase:
   - List which skills to focus on.
   - Break down each skill into 3–6 concrete topics to learn.
   - Suggest 1–3 mini-project ideas.
3. Keep the tone encouraging and clear.
4. Format everything in clean Markdown with headings and bullet points.
5. DO NOT output JSON, just human-readable Markdown.

Important:
- Assume the user has basic programming knowledge.
- Order the phases from easiest / most fundamental skills to more advanced.
"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or str(response)
        return text.strip()
    except Exception as e:
        return f"Error while calling Gemini: {e}"


def main():
    st.set_page_config(page_title="Learning Path", page_icon="📚", layout="wide")

    render_topbar(active="About")  # just highlights something in navbar
    st.title("📚 Personalized Learning Path")

    user = st.session_state.get("user")
    user_email = user.get("email") if user else None

    st.markdown(
        """
This page builds a **learning roadmap** from the skills you were missing in your last job search.

1. Run a job search on the **Home** page.
2. Come here, and I’ll show the missing skills and generate a learning path.
        """
    )

    if not user_email:
        st.warning("You are not logged in. You can still generate a roadmap, but saving history requires login.")
    else:
        st.caption(f"Logged in as **{user_email}**")

    # We rely on last_search set in 1_Home.py
    last_search = st.session_state.get("last_search")
    if not last_search:
        st.warning("No job search found. Please go to the Home page, run a search, and then come back here.")
        return

    result = last_search.get("result") or {}
    matches = result.get("matches") or []
    resume_text = last_search.get("resume_text", "")
    experience = last_search.get("experience", "")
    default_domain = last_search.get("domain", "")

    # --- Collect all unique missing skills across jobs ---
    missing_skills_set = set()
    for job in matches:
        for s in job.get("missing_skills") or []:
            s = (s or "").strip()
            if s:
                missing_skills_set.add(s)

    missing_skills_list = sorted(missing_skills_set, key=str.lower)

    if not missing_skills_list:
        st.info("No missing skills were detected from the last search. Try another search with a richer resume.")
        return

    st.subheader("🧩 Missing Skills Detected")
    st.write("These came from the jobs you just searched:")
    st.write(", ".join(missing_skills_list))

    # --- Skill selection ---
    st.subheader("🎯 Choose skills to focus on first")
    selected_skills = st.multiselect(
        "Select the skills you want to build a learning path for:",
        options=missing_skills_list,
        default=missing_skills_list,  # by default, all
    )

    extra_skill = st.text_input("Add any extra skill (optional)", placeholder="e.g. System Design")
    if extra_skill.strip():
        extra_skill_clean = extra_skill.strip()
        if extra_skill_clean not in selected_skills:
            selected_skills.append(extra_skill_clean)

    # --- Target role / domain ---
    st.subheader("👨‍💻 Target Role")
    target_role = st.text_input(
        "Your target role",
        value=default_domain or "Software Engineer",
        help="e.g. Backend Developer, Data Scientist, AI/ML Engineer",
    )

    # --- YouTube quick links for selected skills ---
    st.subheader("▶️ YouTube Tutorials for Selected Skills")
    st.caption("Click any skill to open YouTube search results for beginner-friendly tutorials.")
    for skill in selected_skills:
        cols = st.columns([1, 5])
        with cols[0]:
            query = quote_plus(f"{skill} tutorial for beginners")
            youtube_url = f"https://www.youtube.com/results?search_query={query}"
            st.link_button(skill, youtube_url)
        with cols[1]:
            st.write(f"Search: `{skill} tutorial for beginners`")

    st.markdown("---")

    # --- Generate learning path button ---
    st.subheader("📘 Generate Structured Learning Path")
    if GEMINI_ERROR:
        st.error(f"Gemini is not configured: {GEMINI_ERROR}")
        st.info("You can still use the YouTube links above, but AI roadmap won't work until the API key is set.")
        return

    if st.button("✨ Generate Learning Path with AI"):
        if not selected_skills:
            st.error("Please select at least one skill.")
        else:
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

            # ✅ Save to MongoDB if logged in
            if user_email:
                try:
                    col = get_collection("learning_paths")
                    doc = {
                        "user_email": user_email,
                        "skills": selected_skills,
                        "target_role": target_role,
                        "experience": experience,
                        "resume_excerpt": (resume_text or "")[:1000],
                        "roadmap_md": roadmap_md,
                        "created_at": datetime.utcnow(),
                    }
                    col.insert_one(doc)
                    st.success("Learning path saved to your history! Check 'My Learning Paths' page.")
                except Exception as e:
                    st.error(f"Failed to save learning path: {e}")
            else:
                st.info("Login to save this learning path in your history.")


if __name__ == "__main__":
    main()
