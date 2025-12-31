# resume_tools.py
from __future__ import annotations
import io

import streamlit as st

def extract_text_from_uploaded_file(uploaded_file) -> str:
    """
    Very simple text extractor for Streamlit uploaded file.
    - For .txt: decode bytes
    - For .pdf/.docx: you can improve later with PyPDF2 / docx2txt
    """
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    # txt
    if filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    # naive pdf/docx handling (you should replace with proper libs later)
    try:
        raw = uploaded_file.read()
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            # as fallback, return repr
            return raw.decode("latin-1", errors="ignore")
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        return ""
