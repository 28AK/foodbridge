"""Contact page with a message form (messages are visible to admins)."""
import streamlit as st

from app.schemas import EMAIL_RE
from app.services import public_ops
from app.ui import layout, style
from app.ui.layout import CONTACT_EMAIL
from app.ui.runtime import run

SUBJECTS = ["General question", "I want to donate food", "Register my NGO", "Report a problem", "Partnership"]


def page() -> None:
    layout.page_head("Contact", "Get in **touch**",
                     "Questions, partnerships or problems with a donation — we'd love to hear from you.",
                     art="delivery")
    info, form_col = st.columns([1, 1.6], gap="large")
    with info:
        style.html(f"""<div class="fb-info"><h4>✉️ Email</h4>
          <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
          <h4>📍 Based in</h4><p>Lucknow, Uttar Pradesh, India</p>
          <h4>⏱️ Response time</h4><p>We usually reply within 1–2 working days.</p></div>""")
        st.write("")
        layout.link("how", "Read the FAQ", icon=":material/help:")

    with form_col, st.container(border=True):
        st.subheader("Send us a message", anchor=False)
        user = st.session_state.get("user") or {}
        with st.form("contact"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Your name", value=user.get("name", ""), max_chars=100)
            email = c2.text_input("Email", value=user.get("email", ""), max_chars=120)
            subject = st.selectbox("Subject", SUBJECTS)
            message = st.text_area("Message", height=150, max_chars=2000)
            sent = st.form_submit_button("Send message", type="primary", width="stretch")
        if sent:
            problems = []
            if len(name.strip()) < 2:
                problems.append("enter your name")
            if not EMAIL_RE.match(email.strip()):
                problems.append("enter a valid email")
            if len(message.strip()) < 10:
                problems.append("write a message (at least 10 characters)")
            if problems:
                st.error("Please " + ", ".join(problems) + ".")
            else:
                run(public_ops.save_contact_message(name, email, subject, message))
                st.success("Thanks! Your message has been sent — we'll get back to you by email.")
                st.toast("Message sent", icon="✅")
