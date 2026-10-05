"""Donor dashboard: AI photo check, new donation, my donations."""
import hashlib
from datetime import datetime
from html import escape

import streamlit as st
from fastapi import HTTPException

from app.services import listing_ops
from app.services.pipeline import check_photo
from app.ui import style
from app.ui.components import location_picker, thumb_uri
from app.ui.runtime import run, try_run


def page() -> None:
    user = st.session_state["user"]
    st.title("Donor Dashboard", anchor=False)
    stats_row(user)
    new_tab, mine_tab = st.tabs(["➕ New donation", "📋 My donations"])
    with new_tab:
        if st.session_state.get("last_listing_id"):
            show_result()
        new_donation(user)
    with mine_tab:
        my_donations(user)


def stats_row(user: dict) -> None:
    listings = run(listing_ops.mine(user, limit=500))
    delivered = [l for l in listings if l["status"] == "delivered"]
    active = [l for l in listings if l["status"] in ("listed", "matched", "picked_up")]
    cols = st.columns(4)
    cards = [
        ("Donations", str(len(listings)), "all time"),
        ("Meals delivered", str(sum(l["quantity_servings"] for l in delivered)), f"{len(delivered)} deliveries"),
        ("Active", str(len(active)), "waiting / on the way"),
        ("Not accepted", str(sum(l["status"] == "rejected" for l in listings)), "judged unsafe by AI"),
    ]
    for col, (label, value, sub) in zip(cols, cards):
        with col:
            style.html(style.stat(label, value, sub))


# ---------- new donation ----------
def form_key(name: str) -> str:
    """Widget keys change after each submit, which resets the form."""
    return f"{name}_{st.session_state.get('donation_form', 0)}"


def new_donation(user: dict) -> None:
    left, right = st.columns([1, 1], gap="large")

    with left, st.container(border=True):
        st.subheader("1. Photo of the food", anchor=False)
        upload = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png", "webp"],
                                  key=form_key("photo"))
        with st.expander("📷 Or take a photo with the camera"):
            camera = st.camera_input("Camera", key=form_key("camera"), label_visibility="collapsed")
        photo = upload or camera

        st.subheader("2. Details", anchor=False)
        c1, c2 = st.columns(2)
        category = c1.radio("Category", ["veg", "non_veg"], horizontal=True, key=form_key("category"),
                            format_func=lambda c: "🟢 Veg" if c == "veg" else "🔴 Non-veg")
        servings = c2.number_input("Servings (approx.)", 1, 5000, 10, key=form_key("servings"))
        c3, c4 = st.columns(2)
        now = datetime.now(style.IST)
        prep_date = c3.date_input("Prepared on", now.date(), max_value=now.date(), key=form_key("prep_date"))
        prep_time = c4.time_input("at", now.time().replace(second=0, microsecond=0), step=300,
                                  key=form_key("prep_time"))
        prepared_at = datetime.combine(prep_date, prep_time)  # naive = IST, as the services expect

        preview = ai_preview(photo, prepared_at, servings, category)
        if preview and preview.get("ai") and not st.session_state.get(form_key("food_name")):
            st.session_state[form_key("food_name")] = preview["ai"]["dish"]["name"]
        food_name = st.text_input("Food name", key=form_key("food_name"), placeholder="e.g. Veg biryani")
        description = st.text_area("Description (optional)", key=form_key("description"), height=68)

    with right:
        with st.container(border=True):
            st.subheader("🧠 AI check", anchor=False)
            if photo is None:
                st.caption("Upload a photo to see the AI freshness check here.")
            elif preview:
                st.image(photo, width="stretch")
                style.html(style.ai_summary(preview))

        with st.container(border=True):
            st.subheader("3. Pickup location", anchor=False)
            address = st.text_input("Pickup address", key=form_key("address"))
            st.caption("📍 Click on the map to mark the pickup point")
            pos = location_picker(form_key("map"), height=300)
            notes = st.text_input("Pickup notes (optional)", key=form_key("notes"),
                                  placeholder="e.g. Ask for the manager at the back gate")

            if st.button("Submit donation", type="primary", width="stretch"):
                problems = []
                if photo is None:
                    problems.append("add a photo")
                if len(food_name.strip()) < 2:
                    problems.append("enter the food name")
                if len(address.strip()) < 5:
                    problems.append("enter the pickup address")
                if pos is None:
                    problems.append("mark the pickup point on the map")
                if problems:
                    st.error("Please " + ", ".join(problems) + ".")
                    return
                with st.spinner("Analysing photo and finding the best NGO…"):
                    listing = try_run(listing_ops.create(
                        user, photo=photo.getvalue(),
                        food_name=food_name, food_category=category, quantity_servings=int(servings),
                        prepared_at=prepared_at, address=address, lat=pos[0], lng=pos[1],
                        description=description, pickup_notes=notes,
                    ))
                if listing:
                    st.session_state["last_listing_id"] = listing["_id"]
                    st.session_state["donation_form"] = st.session_state.get("donation_form", 0) + 1
                    st.rerun()


