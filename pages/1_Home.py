# pages/1_Home.py

import streamlit as st
from datetime import datetime
from urllib.parse import quote_plus  # 👈 for YouTube search URLs

from ui import render_topbar
from resume_tools import extract_text_from_uploaded_file
from jobs_api_gpt import match_jobs_with_gpt
from db import get_mongo_collection
from save_tools import save_single_job


def main():
    st.set_page_config(page_title="GPT Job Matcher - Home", page_icon="💼", layout="wide")

    # --- Session state init for storing last search ---
    if "last_search" not in st.session_state:
        st.session_state["last_search"] = None

    render_topbar(active="Home")
    st.title("💼 AI-Powered Job Matcher")

    user = st.session_state.get("user")
    user_email = user.get("email") if user else None

    if not user_email:
        st.info("You are not logged in. You can still find jobs, but saving them requires login (see Login page).")
    else:
        st.caption(f"Logged in as **{user_email}**")

    # --- Resume input ---
    tab_upload, tab_paste = st.tabs(["📄 Upload Resume", "✍️ Paste Resume Text"])
    resume_text = ""

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF, DOCX, TXT, etc.)",
            type=["pdf", "docx", "txt", "doc"],
        )
        if uploaded_file is not None:
            with st.spinner("Reading resume..."):
                resume_text = extract_text_from_uploaded_file(uploaded_file)
            if resume_text:
                st.success("Resume text extracted.")
                with st.expander("Show extracted text"):
                    st.text_area("Extracted resume text", resume_text, height=250)
            else:
                st.warning("Could not extract text from the file. Try the Paste tab.")

    with tab_paste:
        manual_text = st.text_area("Paste your resume content here", height=280)
        if manual_text.strip():
            resume_text = manual_text.strip()

    # --- Filters ---
    st.subheader("🎯 Preferences (optional)")
    col1, col2, col3 = st.columns(3)

    with col1:
        city = st.text_input("Preferred city / location", placeholder="e.g. Bangalore, Remote, Any")
    with col2:
        experience = st.text_input("Experience level", placeholder="e.g. Fresher, 1–2 years")
    with col3:
        domain = st.text_input("Preferred domain", placeholder="e.g. AI/ML, Web Development")

    search_button = st.button("🔍 Find Jobs", type="primary")

    # 1) If Find Jobs clicked → call Gemini, store result in session_state
    if search_button:
        if not resume_text.strip():
            st.error("Please upload or paste your resume content first.")
            return

        with st.spinner("Talking to Gemini and finding matches..."):
            result = match_jobs_with_gpt(
                resume_text=resume_text,
                city=city,
                experience=experience,
                domain=domain,
            )

        st.success("Job matches generated!")

        # Save in Mongo job_matches collection (optional logging)
        try:
            db, col = get_mongo_collection()
            col.insert_one(
                {
                    "user_email": user_email,
                    "resume_text": resume_text,
                    "filters": {
                        "city": city,
                        "experience": experience,
                        "domain": domain,
                    },
                    "result": result,
                    "created_at": datetime.utcnow(),
                }
            )
        except Exception as e:
            st.warning(f"Could not log this search in MongoDB: {e}")

        # 👉 Store the full search result & filters in session_state
        st.session_state["last_search"] = {
            "resume_text": resume_text,
            "city": city,
            "experience": experience,
            "domain": domain,
            "result": result,
        }

    # 2) Always render from st.session_state["last_search"]
    last_search = st.session_state.get("last_search")

    if not last_search:
        st.info("Run a search to see matching jobs.")
        return

    result = last_search["result"]
    city = last_search["city"]
    experience = last_search["experience"]
    domain = last_search["domain"]

    if result.get("summary"):
        st.subheader("📌 Profile Summary")
        st.write(result["summary"])

    st.subheader("📋 Matching Jobs")

    matches = result.get("matches") or []
    if not matches:
        st.info("No matches returned by the model. Try adjusting your preferences or resume.")
        return

    st.caption(f"Found {len(matches)} matches")

    # 3) Show each job + Save button + clickable missing skill chips
    for idx, job in enumerate(matches):
        with st.container(border=True):
            title = job.get("job_title", "(no title)")
            score = job.get("match_score", "")

            st.markdown(f"### {title} — {score}")

            if job.get("company"):
                st.write("**Company:**", job["company"])
            if job.get("location"):
                st.write("**Location:**", job["location"])

            if job.get("matched_skills"):
                st.write("**Matched skills:**", ", ".join(job.get("matched_skills")))

            # 🔴 NEW: Missing skills → YouTube links
            missing_skills = job.get("missing_skills") or []
            if missing_skills:
                st.write("**Missing skills (click to learn):**")
                # Show them as small link buttons
                skill_cols = st.columns(min(4, len(missing_skills)))
                for i, skill in enumerate(missing_skills):
                    col = skill_cols[i % len(skill_cols)]
                    with col:
                        query = quote_plus(f"{skill} tutorial for beginners")
                        youtube_url = f"https://www.youtube.com/results?search_query={query}"
                        st.link_button(skill, youtube_url)

            if job.get("job_link"):
                st.markdown(f"[🔗 View Job Posting]({job['job_link']})")

            if job.get("summary"):
                st.write("**Summary:**", job["summary"])
            if job.get("explain"):
                st.write("*Why this job?*", job["explain"])

            cols_btn = st.columns([1, 4])
            with cols_btn[0]:
                if user_email:
                    if st.button("💾 Save", key=f"save_job_{idx}"):
                        try:
                            save_single_job(
                                user_email=user_email,
                                match_obj=job,
                                context={
                                    "city": city,
                                    "experience": experience,
                                    "domain": domain,
                                },
                            )
                            st.success("Job saved!")
                        except Exception as e:
                            st.error(f"Failed to save job: {e}")
                else:
                    st.caption("Login to save this job.")

    st.markdown("---")
    st.caption("Tip: Click any missing skill to jump straight to YouTube tutorials for that topic.")


if __name__ == "__main__":
    main()
