"""How FoodBridge works: timeline, interactive flowcharts, food safety, FAQ."""
from html import escape

import streamlit as st

from app.services import public_ops
from app.services.food_catalog import CATEGORIES
from app.ui import flows, layout, style
from app.ui.runtime import run

DONOR_STEPS = [
    ("Create a free account", "Households, restaurants, hotels, caterers and event venues can all donate. "
     "Registration takes under a minute."),
    ("Photograph & list your surplus", "Upload a photo, the approximate servings and when it was cooked. "
     "OpenCV cleans up the photo and the AI checks the dish and freshness instantly."),
    ("We find the right NGO", "The nearest verified NGO with free capacity and demand is matched automatically. "
     "If they decline or don't answer within 15 minutes, the next-best NGO gets it."),
    ("Hand it over & track it", "The NGO calls you, picks up the food and marks it delivered. You see every "
     "status change on your dashboard."),
]
NGO_STEPS = [
    ("Register & get verified", "Add your location, daily meal capacity and whether you accept vegetarian food "
     "only. Our team verifies every organisation before it receives food."),
    ("Set today's demand", "Tell us how many meals you need today. Matching favours NGOs with unmet demand."),
    ("Accept matches", "Matched donations appear on your dashboard with photos, freshness and a pickup deadline. "
     "Accept or decline in one click."),
    ("Follow the route & deliver", "Get a suggested pickup order (most urgent first) and Google Maps directions, "
     "then mark food picked up and delivered."),
]


def timeline(steps: list[tuple[str, str]], first_open: bool = True) -> str:
    items = "".join(
        f'<details{" open" if first_open and i == 0 else ""}><summary>{i + 1}. {escape(title)}</summary>'
        f'<div class="content">{escape(text)}</div></details>' for i, (title, text) in enumerate(steps))
    return f'<div class="fb-timeline">{items}</div>'


def page() -> None:
    layout.page_head("How it works", "From surplus to **served**",
                     "A simple flow for donors and NGOs, with AI and smart matching doing the heavy lifting.",
                     art="ai_scan")

    donors, ngos = st.columns(2, gap="large")
    with donors:
        style.html('<h3 style="margin-top:0">🍱 For donors</h3>' + timeline(DONOR_STEPS))
    with ngos:
        style.html('<h3 style="margin-top:0">🏠 For NGOs & shelters</h3>' + timeline(NGO_STEPS))

    layout.section("Step by step", "The journey of a **donation**",
                   "Click a step to learn what happens — or press play to watch the whole flow.")
    flows.journey(run(public_ops.journey_stats()))

    layout.band("Food safety", "Is my food safe to **donate?**",
                "Answer three quick questions and follow the highlighted path through our safety check.")
    flows.safety_checker()

    layout.section("Smart matching", "How we choose the **right NGO**",
                   "Move the sliders to see how the Match Priority Score responds. This is the same formula "
                   "the platform uses for every donation.")
    flows.match_explainer()

    layout.section("Food safety limits", "How long food stays **safe**",
                   "Conservative room-temperature limits used to set pickup deadlines. Food past its limit, "
                   "or that looks spoiled, is not accepted.")
    rows = "".join(f"<tr><td>{escape(c['name'])}</td><td>{c['shelf_hours']} hours</td>"
                   f"<td>{'Non-veg' if c['non_veg'] else 'Veg'}</td></tr>" for c in CATEGORIES.values())
    style.html(f'<div class="fb-info"><table class="fb-table"><tr><th>Food type</th>'
               f'<th>Safe for about</th><th>Diet</th></tr>{rows}</table></div>')

    layout.section("FAQ", "Frequently asked **questions**")
    faqs = [
        ("Is FoodBridge free?", "Yes — for donors and NGOs alike."),
        ("Who can see my address and phone number?",
         "Only the NGO that accepts your donation. Public pages show just the general area."),
        ("What if the AI gets the dish wrong?",
         "You always enter the food name and category yourself; the AI result is a helpful check, and the "
         "freshness score also uses the cooking time you provide."),
        ("What happens if no NGO accepts my food?",
         "If a matched NGO doesn't accept within the time limit or declines, the donation is offered to the "
         "next-best NGO automatically. Food that passes its safe time is marked expired."),
        ("How are NGOs verified?", "Our admin team reviews each registration before it can receive matches."),
    ]
    for question, answer in faqs:
        with st.expander(question):
            st.write(answer)
