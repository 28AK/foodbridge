"""About the project and team."""
import streamlit as st

from app.ui import layout, style

TEAM = ["Amrita Singh", "Akash Gupta", "Akanksha Pandey", "Akanksha Singh"]
STACK = ["Python 3.11", "Streamlit", "FastAPI", "MongoDB Atlas", "PyTorch", "CLIP (Hugging Face)",
         "OpenCV", "Leaflet / folium"]


def page() -> None:
    layout.page_head("About", "Why we built **FoodBridge**",
                     "A final-year B.Tech (CSE – Artificial Intelligence) project at Babu Banarasi Das University, Lucknow.",
                     art="route")

    left, right = st.columns([1.4, 1], gap="large")
    with left:
        style.html("""<div class="fb-info"><h4>The problem</h4>
          <p>Restaurants, hotels, caterers, events and households throw away edible surplus food every day,
          while shelters and community kitchens nearby struggle to feed everyone. Food donation today runs on
          phone calls and messaging groups — by the time a recipient is found, the food has often spoiled.</p>
          <h4>Our approach</h4>
          <p>FoodBridge automates the whole chain: AI checks every donation's type, quantity and freshness from
          a photo, a matching engine picks the most suitable verified NGO by distance, capacity and demand, and
          the pickup is tracked until delivery.</p></div>""")
    with right:
        chips = "".join(f'<span class="fb-chip" style="margin:0 6px 6px 0">{t}</span>' for t in STACK)
        style.html(f'<div class="fb-info"><h4>Built with</h4><div>{chips}</div></div>')

    layout.section("The team", "Who's behind **FoodBridge**")
    members = "".join(
        f'<div class="fb-card"><div class="body"><div class="head"><div class="fb-icon-tile">'
        f'{name.split()[0][0]}{name.split()[-1][0]}</div><div><div class="title">{name}</div>'
        f'<div class="meta">B.Tech CSE (AI)</div></div></div></div></div>' for name in TEAM)
    style.html(f'<div class="fb-grid four">{members}</div>')
    st.write("")
    style.html("""<div class="fb-info"><h4>Project guide</h4>
      <p><b>Ms. Surbhi</b>, Assistant Professor, Department of Computer Science & Engineering,
      School of Engineering, Babu Banarasi Das University, Lucknow.</p></div>""")
