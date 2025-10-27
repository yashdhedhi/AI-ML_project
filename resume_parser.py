import io
import re
import docx
import spacy 

# Load spaCy English model once


_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{7,}\d)")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    PDFPLUMBER_AVAILABLE = False

from PyPDF2 import PdfReader   # fallback

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:  # type: ignore
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except Exception:
            pass
    # fallback to PyPDF2
    reader = PdfReader(io.BytesIO(file_bytes))
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)

def extract_text_file(file_obj) -> str:
    # Streamlit UploadedFile provides .type and .read()
    data = file_obj.read()
    # Reset pointer for potential re-use by caller
    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except Exception:
            pass
    name = getattr(file_obj, "name", "").lower()
    if name.endswith(".pdf") or getattr(file_obj, "type", "") == "application/pdf":
        return extract_text_from_pdf(data)
    elif name.endswith(".docx") or name.endswith(".doc"):
        return extract_text_from_docx(data)
    # Fallback plain text
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def extract_contact_info(text: str):
    emails = EMAIL_RE.findall(text or "")
    phones = PHONE_RE.findall(text or "")
    # crude name guess from first non-empty lines
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    name = lines[0] if lines else ""
    return {
        "name_guess": name[:120],
        "emails": list(dict.fromkeys(emails)),
        "phones": list(dict.fromkeys(phones)),
    }

# Backwards-compatible aliases if ever needed
def extract_text(file_obj):
    return extract_text_file(file_obj)
