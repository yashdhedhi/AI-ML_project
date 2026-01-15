# pages/7_Interview_Prep.py

import streamlit as st
from urllib.parse import quote_plus
import os

from ui import render_topbar
from dotenv import load_dotenv

# ✅ NEW Gemini SDK
from google import genai

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

def generate_interview_questions(
    company: str,
    role: str,
    skills: list[str],
    resume_text: str,
    difficulty: str,
    num_questions: int,
):
    """
    Generate interview questions using Gemini (Markdown output).
    """

    if GEMINI_ERROR:
        return f"**[Configuration Error]** {GEMINI_ERROR}"

    skills_str = ", ".join(skills) if skills else "not specified"
    resume_text = (resume_text or "")[:3000]

    prompt = f"""
You are an experienced technical interviewer.

Create **{num_questions} interview questions** for this candidate:

Company: {company or "Generic tech company"}
Role: {role or "Software Engineer"}
Skills: {skills_str}
Difficulty: {difficulty}

Candidate resume:
{resume_text}

Guidelines:
- Mix technical, coding/DSA, system design (if applicable), and behavioral questions
- Tailor questions to role and skills
- Include role-relevant questions (ML/DS, backend, frontend, etc.)

Formatting rules (IMPORTANT):
- Output **Markdown only**
- Use this structure:

### Q1. <Short title>
**Type:** <Technical / DSA / System Design / Behavioral>  
**Difficulty:** <Easy / Medium / Hard>

**Question:**  
Question text here...

**What a good answer should cover:**
- Point 1
- Point 2
- Point 3

Do NOT include JSON.
Do NOT add explanations or disclaimers.
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        # Safely extract text
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return response.candidates[0].content.parts[0].text.strip()

    except Exception as e:
        return f"❌ Error while generating questions: {e}"

# ================= STREAMLIT PAGE =================

def main():
    st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

    render_topbar(active="Interview")
    st.title("🎤 AI Interview Preparation")

    st.markdown(
        """
Prepare for **company-specific interviews** with:
- 🔗 Real interview question links (Glassdoor, Google, LeetCode)
- ✨ AI-generated mock interview questions based on your resume
        """
    )

    user = st.session_state.get("user")
    if user:
        st.caption(f"👤 Logged in as **{user.get('email','')}**")

    # ================= CONTEXT FROM LAST SEARCH =================

    last_search = st.session_state.get("last_search", {})
    base_resume = last_search.get("resume_text", "")
    base_domain = last_search.get("domain", "")

    collected_skills = set()
    for job in (last_search.get("result", {}).get("matches") or []):
        for s in (job.get("matched_skills") or []) + (job.get("missing_skills") or []):
            if s:
                collected_skills.add(s.strip())

    # ================= INPUTS =================

    st.subheader("🏢 Target Company & Role")

    company = st.text_input("Company name", placeholder="e.g. Google, Amazon, TCS")
    role = st.text_input(
        "Role / Position",
        value=base_domain or "Software Engineer",
        placeholder="e.g. SDE-1, Backend Developer",
    )

    st.subheader("⚙️ Question Settings")
    difficulty = st.selectbox("Difficulty level", ["Mixed", "Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of AI-generated questions", 5, 25, 10)

    st.subheader("🧩 Skills to focus on")
    skills_list = sorted(collected_skills)
    selected_skills = st.multiselect(
        "Skills",
        options=skills_list,
        default=skills_list,
    )

    extra_skill = st.text_input("Add extra skill (optional)")
    if extra_skill and extra_skill not in selected_skills:
        selected_skills.append(extra_skill.strip())

    st.markdown("---")

    # ================= REAL LINKS =================

    st.subheader("🔗 Real Interview Questions (External)")
    if company:
        google_q = quote_plus(f"{company} {role} interview questions")
        glassdoor_q = quote_plus(f"{company} interview questions glassdoor")
        leetcode_slug = quote_plus(company.lower())

        col1, col2 = st.columns(2)
        with col1:
            st.link_button("🔍 Google interview questions", f"https://www.google.com/search?q={google_q}")
            st.link_button("🟡 Glassdoor interview experiences", f"https://www.google.com/search?q={glassdoor_q}")
        with col2:
            st.link_button("🧩 LeetCode company questions", f"https://leetcode.com/company/{leetcode_slug}/")
    else:
        st.info("Enter a company name to see interview links.")

    st.markdown("---")

    # ================= AI GENERATION =================

    st.subheader("✨ AI-Generated Mock Interview")

    if GEMINI_ERROR:
        st.error(GEMINI_ERROR)
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

# ================= ENTRY =================

if __name__ == "__main__":
    main()
