# pages/4_About.py

import streamlit as st
from ui import render_topbar


def main():
    st.set_page_config(page_title="GPT Job Matcher - About", page_icon="ℹ️", layout="centered")

    render_topbar(active="About")
    st.title("ℹ️ About This Project")

    st.markdown(
        """
This project is a **Resume-Based Job Recommendation System** built with:

- **Streamlit** for the web UI
- **MongoDB Atlas** for storing users, job matches, and saved jobs
- **Gemini API** (Google Generative AI) for:
  - Understanding your resume
  - Matching it against job roles
  - Returning structured job recommendations

### What it does

1. **Upload or paste your resume**
2. Optional: specify preferred **city**, **experience level**, and **domain**
3. The system sends this information to Gemini
4. Gemini returns a list of possible job matches (title, company, skills match, etc.)
5. You can **log in / sign up**, and **save** any job for later
6. View all saved jobs anytime from the **Saved Jobs** page

### Tech Stack

- Frontend: `Streamlit`
- Backend Database: `MongoDB Atlas`
- AI Model: `Gemini (google-generativeai)`
- Auth: simple email/password stored in MongoDB

You can extend this further by:
- Connecting to real job APIs (LinkedIn, Indeed, etc.)
- Improving resume parsing (PDF/DOCX parsing, skill extraction)
- Adding more advanced filters and dashboards
        """
    )

    st.markdown("---")
    st.caption("Built as a learning project combining AI/ML, backend, and frontend skills.")


if __name__ == "__main__":
    main()
