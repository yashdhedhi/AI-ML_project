# pages/7_Interview_Prep.py

import streamlit as st
from urllib.parse import quote_plus
import os

from ui import render_topbar

from dotenv import load_dotenv
import google.generativeai as genai

# --- Gemini setup (same style as other files) ---
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


def generate_interview_questions(
    company: str,
    role: str,
    skills: list[str],
    resume_text: str,
    difficulty: str,
    num_questions: int,
):
    """
    Use Gemini to generate mock interview questions.
    Returns markdown text (no JSON parsing needed).
    """
    if GEMINI_ERROR:
        return f"**[Config error]** Gemini is not configured: {GEMINI_ERROR}"

    skills_str = ", ".join(skills) if skills else "not specified"

    prompt = f"""
You are an experienced technical interviewer.

Design a set of **{num_questions} interview questions** for this candidate:

- Target company: {company or "Generic tech company"}
- Target role: {role or "Software Engineer"}
- Candidate skills: {skills_str}
- Difficulty level: {difficulty}
- Candidate resume (may be partial or noisy):
{resume_text}

Guidelines:
- Include a mix of different question types: technical (coding, CS fundamentals, system design if relevant),
  and behavioral / HR questions.
- Tailor questions to the specified role and skills as much as possible.
- If the role suggests DSA/competitive programming (Software Engineer, SDE, etc.), include some coding/DSA questions.
- If the role suggests ML/DS (Data Scientist, ML Engineer, etc.), include ML/DS/statistics questions.
- If the role is more frontend/backend specific, focus on relevant technologies and system design.

Formatting (VERY IMPORTANT):
- Output in **Markdown** only.
- For each question, use this structure:

### Q1. <short title>
**Type:** <Technical/DSA/System Design/Behavioral/etc.>  
**Difficulty:** <Easy/Medium/Hard>  

**Question:**  
Text of the question...

**What a good answer should cover (bullet points):**
- point 1
- point 2
- ...

- Do NOT include any JSON.
- Do NOT mention that you are an AI or add disclaimers. Just the questions and answer hints.
"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or str(response)
        return text.strip()
    except Exception as e:
        return f"Error while calling Gemini: {e}"


def main():
    st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

    render_topbar(active="About")  # just highlight some tab
    st.title("🎤 AI Interview Preparation")

    st.markdown(
        """
Use this page to prepare for **company-specific interviews**.

- I’ll give you links to **real interview questions** (Glassdoor / Google / etc.)
- And generate **custom mock questions** based on your resume and target role.
        """
    )

    user = st.session_state.get("user")
    user_email = user.get("email") if user else None
    if user_email:
        st.caption(f"Logged in as **{user_email}**")

    # --- Pull context from last job search (if available) ---
    last_search = st.session_state.get("last_search")
    base_resume = ""
    base_domain = ""
    collected_skills = set()

    if last_search:
        base_resume = last_search.get("resume_text", "") or ""
        base_domain = last_search.get("domain", "") or ""
        result = last_search.get("result") or {}
        matches = result.get("matches") or []
        for job in matches:
            for s in job.get("matched_skills") or []:
                s = (s or "").strip()
                if s:
                    collected_skills.add(s)
            for s in job.get("missing_skills") or []:
                s = (s or "").strip()
                if s:
                    collected_skills.add(s)

    # --- Inputs: company, role, difficulty, num questions ---
    st.subheader("🏢 Target Company & Role")

    company = st.text_input("Company name", placeholder="e.g. Google, TCS, Infosys")
    role = st.text_input(
        "Role / Position",
        value=base_domain or "Software Engineer",
        placeholder="e.g. SDE-1, Backend Developer, Data Scientist",
    )

    st.subheader("⚙️ Question Settings")
    difficulty = st.selectbox("Difficulty level", ["Mixed", "Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of AI-generated questions", 5, 25, 10)

    # --- Skills selection ---
    st.subheader("🧩 Skills to focus on")
    st.caption("These are taken from your last job search (matched + missing skills). You can also add your own.")

    collected_skills_list = sorted(collected_skills, key=str.lower) if collected_skills else []
    selected_skills = st.multiselect(
        "Skills for interview focus",
        options=collected_skills_list,
        default=collected_skills_list,
    )

    extra_skill = st.text_input("Add extra skill (optional)", placeholder="e.g. System Design, Operating Systems")
    if extra_skill.strip():
        extra_clean = extra_skill.strip()
        if extra_clean not in selected_skills:
            selected_skills.append(extra_clean)

    st.markdown("---")

    # --- Real interview question links section ---
    st.subheader("🔗 Real Interview Questions (External Resources)")
    if not company:
        st.info("Enter a company name above to see helpful links.")
    else:
        company_slug = company.strip()
        role_slug = role.strip() or "software engineer"

        # Build search queries
        google_q = quote_plus(f"{company_slug} {role_slug} interview questions")
        google_url = f"https://www.google.com/search?q={google_q}"

        glassdoor_q = quote_plus(f"{company_slug} interview questions glassdoor")
        glassdoor_url = f"https://www.google.com/search?q={glassdoor_q}"

        gfg_q = quote_plus(f"{company_slug} interview questions geeksforgeeks")
        gfg_url = f"https://www.google.com/search?q={gfg_q}"

        leetcode_slug = quote_plus(company_slug.lower())
        leetcode_url = f"https://leetcode.com/company/{leetcode_slug}/"

        col_links = st.columns(2)
        with col_links[0]:
            st.link_button("🔍 Google search: company interview questions", google_url)
            st.link_button("🟢 GeeksforGeeks questions (search)", gfg_url)
        with col_links[1]:
            st.link_button("🟡 Glassdoor interview experiences (search)", glassdoor_url)
            st.link_button("🧩 LeetCode company questions", leetcode_url)

    st.markdown("---")

    # --- AI question generation ---
    st.subheader("✨ AI-Generated Mock Interview")
    if GEMINI_ERROR:
        st.error(f"Gemini is not configured: {GEMINI_ERROR}")
        st.info("External links above will still work, but AI question generation needs a valid API key.")
        return

    if st.button("🎯 Generate AI Interview Questions"):
        if not company and not role:
            st.error("Please enter at least a company or a role.")
            return

        with st.spinner("Generating interview questions..."):
            questions_md = generate_interview_questions(
                company=company,
                role=role,
                skills=selected_skills,
                resume_text=base_resume,
                difficulty=difficulty,
                num_questions=num_questions,
            )

        st.markdown("---")
        st.subheader("📝 Mock Interview Questions")
        st.markdown(questions_md)


if __name__ == "__main__":
    main()
