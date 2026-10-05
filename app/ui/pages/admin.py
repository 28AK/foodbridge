"""Admin: platform overview, NGO map and verification."""
from html import escape

import folium
import streamlit as st

from app.db import LISTINGS, get_db
from app.services import ngo_ops
from app.ui import style
from app.ui.components import pin, show_map
from app.ui.runtime import run, try_run

ORG_TYPES = {"ngo": "NGO", "shelter": "Shelter", "community_kitchen": "Community kitchen"}


async def listing_counts() -> dict:
    cursor = await get_db()[LISTINGS].aggregate([
        {"$group": {"_id": "$status", "n": {"$sum": 1}, "servings": {"$sum": "$quantity_servings"}}},
    ])
    return {row["_id"]: row async for row in cursor}


def page() -> None:
    st.title("Admin Dashboard", anchor=False)
    ngos = run(ngo_ops.list_all())
    counts = run(listing_counts())

    delivered = counts.get("delivered", {})
    active = sum(counts.get(s, {}).get("n", 0) for s in ("listed", "matched", "picked_up"))
    cards = [
        ("Organisations", str(len(ngos)), f"{sum(n['verified'] for n in ngos)} verified"),
        ("Pending verification", str(sum(not n["verified"] for n in ngos)), "need review"),
        ("Active donations", str(active), "listed / matched / in transit"),
        ("Meals delivered", str(delivered.get("servings", 0)), f"{delivered.get('n', 0)} deliveries"),
    ]
    for col, (label, value, sub) in zip(st.columns(4), cards):
        with col:
            style.html(style.stat(label, value, sub))

    left, right = st.columns([1, 1.25], gap="large")
    with left, st.container(border=True):
        st.subheader("🗺️ Organisations", anchor=False)
        m = folium.Map(location=(26.8467, 80.9462), zoom_start=12, control_scale=True)
        for ngo in ngos:
            lng, lat = ngo["location"]["coordinates"]
            folium.Marker((lat, lng), tooltip=f"{ngo['name']} ({'verified' if ngo['verified'] else 'pending'})",
                          icon=pin("✓" if ngo["verified"] else "?",
                                   "#2e7d32" if ngo["verified"] else "#ef6c00")).add_to(m)
        show_map(m, key="admin_map", height=460)

    with right, st.container(border=True):
        st.subheader("Verification", anchor=False)
        st.caption("Only verified NGOs, shelters and community kitchens receive food matches.")
        for ngo in ngos:
            info, action = st.columns([4, 1])
            badge = ('<span class="fb-badge verified">Verified</span>' if ngo["verified"]
                     else '<span class="fb-badge pending">Pending</span>')
            with info:
                style.html(
                    f'<div><b>{escape(ngo["name"])}</b> {badge}<br>'
                    f'<span class="fb-muted">{ORG_TYPES.get(ngo["type"], escape(ngo["type"]))} · '
                    f'{ngo["capacity_meals"]} meals/day{" · veg only" if ngo["veg_only"] else ""} · '
                    f'{escape(ngo["address"])} · {escape(ngo["phone"])}</span></div>')
            label = "Revoke" if ngo["verified"] else "Verify"
            if action.button(label, key=f"verify_{ngo['_id']}",
                             type="secondary" if ngo["verified"] else "primary"):
                try_run(ngo_ops.set_verified(ngo["_id"], not ngo["verified"]))
                st.rerun()
