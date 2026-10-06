"""FoodBridge – Streamlit app.

Run:  streamlit run streamlit_app.py
"""
import streamlit as st

from app.config import BASE_DIR

st.set_page_config(page_title="FoodBridge – Surplus Food Redistribution",
                   page_icon=str(BASE_DIR / "assets" / "logo-mark.png"), layout="wide")

from app.ui import layout, style  # noqa: E402  (set_page_config must run first)
from app.ui.pages import about, admin, auth, contact, donor, food, home, how, impact, ngo, ngos  # noqa: E402
from app.ui.runtime import start  # noqa: E402

# Full wordmark everywhere (with top navigation, icon_image would replace it in the header)
st.logo(str(BASE_DIR / "assets" / "logo.png"), size="large")
start()

user = auth.current_user()
if user:
    st.session_state["user"] = user
else:
    st.session_state.pop("user", None)

public = {
    "home": st.Page(home.page, title="Home", icon=":material/home:", url_path="home", default=True),
    "food": st.Page(food.page, title="Available food", icon=":material/restaurant:", url_path="available-food"),
    "ngos": st.Page(ngos.page, title="NGOs", icon=":material/diversity_3:", url_path="ngos"),
    "impact": st.Page(impact.page, title="Impact", icon=":material/insights:", url_path="impact"),
    "how": st.Page(how.page, title="How it works", icon=":material/lightbulb:", url_path="how-it-works"),
    "about": st.Page(about.page, title="About", icon=":material/info:", url_path="about"),
    "contact": st.Page(contact.page, title="Contact", icon=":material/mail:", url_path="contact"),
}
DASHBOARDS = {"donor": donor.page, "ngo": ngo.page, "admin": admin.page}

if user:
    account = {
        "dashboard": st.Page(DASHBOARDS[user["role"]], title="My dashboard", icon=":material/dashboard:",
                             url_path="dashboard"),
        "logout": st.Page(auth.log_out, title="Log out", icon=":material/logout:", url_path="logout"),
    }
    account_label = f"{user['name'].split()[0]} ({user['role']})"
else:
    account = {"signin": st.Page(auth.signin_page, title="Log in / Sign up", icon=":material/login:",
                                 url_path="sign-in")}
    account_label = ""

layout.PAGES.clear()
layout.PAGES.update(public | account)

# Logged out: "Log in / Sign up" is a plain link (last item, shown as a button on the right).
# Logged in: the user's name becomes a dropdown (dashboard, log out) on the right.
nav = ({"": list(public.values()) + list(account.values())} if not user
       else {"": list(public.values()), account_label: list(account.values())})
current = st.navigation(nav, position="top")
if st.session_state.pop("go_to_dashboard", False) and "dashboard" in account:
    st.switch_page(account["dashboard"])
# Inject the stylesheet after st.navigation(): elements created before it don't survive page rendering
style.inject_css()
current.run()
layout.footer()
