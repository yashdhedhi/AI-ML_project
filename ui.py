# ui.py
import streamlit as st


def _inject_theme_css():
    """Inject global CSS for dark UI theme."""

    primary = "#818cf8"
    accent = "#f472b6"
    bg_main = "#020617"
    bg_alt = "#020617"

    # Global text color
    text_main = "#89a2d4"
    text_muted = "#89a2d4"

    css = f"""
    <style>

    /* Remove Streamlit default top bar */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}

    /* App background */
    .stApp {{
        background:
            radial-gradient(circle at 0% 0%, rgba(129,140,248,0.24), transparent 55%),
            radial-gradient(circle at 100% 0%, rgba(236,72,153,0.18), transparent 60%),
            linear-gradient(180deg, {bg_main}, {bg_alt});
        color: {text_main};
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .block-container {{
        max-width: 1100px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg, #020617, #020617);
        border-right: 1px solid rgba(148,163,184,0.25);
    }}

    section[data-testid="stSidebar"] * {{
        color: #ffffff !important;
    }}

    /* Topbar */
    .topbar {{
        padding: 0.7rem 1rem;
        border-radius: 999px;
        backdrop-filter: blur(14px);
        background: linear-gradient(120deg, rgba(15,23,42,0.9), rgba(15,23,42,0.8));
        border: 1px solid rgba(148,163,184,0.45);
        box-shadow: 0 18px 45px rgba(15,23,42,0.55);
        margin-bottom: 1.4rem;
    }}

    .topbar-title {{
        font-weight: 600;
        font-size: 1rem;
        color: {text_main};
    }}

    .topbar-subtitle {{
        font-size: 0.8rem;
        color: {text_main};
    }}

    /* Main buttons */
    div[data-testid="stButton"] > button {{
        background-image: linear-gradient(120deg, {primary}, {accent});
        color: #000000 !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 0.45rem 1.2rem !important;
        font-weight: 600 !important;
        transition: 0.15s ease;
    }}

    div[data-testid="stButton"] > button:hover {{
        transform: scale(1.04);
    }}

    /* Skill / link buttons */
    div[data-testid="stLinkButton"] > button {{
        background: {text_main} !important;
        color: #ffffff !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 0.4rem 1.1rem !important;
        font-size: 0.82rem !important;
        transition: transform 0.15s ease;
    }}

    div[data-testid="stLinkButton"] > button:hover {{
        transform: scale(1.08);
    }}

    /* Global text */
    h1, h2, h3, h4, h5, h6,
    p, label, span, li, a, strong {{
        color: {text_main} !important;
    }}

    .stCaption {{
        color: {text_muted} !important;
    }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_topbar(active: str = "Home"):
    _inject_theme_css()

    # Top bar
    st.markdown(
        """
        <div class="topbar">
            <div class="topbar-title">💼 AI Career Assistant</div>
            <div class="topbar-subtitle">
                Jobs • Skills • Learning Paths • Interviews
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top navigation (FIXED PATHS)
    nav_cols = st.columns([1.3, 1.3, 1.4, 1.7, 1.7])
    with nav_cols[0]:
        st.page_link("pages/Home.py", label="🏠 Home")
    with nav_cols[1]:
        st.page_link("pages/Login.py", label="🔐 Login")
    with nav_cols[2]:
        st.page_link("pages/Saved_Jobs.py", label="💾 Saved Jobs")
    with nav_cols[3]:
        st.page_link("pages/Learning_Path.py", label="📚 Learning Path")
    with nav_cols[4]:
        st.page_link("pages/Interview_Prep.py", label="🎤 Interview Prep")

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🚀 AI Career Assistant")

        st.markdown("### Main")
        st.page_link("pages/Home.py", label="🏠 Home")
        st.page_link("pages/Login.py", label="🔐 Login / Sign up")
        st.page_link("pages/Saved_Jobs.py", label="💾 Saved Jobs")

        st.markdown("### Growth")
        st.page_link("pages/Learning_Path.py", label="📚 Learning Path")
        st.page_link("pages/My_Learning_Paths.py", label="🧾 My Learning Paths")

        st.markdown("### Interviews")
        st.page_link("pages/Interview_Prep.py", label="🎤 Interview Prep")

        st.markdown("---")
        user = st.session_state.get("user")
        if user:
            st.caption(f"👤 Logged in as **{user.get('email','')}**")
        else:
            st.caption("👤 Not logged in")
