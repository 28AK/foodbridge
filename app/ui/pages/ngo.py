"""NGO dashboard: today's capacity, incoming matches, pickup lifecycle, route map."""
from html import escape

import folium
import streamlit as st

from app.services import ngo_ops
from app.ui import style
from app.ui.components import pin, show_map, thumb_uri
from app.ui.runtime import run, try_run

ORG_TYPES = {"ngo": "NGO", "shelter": "Shelter", "community_kitchen": "Community kitchen"}


def page() -> None:
    dashboard(st.session_state["user"])


@st.fragment(run_every=20)
def dashboard(user: dict) -> None:
    ngo = run(ngo_ops.ngo_for(user))
    profile = run(ngo_ops.profile(ngo))
    active = run(ngo_ops.matches(ngo, "active"))
    history = run(ngo_ops.matches(ngo, "history"))
    route = run(ngo_ops.route(ngo))

    title, demand_col = st.columns([4, 1], vertical_alignment="center")
    with title:
        st.title(ngo["name"], anchor=False)
        st.caption(f"{ORG_TYPES.get(ngo['type'], ngo['type'])} · {ngo['address']}"
                   f"{' · 🟢 veg only' if ngo['veg_only'] else ''} · updates every 20 seconds")
    with demand_col, st.popover("✏️ Today's demand", width="stretch"):
        demand = st.number_input("Meals needed today", 0, 10_000, profile["current_demand"])
        if st.button("Save", type="primary"):
            try_run(ngo_ops.update(profile, {"current_demand": int(demand)}))
            st.rerun()
    if not ngo["verified"]:
        style.html('<div class="fb-banner">⏳ Your organisation is awaiting verification by an admin. '
                   "You'll start receiving food matches once verified.</div>")

    new = [l for l in active if l["status"] == "matched" and not l["match"]["accepted_at"]]
    to_collect = [l for l in active if l["status"] == "matched" and l["match"]["accepted_at"]]
    in_transit = [l for l in active if l["status"] == "picked_up"]
    order = {s["id"]: s["order"] for s in route["stops"]}
    to_collect.sort(key=lambda l: order.get(l["_id"], 99))

    stats(profile, new, to_collect, in_transit, history)

    left, right = st.columns([1.1, 1], gap="large")
    with left, st.container(border=True):
        st.subheader("🗺️ Pickup route", anchor=False)
        route_map(ngo, active, route, order)
    with right:
        tabs = st.tabs([f"🔔 New ({len(new)})", f"🚐 Collect ({len(to_collect)})",
                        f"📦 Transit ({len(in_transit)})", f"✅ Done ({len(history)})"])
        with tabs[0]:
            listing_cards(ngo, new, "No new matches right now.",
                          [("Accept", "accept", "primary"), ("Decline", "decline", "secondary")])
        with tabs[1]:
            listing_cards(ngo, to_collect, "Nothing to collect.",
                          [("Mark picked up", "picked_up", "primary")], order=order)
        with tabs[2]:
            listing_cards(ngo, in_transit, "Nothing in transit.",
                          [("Mark delivered", "delivered", "primary")])
        with tabs[3]:
            listing_cards(ngo, list(reversed(history))[:20], "No deliveries yet.", [])


def stats(profile: dict, new, to_collect, in_transit, history) -> None:
    today = profile["today"]
    used = today["received_servings"] / profile["capacity_meals"] * 100 if profile["capacity_meals"] else 0
    c1, c2, c3 = st.columns(3)
    with c1:
        style.html(style.stat("Received today", f"{today['received_servings']} meals",
                              f"of {profile['capacity_meals']} capacity · {today['free_capacity']} free",
                              extra=style.meter(used, "low")))
    with c2:
        style.html(style.stat("Still needed today", f"{today['unmet_demand']} meals",
                              f"daily demand set to {profile['current_demand']}"))
    with c3:
        style.html(style.stat("Pickups", f"{len(new) + len(to_collect) + len(in_transit)} active",
                              f"{len(new)} new · {len(to_collect)} to collect · {len(in_transit)} in transit"))


