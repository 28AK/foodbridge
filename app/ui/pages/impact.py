"""Public impact dashboard."""
import altair as alt
import pandas as pd
import streamlit as st

from app.services import public_ops
from app.ui import layout, style
from app.ui.runtime import run

GREEN = "#3e6650"
PALETTE = ["#1daa55", "#3e6650", "#d2553b", "#e0a100", "#7fb69a", "#b9a98e", "#90a4ae", "#245b84"]
STATUS_NAMES = {"listed": "Waiting for NGO", "matched": "Matched", "picked_up": "In transit",
                "delivered": "Delivered", "expired": "Expired", "cancelled": "Cancelled",
                "rejected": "Rejected (unsafe)"}


def page() -> None:
    layout.page_head("Impact", "What FoodBridge has **achieved**",
                     "Live figures from every donation on the platform.",
                     art="served")
    stats = run(public_ops.impact())
    layout.counters([
        (f"{stats['meals_delivered']:,}", "meals delivered"),
        (f"{stats['kg_saved']:,} kg", "food waste avoided*"),
        (f"{stats['deliveries']:,}", "successful pickups"),
        (f"{stats['donors']:,}", "registered donors"),
    ])
    st.caption(f"*Estimated at {public_ops.KG_PER_SERVING} kg per meal.")

    if not stats["donations"]:
        st.write("")
        layout.empty("📊", "No donations yet", "Charts will appear here once food starts moving.")
        return

    per_day = pd.DataFrame(run(public_ops.delivered_per_day(30)))
    left, right = st.columns([1.6, 1], gap="large")
    with left, st.container(border=True):
        st.subheader("Meals delivered — last 30 days", anchor=False)
        if per_day.empty:
            st.caption("No deliveries in the last 30 days.")
        else:
            per_day["date"] = pd.to_datetime(per_day["date"])
            chart = alt.Chart(per_day).mark_bar(color=GREEN, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("date:T", title=None, axis=alt.Axis(format="%d %b")),
                y=alt.Y("meals:Q", title="Meals"),
                tooltip=[alt.Tooltip("date:T", format="%d %b %Y"), "meals:Q", "deliveries:Q"],
            ).properties(height=300)
            st.altair_chart(chart, width="stretch")
    with right, st.container(border=True):
        st.subheader("Donation outcomes", anchor=False)
        outcomes = pd.DataFrame([{"status": STATUS_NAMES.get(k, k), "count": v}
                                 for k, v in stats["by_status"].items()])
        donut = alt.Chart(outcomes).mark_arc(innerRadius=60).encode(
            theta="count:Q",
            color=alt.Color("status:N", scale=alt.Scale(range=PALETTE), legend=alt.Legend(title=None, orient="bottom")),
            tooltip=["status:N", "count:Q"],
        ).properties(height=300)
        st.altair_chart(donut, width="stretch")

    by_cat = pd.DataFrame(run(public_ops.delivered_by_category()))
    by_area = pd.DataFrame(run(public_ops.delivered_by_area()))
    c1, c2 = st.columns(2, gap="large")
    for col, df, field, title in [(c1, by_cat, "category", "Meals delivered by food type"),
                                  (c2, by_area, "area", "Meals delivered by area")]:
        with col, st.container(border=True):
            st.subheader(title, anchor=False)
            if df.empty:
                st.caption("No deliveries yet.")
                continue
            bars = alt.Chart(df).mark_bar(color="#1daa55", cornerRadiusEnd=4).encode(
                y=alt.Y(f"{field}:N", sort="-x", title=None),
                x=alt.X("meals:Q", title="Meals"),
                tooltip=[f"{field}:N", "meals:Q"],
            ).properties(height=max(160, 34 * len(df)))
            st.altair_chart(bars, width="stretch")

    style.html('<div class="fb-cta"><h3>Want to add to these numbers?</h3>'
               "<p>Every listing helps. Donors and NGOs can join for free.</p></div>")
    st.write("")
    if not st.session_state.get("user_id"):
        layout.link("signin", "Join FoodBridge", icon=":material/arrow_forward:")
