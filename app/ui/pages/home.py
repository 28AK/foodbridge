"""Landing page."""
import streamlit as st

from app.services import public_ops
from app.ui import cards, flows, layout, style
from app.ui.runtime import run


def page() -> None:
    stats = run(public_ops.impact())
    journey = run(public_ops.journey_stats())
    food = run(public_ops.available_food())
    ngos = run(public_ops.public_ngos())

    style.html(f"""
    <div class="fb-hero">
      <div>
        <span class="eyebrow">AI-powered surplus food redistribution · Lucknow</span>
        <h1>Good food belongs on a plate, <span class="accent">not in a bin.</span></h1>
        <p>FoodBridge connects restaurants, hotels, households and events with nearby NGOs, shelters and
        community kitchens. Our AI checks every donation's freshness and routes it to the right place
        before it spoils.</p>
      </div>
      <div class="art"><img src="{layout.illustration('delivery')}" alt="Food being delivered to an NGO"></div>
    </div>""")
    with st.container(horizontal=True, gap="small", key="fb-ctas-home"):
        if st.session_state.get("user_id"):
            layout.link("dashboard", "Go to my dashboard", icon=":material/dashboard:")
        else:
            layout.link("signin", "Donate surplus food", icon=":material/volunteer_activism:")
            layout.link("signin", "Register your NGO", icon=":material/diversity_3:")
        layout.link("food", "See available food", icon=":material/restaurant:")

    layout.band("Our impact", "Every meal **counts**", "Live numbers from the platform.", layout.counters_html([
        (f"{stats['meals_delivered']:,}", "meals delivered"),
        (f"{stats['kg_saved']:,} kg", "food waste avoided (est.)"),
        (str(stats["ngos"]), "verified NGOs & shelters"),
        (str(stats["active_now"]), "donations active right now"),
    ]))

    layout.section("How it works", "The journey of a **donation**",
                   "Click any step to see what happens there — or press play. Numbers are live.")
    flows.journey(journey)

    layout.arc()
    layout.section("Available now", "Food waiting to be **picked up**",
                   "Exact addresses are shared only with the NGO that accepts the pickup.")
    if food:
        style.html(cards.grid([cards.food_card(item) for item in food[:3]]))
        st.write("")
        layout.link("food", f"View all {len(food)} available donations →")
    else:
        layout.empty("🍽️", "No food waiting right now", "New donations appear here as soon as they're listed.")

    layout.section("Our network", "NGOs, shelters & **community kitchens**",
                   "Every organisation is verified by our team before it can receive food.")
    if ngos:
        style.html(cards.grid([cards.ngo_card(n) for n in ngos[:6]]))
        st.write("")
        layout.link("ngos", f"See all {len(ngos)} organisations →")

    st.write("")
    style.html("""
    <div class="fb-cta"><h3>Run a restaurant, hotel, caterer or event?</h3>
      <p>List your surplus in under a minute. We'll find the nearest NGO that can use it today.</p></div>""")
    if not st.session_state.get("user_id"):
        st.write("")
        with st.container(horizontal=True, key="fb-ctas-bottom"):
            layout.link("signin", "Create a free account", icon=":material/arrow_forward:")
