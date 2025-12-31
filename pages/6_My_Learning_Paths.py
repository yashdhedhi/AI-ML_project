# pages/6_My_Learning_Paths.py

import streamlit as st
from datetime import datetime
from urllib.parse import quote_plus

from ui import render_topbar
from db import get_collection


def main():
    st.set_page_config(page_title="My Learning Paths", page_icon="🧾", layout="wide")

    render_topbar(active="About")  # no exact tab for this, but it's fine
    st.title("🧾 My Learning Paths")

    user = st.session_state.get("user")
    if not user or not user.get("email"):
        st.warning("You need to log in to view your saved learning paths.")
        return

    user_email = user["email"]
    st.caption(f"Showing learning paths for **{user_email}**")

    col = get_collection("learning_paths")

    try:
        docs = list(col.find({"user_email": user_email}).sort("created_at", -1))
    except Exception as e:
        st.error(f"Failed to load learning paths: {e}")
        return

    if not docs:
        st.info("You haven't saved any learning paths yet. Generate one from the 'Learning Path' page.")
        return

    st.write(f"Found **{len(docs)}** saved learning paths.")

    for idx, doc in enumerate(docs):
        created_at = doc.get("created_at")
        if isinstance(created_at, datetime):
            created_str = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            created_str = str(created_at)

        target_role = doc.get("target_role", "Not specified")
        skills = doc.get("skills") or []
        experience = doc.get("experience", "")
        roadmap_md = doc.get("roadmap_md", "")

        # Header card
        with st.container(border=True):
            st.markdown(f"### #{idx + 1} — {target_role}")
            st.caption(f"Created at: {created_str} | Experience: {experience or 'N/A'}")

            if skills:
                st.write("**Skills covered:**", ", ".join(skills))

            # Quick YouTube links again
            if skills:
                st.write("▶️ **YouTube quick links:**")
                skill_cols = st.columns(min(4, len(skills)))
                for i, skill in enumerate(skills):
                    col_btn = skill_cols[i % len(skill_cols)]
                    with col_btn:
                        query = quote_plus(f"{skill} tutorial for beginners")
                        youtube_url = f"https://www.youtube.com/results?search_query={query}"
                        st.link_button(skill, youtube_url)

            # Show roadmap in expander
            with st.expander("📘 View learning path details", expanded=False):
                if roadmap_md:
                    st.markdown(roadmap_md)
                else:
                    st.write("_No roadmap text saved._")

            # Delete button
            cols_bottom = st.columns([1, 5])
            with cols_bottom[0]:
                if st.button("🗑️ Delete", key=f"del_lp_{idx}"):
                    try:
                        col.delete_one({"_id": doc["_id"]})
                        st.success("Deleted. Please refresh or reopen this page to see updates.")
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")


if __name__ == "__main__":
    main()