def route_map(ngo: dict, active: list[dict], route: dict, order: dict) -> None:
    lng, lat = ngo["location"]["coordinates"]
    m = folium.Map(location=(lat, lng), zoom_start=13, control_scale=True)
    folium.Marker((lat, lng), tooltip=ngo["name"], icon=pin("🏠", "#ffffff")).add_to(m)
    points = [(lat, lng)]
    for listing in active:
        plng, plat = listing["location"]["coordinates"]
        points.append((plat, plng))
        if listing["_id"] in order:
            label, color = str(order[listing["_id"]]), "#2e7d32"
        elif listing["status"] == "picked_up":
            label, color = "✓", "#5e35b1"
        else:
            label, color = "•", "#ef6c00"
        folium.Marker((plat, plng), icon=pin(label, color),
                      tooltip=f"{listing['food_name']} · {listing['quantity_servings']} servings").add_to(m)
    if route["stops"]:
        origin = (route["origin"]["lat"], route["origin"]["lng"])
        path = [origin, *[(s["lat"], s["lng"]) for s in route["stops"]], origin]
        folium.PolyLine(path, color="#2e7d32", weight=4, opacity=0.8, dash_array="8 6").add_to(m)
    if len(points) > 1:
        m.fit_bounds(points, padding=(30, 30), max_zoom=15)
    show_map(m, key="ngo_route_map", height=430)

    if route["stops"]:
        steps = " → ".join(f"**{s['order']}.** {s['food_name']} (≈{style.fmt_dt(s['eta'])}"
                           f"{'' if s['on_time'] else ' ⚠️ late'})" for s in route["stops"])
        st.markdown(f"{steps} → back to kitchen")
        st.caption(f"Total ≈ {route['total_km']} km · finish ≈ {style.fmt_dt(route['estimated_finish'])}"
                   f"{'' if route['all_on_time'] else ' · ⚠️ some pickups may miss their deadline'}")
        st.link_button("Open route in Google Maps", route["maps_url"], type="primary")
    else:
        st.caption("🟠 new match · 🟢 numbered = accepted pickups in suggested order · 🟣 picked up. "
                   "Accept matches to get a route.")


ACTIONS = {"accept": ngo_ops.accept, "decline": ngo_ops.decline,
           "picked_up": ngo_ops.picked_up, "delivered": ngo_ops.delivered}


def listing_cards(ngo: dict, listings: list[dict], empty: str, actions: list[tuple],
                  order: dict | None = None) -> None:
    if not listings:
        st.caption(empty)
        return
    for listing in listings:
        with st.container(border=True):
            style.html(match_card(listing, order))
            if actions:
                with st.container(horizontal=True, gap="small"):
                    for label, action, kind in actions:
                        if st.button(label, key=f"{action}_{listing['_id']}", type=kind):
                            if try_run(ACTIONS[action](ngo, listing["_id"])):
                                st.rerun()


def match_card(listing: dict, order: dict | None) -> str:
    m = listing["match"]
    veg = "🟢 Veg" if listing["food_category"] == "veg" else "🔴 Non-veg"
    stop = f"Stop {order[listing['_id']]} · " if order and listing["_id"] in order else ""
    lines = [
        f'<span class="fb-muted">{stop}{listing["quantity_servings"]} servings · {veg}</span> '
        f'{style.risk_badge(listing.get("freshness"))}',
        f'<span class="fb-muted">Pick up by <b>{style.fmt_dt(listing["pickup_deadline"])}</b> '
        f'({style.time_left(listing["pickup_deadline"])}) · {m["distance_km"]} km · ~{m["eta_minutes"]} min</span>',
        f'<span class="fb-muted">{escape(listing["donor_name"])} · {escape(listing["address"])}</span>',
    ]
    if m.get("accepted_at"):
        lines.append(f'<span class="fb-muted">📞 {escape(listing["donor_phone"])}</span>')
    if listing.get("pickup_notes"):
        lines.append(f'<span class="fb-muted">📝 {escape(listing["pickup_notes"])}</span>')
    ai = f" · AI: {escape(listing['ai']['dish']['name'])}" if listing.get("ai") else ""
    b = m["breakdown"]
    lines.append(f'<span class="fb-muted" title="distance {b["distance"]} · capacity {b["capacity"]} · '
                 f'demand {b["demand"]} · time {b["time"]}">Match score <b>{m["score"]}</b>/100{ai}</span>')
    return style.item(thumb_uri(listing["images"]["processed"]), listing["food_name"], lines)
