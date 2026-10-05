"""Landing page with login and registration."""
import streamlit as st
from bson import ObjectId
from pydantic import ValidationError

from app.schemas import RegisterIn
from app.services import accounts
from app.ui import style
from app.ui.components import location_picker
from app.ui.runtime import run, try_run

DONOR_TYPES = {"household": "Household", "restaurant": "Restaurant", "hotel": "Hotel",
               "caterer": "Catering service", "event": "Event / venue"}
ORG_TYPES = {"ngo": "NGO", "shelter": "Shelter", "community_kitchen": "Community kitchen"}


def current_user() -> dict | None:
    """Logged-in user, re-read each run so changes (e.g. NGO verification) show up."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    user = run(accounts.get_user(ObjectId(user_id)))
    if user is None:
        st.session_state.pop("user_id", None)
    return user


def log_in(user: dict) -> None:
    st.session_state["user_id"] = str(user["_id"])
    st.rerun()


def log_out() -> None:
    st.session_state.clear()
    st.rerun()


def validation_message(exc: ValidationError) -> str:
    return "; ".join(e["msg"].removeprefix("Value error, ") for e in exc.errors())


def home_page() -> None:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        style.html("""
        <div class="fb-hero">
          <h1>🍲 Surplus food shouldn't go to waste.</h1>
          <p>FoodBridge connects restaurants, hotels, households and events with nearby NGOs,
          shelters and community kitchens — using AI to check food freshness and match it
          to the right place before it spoils.</p>
          <div class="fb-features">
            <div class="fb-feature"><b>📸 List surplus food</b><span>Photos auto-enhanced with OpenCV</span></div>
            <div class="fb-feature"><b>🧠 AI freshness check</b><span>Dish, spoilage risk & pickup deadline</span></div>
            <div class="fb-feature"><b>📍 Smart matching</b><span>Nearest NGO with capacity & demand</span></div>
          </div>
        </div>""")
        with st.expander("Demo accounts"):
            st.markdown(
                "- **Donor:** `donor@foodbridge.local` / `demo1234`\n"
                "- **NGO:** `annapurna@foodbridge.local` / `demo1234` (others in `data/seed/ngos.json`)\n"
                "- **Admin:** `admin@foodbridge.local` / your `ADMIN_PASSWORD`")

    with right, st.container(border=True):
        login_tab, register_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            login_form()
        with register_tab:
            register_form()


def login_form() -> None:
    with st.form("login"):
        email = st.text_input("Email", autocomplete="email")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        if st.form_submit_button("Log in", type="primary", width="stretch"):
            user = try_run(accounts.authenticate(email, password))
            if user:
                log_in(user)


def register_form() -> None:
    role = st.segmented_control(
        "I want to", ["donor", "ngo"], default="donor", key="reg_role",
        format_func=lambda r: "🍱 Donate food" if r == "donor" else "🏠 Receive food (NGO)",
    ) or "donor"

    name = st.text_input("Organisation name" if role == "ngo" else "Your / business name", key="reg_name")
    email = st.text_input("Email", key="reg_email")
    phone = st.text_input("Phone (for SMS alerts)", placeholder="+91XXXXXXXXXX", key="reg_phone")
    password = st.text_input("Password (min 6 characters)", type="password", key="reg_password")

    fields = {}
    if role == "donor":
        fields["donor_type"] = st.selectbox("Donor type", list(DONOR_TYPES),
                                            format_func=DONOR_TYPES.get, key="reg_donor_type")
    else:
        c1, c2 = st.columns(2)
        fields["org_type"] = c1.selectbox("Organisation type", list(ORG_TYPES),
                                          format_func=ORG_TYPES.get, key="reg_org_type")
        fields["capacity_meals"] = c2.number_input("Daily capacity (meals)", 1, 10_000, 100, key="reg_capacity")
        fields["veg_only"] = st.checkbox("We accept vegetarian food only", key="reg_veg_only")
        fields["address"] = st.text_input("Address", key="reg_address")
        st.caption("📍 Click on the map to mark your location")
        pos = location_picker("reg_map", height=260)
        if pos:
            fields["lat"], fields["lng"] = pos

    if st.button("Create account", type="primary", width="stretch"):
        if role == "ngo" and "lat" not in fields:
            st.error("Please mark your organisation's location on the map.")
            return
        try:
            data = RegisterIn(name=name, email=email, phone=phone, password=password, role=role, **fields)
        except ValidationError as exc:
            st.error(validation_message(exc))
            return
        user = try_run(accounts.register(data))
        if user:
            log_in(user)
