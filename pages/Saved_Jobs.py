# pages/3_Saved_Jobs.py

import streamlit as st
from datetime import datetime

from ui import render_topbar
from db import get_collection


def main():
    st.set_page_config(page_title="GPT Job Matcher - Saved Jobs", page_icon="💾", layout="wide")

    render_topbar(active="Saved Jobs")
    st.title("💾 Your Saved Jobs")

    user = st.session_state.get("user")
    if not user or not user.get("email"):
        st.warning("You need to log in to view saved jobs. Go to the Login page.")
        return

    user_email = user["email"]
    col = get_collection("saved_jobs")

    try:
        docs = list(col.find({"user_email": user_email}).sort("created_at", -1))
    except Exception as e:
        st.error(f"Failed to load saved jobs: {e}")
        return

    if not docs:
        st.info("You haven’t saved any jobs yet. Use the Home page to find and save jobs.")
        return

    st.write(f"Found **{len(docs)}** saved jobs for **{user_email}**")

    for idx, doc in enumerate(docs):
        job = doc.get("job", {})
        meta = doc.get("meta", {})
        created_at = doc.get("created_at")
        if isinstance(created_at, datetime):
            created_str = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            created_str = str(created_at)

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
            if job.get("missing_skills"):
                st.write("**Missing skills:**", ", ".join(job.get("missing_skills")))

            if job.get("job_link"):
                st.markdown(f"[🔗 View Job Posting]({job['job_link']})")

            if job.get("summary"):
                st.write("**Summary:**", job["summary"])
            if job.get("explain"):
                st.write("*Why this job?*", job["explain"])

            st.caption(
                f"Saved on {created_str} | "
                f"Filters → city: {meta.get('city','–')}, "
                f"experience: {meta.get('experience','–')}, "
                f"domain: {meta.get('domain','–')}"
            )

            col_btn = st.columns([1, 5])
            with col_btn[0]:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    try:
                        col.delete_one({"_id": doc["_id"]})
                        st.success("Deleted. Reload the page to refresh.")
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")


if __name__ == "__main__":
    main()
