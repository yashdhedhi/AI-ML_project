import time
import streamlit as st


def gemini_rate_limit(seconds: int = 25) -> bool:
    """
    Prevents Gemini API from being called too frequently.

    Returns:
        True  -> allowed
        False -> blocked (show warning)
    """

    last_call = st.session_state.get("_last_gemini_call", 0)
    now = time.time()

    remaining = seconds - (now - last_call)

    if remaining > 0:
        st.warning(f"⏳ Please wait {int(remaining)}s before next AI request.")
        return False

    st.session_state["_last_gemini_call"] = now
    return True
