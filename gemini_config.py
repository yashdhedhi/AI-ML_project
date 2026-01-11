# gemini_config.py
import os
import streamlit as st
from functools import lru_cache
from dotenv import load_dotenv
from google import genai

load_dotenv()


def _get_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    except Exception:
        return os.getenv("GEMINI_API_KEY")


@lru_cache(maxsize=1)
def get_gemini_client():
    key = _get_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=key)
