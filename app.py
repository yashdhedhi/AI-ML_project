
# app.py
import streamlit as st

st.set_page_config(
    page_title="GPT Job Matcher",
    page_icon="💼",
    layout="centered",
)

st.title("GPT Job Matcher")
st.write(
    "Use the navigation in the sidebar (Pages section) to go to **Home**, **Login**, "
    "**Saved Jobs**, or **About**."
)

import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from resume_parser import extract_text_file, extract_contact_info
from skill_matcher import load_skills, extract_skills_from_text
from jobs_api import get_jobs  # now supports Adzuna/Workable/Arbeitnow
from matcher import semantic_similarity_pct, final_combine, compute_scores

load_dotenv()

st.set_page_config(page_title="Resume Analyzer & Job Recommender", layout="wide")

@st.cache_resource
def load_skills_cached(path: str = "skills.json"):
    return load_skills(path)

st.title("Intelligent Resume Analyzer + Live Job Recommender")

# Sidebar: API and settings
st.sidebar.header("Settings & API")
source = st.sidebar.selectbox("Source", ["Workable", "Adzuna", "Arbeitnow"], index=1)
st.sidebar.markdown("For Adzuna, set ADZUNA_APP_ID/ADZUNA_APP_KEY in .env or Streamlit secrets.")
location = st.sidebar.text_input("Job location (e.g., India, Mumbai)", value="Bengaluru")
num_jobs = st.sidebar.slider("Jobs to fetch (per page)", 5, 50, 15)
page = st.sidebar.number_input("Page", min_value=1, value=1, step=1)

# Workable-specific: comma-separated company slugs
companies_text = st.sidebar.text_input(
    "Workable company slugs (comma-separated)",
    value="openai,databricks,elastic"
)
workable_companies = [c.strip() for c in companies_text.split(",") if c.strip()]

skills_list = load_skills_cached()

# Resume upload
uploaded = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx", "doc"])
if uploaded:
    with st.spinner("Parsing resume..."):
        resume_text = extract_text_file(uploaded)
        contact = extract_contact_info(resume_text)
        resume_skills = extract_skills_from_text(resume_text, skills_list)

    st.subheader("Extracted Contact")
    st.json(contact)
    st.subheader("Detected Skills")
    st.write(", ".join(resume_skills) if resume_skills else "No skills found")
    st.subheader("Resume Preview (first 1,500 chars)")
    st.code(resume_text[:1500])

    # Query box
    st.markdown("---")
    st.subheader("Find Live Jobs")
    default_query = "Software Engineer"
    query = st.text_input("Job query/role/title", value=default_query)

    if st.button("Fetch & Match"):
        with st.spinner("Fetching jobs and computing matches..."):
            try:
                results = get_jobs(
                    source=source,
                    query=query,
                    location=location,
                    results_per_page=num_jobs,
                    workable_companies=workable_companies,
                    page=page,
                )
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        jobs = results or []
        rows = []
        for job in jobs:
            score_dict = compute_scores(
                resume_text=resume_text,
                resume_skills=resume_skills,
                job=job
            )
            rows.append({
                "title": job.get("title", ""),
                "company": (job.get("company") or {}).get("display_name", ""),
                "location": (job.get("location") or {}).get("display_name", ""),
                "redirect_url": job.get("redirect_url", ""),
                "skill_match_%": round(score_dict["skill_pct"], 1),
                "semantic_%": round(score_dict["semantic_pct"], 1),
                "final_%": round(score_dict["final_score"], 1),
                "matched_skills": ", ".join(score_dict["matched_skills"]),
                "missing_skills": ", ".join(score_dict["missing_skills"]),
            })

        if not rows:
            st.warning("No jobs returned from selected source. Try a broader query, another page, or another source.")
        else:
            df = pd.DataFrame(rows).sort_values("final_%", ascending=False).head(10)
            st.subheader("Top Recommendations")
            st.dataframe(df, use_container_width=True)
            st.markdown("Open selected job:")
            for _, r in df.iterrows():
                st.markdown(
                    f"- {r['title']} — {r['company']} — {r['location']} | "
                    f"Score: {r['final_%']}% | [Job Link]({r['redirect_url']})"
                    )

