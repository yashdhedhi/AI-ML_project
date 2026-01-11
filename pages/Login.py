# pages/2_Login.py

import streamlit as st

from ui import render_topbar
from db import Database


def main():
    st.set_page_config(page_title="GPT Job Matcher - Login", page_icon="🔐", layout="centered")

    render_topbar(active="Login")
    st.title("🔐 Login / Sign Up")

    db = Database()

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    # --- LOGIN TAB ---
    with tab_login:
        st.subheader("Existing user login")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.error("Please fill in both email and password.")
            else:
                user = db.authenticate_user(email=email, password=password)
                if user:
                    # ✅ store user in a consistent format
                    st.session_state["user"] = {
                        "id": str(user["_id"]),           # <--- use 'id', not '_id'
                        "email": user["email"],
                        "name": user.get("name", ""),
                    }
                    st.session_state["is_authenticated"] = True
                    st.success("Logged in successfully! Go to Home or Saved Jobs from sidebar.")
                else:
                    st.error("Invalid email or password.")

    # --- SIGNUP TAB ---
    with tab_signup:
        st.subheader("Create a new account")

        with st.form("signup_form"):
            name = st.text_input("Full name")
            email_s = st.text_input("Email")
            password_s = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm password", type="password")
            submitted_s = st.form_submit_button("Sign Up")

        if submitted_s:
            if not email_s or not password_s:
                st.error("Email and password are required.")
            elif password_s != password2:
                st.error("Passwords do not match.")
            else:
                try:
                    doc = db.create_user(email=email_s, password=password_s, name=name)
                    st.success("Account created successfully! You can now log in from the Login tab.")
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"Failed to create user: {e}")

    # Logout button if someone is logged in
    st.markdown("---")
    user = st.session_state.get("user")
    if user:
        st.caption(f"Currently logged in as **{user.get('email')}**")
        if st.button("Logout"):
            st.session_state.pop("user", None)
            st.session_state["is_authenticated"] = False
            st.success("You have been logged out.")


if __name__ == "__main__":
    main()
