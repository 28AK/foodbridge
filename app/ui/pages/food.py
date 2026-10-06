"""Public list of food currently available for pickup."""
import folium
import streamlit as st

from app.services import public_ops
from app.ui import cards, layout, style
from app.ui.components import LUCKNOW, pin, show_map
from app.ui.runtime import run


def page() -> None:
    layout.page_head("Available food", "Food waiting for **pickup**",
                     "Live donations from restaurants, hotels, caterers and households. Verified NGOs are "
                     "matched automatically — log in as an NGO to receive and accept pickups.",
                     art="tiffin")
    listing_view()


@st.fragment(run_every=60)
def listing_view() -> None:
    items = run(public_ops.available_food())

    search, diet, sort = st.columns([2, 1.2, 1.2])
    query = search.text_input("Search", placeholder="Search dish or area…", label_visibility="collapsed")
    diet_choice = diet.segmented_control("Diet", ["All", "Veg", "Non-veg"], default="All",
                                         label_visibility="collapsed")
    sort_choice = sort.selectbox("Sort", ["Pickup deadline", "Most servings", "Newest"],
                                 label_visibility="collapsed")
    categories = sorted({i["ai"]["category"]["name"] for i in items if i.get("ai")})
    chosen = st.pills("Category", categories, selection_mode="multi", label_visibility="collapsed")

    if query:
        q = query.lower()
        items = [i for i in items if q in i["food_name"].lower() or q in i["area"].lower()
                 or q in ((i.get("ai") or {}).get("dish") or {}).get("name", "").lower()]
    if diet_choice == "Veg":
        items = [i for i in items if i["food_category"] == "veg"]
    elif diet_choice == "Non-veg":
        items = [i for i in items if i["food_category"] == "non_veg"]
    if chosen:
        items = [i for i in items if i.get("ai") and i["ai"]["category"]["name"] in chosen]
    if sort_choice == "Most servings":
        items.sort(key=lambda i: i["quantity_servings"], reverse=True)
    elif sort_choice == "Newest":
        items.sort(key=lambda i: i["created_at"], reverse=True)

    count, view = st.columns([3, 1], vertical_alignment="center")
    count.caption(f"{len(items)} donation{'s' if len(items) != 1 else ''} · "
                  f"{sum(i['quantity_servings'] for i in items)} servings · updates every minute")
    mode = view.segmented_control("View", ["Grid", "Map"], default="Grid", label_visibility="collapsed",
                                  key="food_view")

    if not items:
        layout.empty("🍽️", "No food matches your filters", "Try clearing the filters, or check back soon.")
        return
    if mode == "Map":
        m = folium.Map(location=LUCKNOW, zoom_start=12, control_scale=True)
        for i in items:
            folium.Marker(i["approx_point"], icon=pin(str(i["quantity_servings"]), "#2e7d32"),
                          tooltip=f"{i['food_name']} · {i['quantity_servings']} servings · near {i['area']}").add_to(m)
        show_map(m, key="food_map", height=520)
        st.caption("Markers show the approximate area (about 1 km) — exact pickup points are private.")
    else:
        style.html(cards.grid([cards.food_card(i) for i in items]))
