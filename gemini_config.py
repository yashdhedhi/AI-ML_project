# gemini_config.py
import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Load .env for LOCAL only
load_dotenv()


def get_gemini_api_key():
    """
    Priority:
    1. Streamlit Cloud Secrets
    2. Local .env
    """
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]

    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key

    raise RuntimeError(
        "GEMINI_API_KEY not found. "
        "Add it to Streamlit Secrets or .env"
    )


def get_gemini_client():
    """Return initialized Gemini client"""
    return genai.Client(api_key=get_gemini_api_key())
