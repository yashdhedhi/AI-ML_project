# pages/1_Home.py

import streamlit as st
from datetime import datetime
from urllib.parse import quote_plus

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
        st.info("You are not logged in. You can still find jobs, but saving them requires login.")
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
        if uploaded_file:
            with st.spinner("Reading resume..."):
                resume_text = extract_text_from_uploaded_file(uploaded_file)
            if resume_text:
                st.success("Resume text extracted.")
                with st.expander("Show extracted text"):
                    st.text_area("Extracted resume text", resume_text, height=250)
            else:
                st.warning("Could not extract text. Try paste option.")

    with tab_paste:
        manual_text = st.text_area("Paste your resume content here", height=280)
        if manual_text.strip():
            resume_text = manual_text.strip()

    # --- Filters ---
    st.subheader("🎯 Preferences (optional)")
    col1, col2, col3 = st.columns(3)

    with col1:
        city = st.text_input("Preferred city / location", placeholder="e.g. Bangalore, Remote")
    with col2:
        experience = st.text_input("Experience level", placeholder="e.g. Fresher, 1–2 years")
    with col3:
        domain = st.text_input("Preferred domain", placeholder="e.g. AI/ML, Web Development")

    if st.button("🔍 Find Jobs", type="primary"):
        if not resume_text.strip():
            st.error("Please upload or paste your resume first.")
            return

        with st.spinner("Finding best job matches..."):
            result = match_jobs_with_gpt(
                resume_text=resume_text,
                city=city,
                experience=experience,
                domain=domain,
            )

        st.success("Job matches generated!")

        # Optional Mongo logging
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
            st.warning(f"MongoDB logging failed: {e}")

        st.session_state["last_search"] = {
            "resume_text": resume_text,
            "city": city,
            "experience": experience,
            "domain": domain,
            "result": result,
        }

    # --- Render results from session ---
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
        st.info("No matches found. Try updating your resume.")
        return

    st.caption(f"Found {len(matches)} matches")

    # --- Job cards ---
    for idx, job in enumerate(matches):
        with st.container(border=True):
            st.markdown(f"### {job.get('job_title')} — {job.get('match_score')}%")

            if job.get("matched_skills"):
                st.write("**Matched skills:**", ", ".join(job["matched_skills"]))

            # Missing skills → YouTube
            missing_skills = job.get("missing_skills", [])
            if missing_skills:
                st.write("**Missing skills (click to learn):**")
                cols = st.columns(min(4, len(missing_skills)))
                for i, skill in enumerate(missing_skills):
                    with cols[i % len(cols)]:
                        query = quote_plus(f"{skill} tutorial for beginners")
                        yt_url = f"https://www.youtube.com/results?search_query={query}"
                        st.link_button(skill, yt_url)

            # ✅ Live job links (multi-platform)
            links = job.get("job_links", {})
            if links:
                st.write("**View live jobs:**")
                cols = st.columns(len(links))
                for i, (platform, url) in enumerate(links.items()):
                    cols[i].link_button(platform.capitalize(), url)

            # Save job
            if user_email:
                if st.button("💾 Save Job", key=f"save_{idx}"):
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
                        st.error(f"Save failed: {e}")
            else:
                st.caption("Login to save jobs.")

    st.markdown("---")
    st.caption("Tip: Click missing skills to learn them instantly on YouTube.")


if __name__ == "__main__":
    main()
