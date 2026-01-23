import streamlit as st
from urllib.parse import quote_plus
from datetime import datetime
import os, time

from ui import render_topbar
from db import get_collection
from dotenv import load_dotenv

# ================= SAFE GEMINI IMPORT =================
Client = None
genai = None

try:
    from google.genai import Client
except Exception:
    try:
        import google.generativeai as genai
    except Exception:
        pass


# ================= RATE LIMIT =================
def gemini_rate_limit(seconds: int = 25):
    last = st.session_state.get("_last_gemini_call", 0)
    now = time.time()

    if now - last < seconds:
        wait = int(seconds - (now - last))
        st.warning(f"⏳ Please wait {wait}s before next request")
        return False

    st.session_state["_last_gemini_call"] = now
    return True


# ================= ENV =================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.0-flash")

client = None
GEMINI_ERROR = None

if GEMINI_API_KEY:
    try:
        if Client:
            client = Client(api_key=GEMINI_API_KEY)
        elif genai:
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai
    except Exception as e:
        GEMINI_ERROR = str(e)
else:
    GEMINI_ERROR = "GEMINI_API_KEY not set"


# ================= CACHE =================
@st.cache_data(ttl=600)
def cached_generate(prompt: str):
    if Client:
        r = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return r.text
    else:
        model = client.GenerativeModel(GEMINI_MODEL)
        return model.generate_content(prompt).text


# ================= GEMINI =================
def generate_learning_path(skills, role, experience, resume):

    if GEMINI_ERROR or not client:
        return f"❌ {GEMINI_ERROR}"

    resume = (resume or "")[:1500]

    prompt = f"""
Create a phase-wise learning roadmap.

Role: {role}
Experience: {experience}
Skills: {', '.join(skills)}

Markdown only.
"""

    try:
        return cached_generate(prompt)
    except Exception as e:
        return f"❌ API Error: {e}"


# ================= PAGE =================
def main():
    st.set_page_config(page_title="Learning Path", page_icon="📚", layout="wide")

    render_topbar(active="Learning Path")
    st.title("📚 Personalized Learning Path")

    last_search = st.session_state.get("last_search") or {}
    matches = (last_search.get("result") or {}).get("matches") or []

    if not matches:
        st.warning("Run job search first")
        return

    resume = last_search.get("resume_text", "")
    experience = last_search.get("experience", "")
    role = last_search.get("domain", "")

    missing = sorted({
        s for j in matches for s in (j.get("missing_skills") or [])
    })

    selected = st.multiselect("Skills", missing, default=missing)

    if st.button("✨ Generate Learning Path"):

        if not gemini_rate_limit():
            return

        with st.spinner("Generating..."):
            roadmap = generate_learning_path(selected, role, experience, resume)

        st.markdown(roadmap)


if __name__ == "__main__":
    main()
