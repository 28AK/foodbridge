"""Public directory of verified organisations."""
import folium
import streamlit as st

from app.services import public_ops
from app.ui import cards, layout, style
from app.ui.components import LUCKNOW, pin, show_map
from app.ui.runtime import run

TYPE_FILTERS = {"All": None, "NGOs": "ngo", "Shelters": "shelter", "Community kitchens": "community_kitchen"}


def page() -> None:
    layout.page_head("Our network", "NGOs, shelters & **community kitchens**",
                     "Every organisation below has been verified by the FoodBridge team. They receive "
                     "matched donations based on their location, daily capacity and demand.",
                     art="kitchen")
    ngos = run(public_ops.public_ngos())

    search, kind, veg = st.columns([2, 2, 1], vertical_alignment="center")
    query = search.text_input("Search", placeholder="Search by name or area…", label_visibility="collapsed")
    kind_choice = kind.segmented_control("Type", list(TYPE_FILTERS), default="All", label_visibility="collapsed")
    veg_only = veg.toggle("Veg only")

    if query:
        q = query.lower()
        ngos = [n for n in ngos if q in n["name"].lower() or q in (n.get("area") or "").lower()
                or q in n.get("address", "").lower()]
    if TYPE_FILTERS.get(kind_choice):
        ngos = [n for n in ngos if n["type"] == TYPE_FILTERS[kind_choice]]
    if veg_only:
        ngos = [n for n in ngos if n.get("veg_only")]

    count, view = st.columns([3, 1], vertical_alignment="center")
    count.caption(f"{len(ngos)} organisation{'s' if len(ngos) != 1 else ''} · "
                  f"combined capacity {sum(n['capacity_meals'] for n in ngos):,} meals/day")
    mode = view.segmented_control("View", ["List", "Map"], default="List", label_visibility="collapsed",
                                  key="ngo_view")
    if not ngos:
        layout.empty("🔍", "No organisations match", "Try a different search or filter.")
    elif mode == "Map":
        m = folium.Map(location=LUCKNOW, zoom_start=12, control_scale=True)
        for n in ngos:
            lng, lat = n["location"]["coordinates"]
            icon = cards.ORG_TYPES.get(n["type"], ("", "🤝"))[1]
            folium.Marker((lat, lng), icon=pin(icon, "#ffffff"),
                          tooltip=f"{n['name']} · up to {n['capacity_meals']} meals/day").add_to(m)
        show_map(m, key="ngo_directory_map", height=560)
    else:
        style.html(cards.grid([cards.ngo_card(n) for n in ngos]))

    layout.section("Join the network", "Run an NGO, shelter or **community kitchen?**",
                   "Register for free. After a quick verification you'll start receiving nearby surplus food "
                   "matched to your daily demand.")
    if not st.session_state.get("user_id"):
        layout.link("signin", "Register your organisation", icon=":material/arrow_forward:")
