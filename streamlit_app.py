"""FoodBridge – Streamlit app.

Run:  streamlit run streamlit_app.py
"""
import streamlit as st

st.set_page_config(page_title="FoodBridge", page_icon="🍲", layout="wide")

from app.ui import style  # noqa: E402  (set_page_config must run first)
from app.ui.pages import admin, auth, donor, ngo  # noqa: E402
from app.ui.runtime import start  # noqa: E402

style.inject_css()
start()

user = auth.current_user()
if user is None:
    pages = [st.Page(auth.home_page, title="Welcome", icon="🍲", default=True)]
    st.navigation(pages, position="hidden").run()
else:
    st.session_state["user"] = user
    role_pages = {
        "donor": st.Page(donor.page, title="Donor dashboard", icon="🍱", default=True),
        "ngo": st.Page(ngo.page, title="NGO dashboard", icon="🏠", default=True),
        "admin": st.Page(admin.page, title="Admin dashboard", icon="🛠️", default=True),
    }
    with st.sidebar:
        style.html(f'<div style="font-size:1.3rem;font-weight:700;color:#1b5e20">🍲 FoodBridge</div>'
                   f'<div class="fb-muted">Signed in as <b>{style.escape(user["name"])}</b> · {user["role"]}</div>')
        if st.button("Log out", width="stretch"):
            auth.log_out()
    st.navigation([role_pages[user["role"]]], position="hidden").run()