def ai_preview(photo, prepared_at: datetime, servings: int, category: str) -> dict | None:
    """Run the AI on the chosen photo once per (photo, inputs) and remember the result."""
    if photo is None:
        return None
    digest = hashlib.sha1(photo.getvalue()).hexdigest()
    cache_key = (digest, prepared_at.isoformat(), servings, category)
    cache = st.session_state.setdefault("ai_preview_cache", {})
    if cache_key not in cache:
        with st.spinner("🧠 Analysing photo…"):
            try:
                data = check_photo(photo.getvalue(), photo.type)
            except HTTPException as exc:
                st.error(exc.detail)
                return None
            cache.clear()
            cache[cache_key] = try_run(listing_ops.preview(data, prepared_at, servings, category))
    return cache[cache_key]


def show_result() -> None:
    user = st.session_state["user"]
    listing = try_run(listing_ops.get_for(user, st.session_state["last_listing_id"]))
    if not listing:
        return
    with st.container(border=True):
        top, close = st.columns([6, 1])
        if listing["status"] == "rejected":
            top.error("❌ Not accepted – this food is not safe to donate.")
        elif listing.get("match"):
            m = listing["match"]
            top.success(f"✅ Matched with **{m['ngo_name']}** ({m['distance_km']} km away). "
                        "They've been asked to accept the pickup.")
        else:
            top.info("✅ Listed – looking for a nearby NGO with capacity…")
        if close.button("Close", key="close_result"):
            st.session_state.pop("last_listing_id")
            st.rerun()
        style.html(style.ai_summary(listing))
        st.caption("Image preprocessing pipeline (OpenCV)")
        figures = "".join(
            f'<figure><img src="{thumb_uri(listing["images"][stage], 400) or ""}" alt="{label}">'
            f"<figcaption>{label}</figcaption></figure>"
            for stage, label in [("original", "Original"), ("processed", "Enhanced"),
                                 ("model_input", "AI input 224×224")])
        style.html(f'<div class="fb-pipeline">{figures}</div>')
        r = listing["preprocessing"]
        st.caption(f"Brightness {r['before']['brightness']} → {r['after']['brightness']} · "
                   f"Contrast {r['before']['contrast']} → {r['after']['contrast']} · "
                   f"Steps: {', '.join(r['steps']) or 'none needed'}")


# ---------- my donations ----------
@st.fragment(run_every=20)
def my_donations(user: dict) -> None:
    listings = run(listing_ops.mine(user))
    if not listings:
        st.info("No donations yet. Your listings will appear here.")
        return
    st.caption("Updates automatically every 20 seconds.")
    for listing in listings:
        with st.container(border=True):
            info, actions = st.columns([5, 1])
            with info:
                style.html(donation_card(listing))
            if listing["status"] in ("listed", "matched"):
                if actions.button("Cancel", key=f"cancel_{listing['_id']}"):
                    if try_run(listing_ops.cancel(user, listing["_id"])):
                        st.rerun()


def donation_card(listing: dict) -> str:
    veg = "🟢 Veg" if listing["food_category"] == "veg" else "🔴 Non-veg"
    ai = f" · AI: {escape(listing['ai']['dish']['name'])}" if listing.get("ai") else ""
    lines = [
        f'<span class="fb-muted">{listing["quantity_servings"]} servings · {veg}{ai} · '
        f'listed {style.fmt_dt(listing["created_at"])}</span>',
        f'{style.status_badge(listing["status"])} {style.risk_badge(listing.get("freshness"))}',
    ]
    match = listing.get("match")
    if match:
        accepted = " ✓ accepted" if match.get("accepted_at") else " · waiting for them to accept"
        lines.append(f'<span class="fb-muted">→ {escape(match["ngo_name"])} '
                     f'({match["distance_km"]} km){accepted}</span>')
    elif listing["status"] == "listed":
        lines.append('<span class="fb-muted">Looking for a nearby NGO…</span>')
    if listing["status"] in ("listed", "matched"):
        lines.append(f'<span class="fb-muted">Pick up by {style.fmt_dt(listing["pickup_deadline"])} '
                     f'({style.time_left(listing["pickup_deadline"])})</span>')
    if listing.get("rejection_reason"):
        lines.append(f'<span class="fb-muted">Reason: {escape(listing["rejection_reason"])}</span>')
    return style.item(thumb_uri(listing["images"]["processed"]), listing["food_name"], lines)
