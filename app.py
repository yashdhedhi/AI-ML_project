# app.py
import streamlit as st

st.set_page_config(
    page_title="AI Career Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Redirect immediately to Home page
st.switch_page("pages/Home.py")
