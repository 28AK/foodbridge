"""Interactive flowcharts:

* journey()          – clickable, animated "journey of a donation" with live numbers (HTML + JS)
* safety_checker()   – "Is my food safe to donate?" decision flowchart driven by widgets
* match_explainer()  – sliders feeding the real matching score, with a live breakdown chart
"""
import json
import uuid
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from app.services.food_catalog import CATEGORIES
from app.services.freshness import MIN_PICKUP_HOURS
from app.services.geo import HANDLING_MINUTES, travel_minutes
from app.services.matching import MAX_RADIUS_KM, WEIGHTS, score_candidate
from app.ui import style

# Step icons (emoji: Streamlit's HTML sanitiser strips inline <svg> here)
ICONS = {"camera": "📸", "wand": "🪄", "brain": "🧠", "gauge": "⏱️", "pin": "📍",
         "check": "🤝", "truck": "🛵", "heart": "🍽️"}


def _icon(name: str) -> str:
    return f'<span style="font-size:1.6rem">{ICONS[name]}</span>'


# ---------------------------------------------------------------------------
# 1. Journey of a donation
# ---------------------------------------------------------------------------
JOURNEY_CSS = """
.fbj { background: #fff; border: 1px solid var(--fb-border); border-radius: 22px; padding: 26px 26px 20px; }
.fbj-track { display: flex; align-items: flex-start; overflow-x: auto; padding: 6px 2px 14px; scrollbar-width: thin; }
.fbj-node { flex: 0 0 auto; width: 104px; background: none; border: 0; padding: 0; cursor: pointer;
            display: flex; flex-direction: column; align-items: center; gap: 8px; font: inherit; color: var(--fb-muted); }
.fbj-circle { position: relative; width: 64px; height: 64px; border-radius: 50%; background: var(--fb-bg);
              border: 2px solid var(--fb-border); color: var(--fb-forest); display: flex; align-items: center;
              justify-content: center; transition: all .25s ease; }
.fbj-node:hover .fbj-circle { transform: translateY(-3px); border-color: var(--fb-bright); }
.fbj-node.done .fbj-circle { background: #e7f4ea; border-color: var(--fb-bright); color: var(--fb-bright); }
.fbj-node.active .fbj-circle { background: var(--fb-forest); border-color: var(--fb-forest); color: #fff;
                               box-shadow: 0 0 0 6px rgba(62,102,80,.15); transform: scale(1.08); }
.fbj-badge { position: absolute; top: -6px; right: -10px; min-width: 22px; height: 22px; padding: 0 6px; border-radius: 999px;
             background: var(--fb-terra); color: #fff; font-size: .72rem; font-weight: 700; display: flex;
             align-items: center; justify-content: center; border: 2px solid #fff; }
.fbj-label { font-size: .8rem; font-weight: 600; text-align: center; line-height: 1.25; }
.fbj-node.active .fbj-label { color: var(--fb-forest); }
.fbj-link { flex: 1 0 26px; height: 2px; margin-top: 32px; min-width: 26px;
            background: repeating-linear-gradient(90deg, #d9cfbf 0 6px, transparent 6px 12px); }
.fbj-link.lit { background: repeating-linear-gradient(90deg, var(--fb-terra) 0 6px, transparent 6px 12px);
                background-size: 24px 2px; animation: fbj-flow .9s linear infinite; }
@keyframes fbj-flow { to { background-position: 24px 0; } }
.fbj-panel { display: grid; grid-template-columns: 1fr auto; gap: 18px; align-items: center; margin-top: 8px;
             padding: 18px 20px; border-radius: 16px; background: var(--fb-bg); border-left: 4px solid var(--fb-terra); }
.fbj-panel .step { color: var(--fb-terra); font-weight: 700; font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; }
.fbj-panel h3 { margin: 4px 0 6px; color: var(--fb-forest); font-size: 1.25rem; }
.fbj-panel p { margin: 0; color: var(--fb-muted); line-height: 1.6; }
.fbj-stat { text-align: right; min-width: 120px; }
.fbj-stat b { display: block; font-size: 2rem; color: var(--fb-bright); line-height: 1.1; }
.fbj-stat span { color: var(--fb-muted); font-size: .82rem; }
.fbj-controls { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }
.fbj-controls button { width: 46px; height: 46px; border-radius: 50%; border: 1.5px solid var(--fb-forest); background: #fff;
                       color: var(--fb-forest); cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; }
.fbj-controls button.play { width: auto; padding: 0 20px; border-radius: 999px; background: var(--fb-forest); color: #fff; font-weight: 600; font-family: inherit; }
.fbj-controls button:hover { box-shadow: 0 4px 12px rgba(36,51,43,.15); }
@media (max-width: 640px) { .fbj-panel { grid-template-columns: 1fr; } .fbj-stat { text-align: left; } }
"""

JOURNEY_JS = """
(function () {
  const root = document.getElementById("%(id)s");
  if (!root) return;
  const steps = %(steps)s;
  const nodes = root.querySelectorAll(".fbj-node"), links = root.querySelectorAll(".fbj-link");
  const panel = { step: root.querySelector(".step"), title: root.querySelector("h3"), text: root.querySelector(".fbj-panel p"),
                  num: root.querySelector(".fbj-stat b"), lbl: root.querySelector(".fbj-stat span") };
  const playBtn = root.querySelector(".play");
  let current = 0, timer = null;
  function show(i) {
    current = (i + steps.length) %% steps.length;
    nodes.forEach((n, k) => { n.classList.toggle("active", k === current); n.classList.toggle("done", k < current); });
    links.forEach((l, k) => l.classList.toggle("lit", k < current));
    const s = steps[current];
    panel.step.textContent = "Step " + (current + 1) + " of " + steps.length;
    panel.title.textContent = s.title; panel.text.textContent = s.text;
    panel.num.textContent = s.stat; panel.lbl.textContent = s.stat_label;
  }
  function stop() { clearInterval(timer); timer = null; playBtn.textContent = "▶ Play journey"; }
  function play() {
    if (timer) return stop();
    if (current === steps.length - 1) show(0);
    playBtn.textContent = "❚❚ Pause";
    timer = setInterval(() => { if (current === steps.length - 1) return stop(); show(current + 1); }, 2200);
  }
  nodes.forEach((n, k) => n.addEventListener("click", () => { stop(); show(k); }));
  root.querySelector(".prev").addEventListener("click", () => { stop(); show(current - 1); });
  root.querySelector(".next").addEventListener("click", () => { stop(); show(current + 1); });
  playBtn.addEventListener("click", play);
  show(0);
})();
"""


def journey(stats: dict) -> None:
    """Interactive 'journey of a donation' flowchart. `stats` comes from public_ops.journey_stats()."""
    steps = [
        ("camera", "Donor lists food", "A restaurant, hotel, caterer or household photographs surplus food and "
         "enters the servings and cooking time.", stats["donations"], "donations listed so far"),
        ("wand", "Photo clean-up", "OpenCV fixes rotation, resizes the photo, and repairs dark or low-contrast "
         "images with denoising, gamma correction and CLAHE.", stats["enhanced"], "photos auto-enhanced"),
        ("brain", "AI food check", "A pretrained CLIP model confirms it's food, recognises the dish, estimates "
         "the quantity and looks for visible spoilage.", stats["analysed"], "photos analysed by AI"),
        ("gauge", "Risk & deadline", "Food age and the spoilage signal combine into a 0–100 risk score and a "
         "pickup deadline. Unsafe food is stopped here.", stats["rejected"], "unsafe donations stopped"),
        ("pin", "Smart match", f"Verified NGOs within {MAX_RADIUS_KM} km are scored on distance, free capacity, "
         "today's demand and time to reach — the best one is alerted.", stats["waiting"], "waiting for an NGO now"),
        ("check", "NGO accepts", "The NGO accepts or declines. Declined or unanswered matches move to the "
         "next-best NGO automatically.", stats["matched"], "matched right now"),
        ("truck", "Pickup", "The NGO follows a suggested route that visits the most urgent pickups first, "
         "then marks the food picked up.", stats["in_transit"], "on the way right now"),
        ("heart", "Served", "Food reaches the kitchen or shelter and is marked delivered — the meal is counted "
         "in our impact numbers.", stats["meals_delivered"], "meals delivered"),
    ]
    root_id = f"fbj-{uuid.uuid4().hex[:8]}"
    track = []
    for i, (icon, title, _, count, _) in enumerate(steps):
        if i:
            track.append('<div class="fbj-link"></div>')
        badge = f'<span class="fbj-badge">{count}</span>' if count else ""
        track.append(f'<button class="fbj-node" type="button" aria-label="{escape(title)}">'
                     f'<span class="fbj-circle">{_icon(icon)}{badge}</span>'
                     f'<span class="fbj-label">{escape(title)}</span></button>')
    data = json.dumps([{"title": t, "text": d, "stat": f"{c:,}", "stat_label": lbl}
                       for _, t, d, c, lbl in steps])
    st.html(f"""<style>{JOURNEY_CSS}</style>
    <div class="fbj" id="{root_id}">
      <div class="fbj-track">{''.join(track)}</div>
      <div class="fbj-panel"><div><div class="step"></div><h3></h3><p></p></div>
        <div class="fbj-stat"><b></b><span></span></div></div>
      <div class="fbj-controls"><button class="prev" type="button" aria-label="Previous step">←</button>
        <button class="play" type="button">▶ Play journey</button>
        <button class="next" type="button" aria-label="Next step">→</button></div>
    </div>
    <script>{JOURNEY_JS % {"id": root_id, "steps": data}}</script>""", unsafe_allow_javascript=True)


# ---------------------------------------------------------------------------
# 2. Is my food safe to donate?  (decision flowchart)
# ---------------------------------------------------------------------------
FLOW_CSS = """
.fbf { display: flex; flex-direction: column; align-items: center; gap: 0; }
.fbf-node { width: min(100%, 440px); text-align: center; padding: 12px 18px; border-radius: 14px; background: #fff;
            border: 1.5px solid var(--fb-border); color: var(--fb-muted); font-weight: 600; transition: all .3s; }
.fbf-node small { display: block; font-weight: 500; font-size: .8rem; margin-top: 2px; }
.fbf-node.decision { border-radius: 999px; }
.fbf-node.on { border-color: var(--fb-forest); color: var(--fb-forest); box-shadow: 0 6px 18px rgba(36,51,43,.08); }
.fbf-node.off { opacity: .45; }
.fbf-node.fail { border-color: var(--fb-terra); color: #a33a24; background: #fdf3f0; }
.fbf-edge { position: relative; width: 2px; height: 30px; background: #d9cfbf; }
.fbf-edge.on { background: repeating-linear-gradient(180deg, var(--fb-terra) 0 6px, transparent 6px 11px);
               background-size: 2px 22px; animation: fbf-flow .8s linear infinite; }
.fbf-edge span { position: absolute; left: 10px; top: 6px; font-size: .72rem; font-weight: 700; color: var(--fb-terra); white-space: nowrap; }
@keyframes fbf-flow { to { background-position: 0 22px; } }
.fbf-result { width: min(100%, 440px); text-align: center; padding: 16px 18px; border-radius: 16px; font-weight: 700; font-size: 1.05rem; }
.fbf-result.ok { background: #e7f4ea; color: #1b6b3a; border: 2px solid var(--fb-bright); }
.fbf-result.warn { background: #fff1d6; color: #8a5a00; border: 2px solid #e0a100; }
.fbf-result.no { background: #fbe9e5; color: #a33a24; border: 2px solid var(--fb-terra); }
.fbf-result small { display: block; font-weight: 500; font-size: .86rem; margin-top: 4px; }
"""

URGENT_HOURS = 2


def _decide(looks_ok: bool, hours: float, shelf: int) -> tuple[list[bool], str, str, str]:
    """Return which checks passed, result class, result title, result detail."""
    remaining = shelf - hours
    checks = [looks_ok, looks_ok and remaining > 0, looks_ok and remaining >= MIN_PICKUP_HOURS]
    if not looks_ok:
        return checks, "no", "🚫 Please don't donate", "Food that looks or smells off isn't safe for anyone."
    if remaining <= 0:
        return checks, "no", "🚫 Too old to donate", f"It has passed its ~{shelf} h safe limit at room temperature."
    if remaining < MIN_PICKUP_HOURS:
        return checks, "no", "⏱️ Not enough time left", "There isn't enough time for an NGO to collect it safely."
    if remaining < URGENT_HOURS:
        return checks, "warn", "⚡ Donate now — urgent", f"Only about {remaining:.1f} h left. List it right away."
    return checks, "ok", "✅ Safe to donate", f"An NGO should collect it within about {remaining:.1f} h."


def safety_checker() -> None:
    controls, chart = st.columns([1, 1.2], gap="large")
    with controls, st.container(border=True):
        st.subheader("Your food", anchor=False)
        key = st.selectbox("What kind of food is it?", list(CATEGORIES),
                           format_func=lambda k: CATEGORIES[k]["name"], key="safe_cat")
        hours = st.slider("Hours since it was cooked", 0.0, 24.0, 2.0, 0.5, key="safe_hours")
        looks_ok = st.radio("Does it look and smell fine?", ["Yes", "No"], horizontal=True, key="safe_look") == "Yes"
        shelf = CATEGORIES[key]["shelf_hours"]
        st.caption(f"{CATEGORIES[key]['name']} stay safe for about **{shelf} hours** at room temperature.")

    checks, kind, title, detail = _decide(looks_ok, hours, shelf)
    labels = [
        ("Looks and smells fresh?", "No mould, sour smell or discolouration"),
        (f"Within ~{shelf} h of cooking?", "Room-temperature safe limit for this food"),
        (f"At least {int(MIN_PICKUP_HOURS * 60)} min left to collect?", "Time for an NGO to reach you"),
    ]
    # Every question is drawn; the path taken lights up, a failed check turns red, later steps fade
    parts = ['<div class="fbf"><div class="fbf-node on">🍲 Surplus food<small>Start here</small></div>']
    failed = False
    for i, (passed, (question, hint)) in enumerate(zip(checks, labels)):
        reached = not failed
        label = "<span>YES</span>" if i and reached else ""
        parts.append(f'<div class="fbf-edge{" on" if reached else ""}">{label}</div>')
        state = "fail" if reached and not passed else "on" if reached else "off"
        parts.append(f'<div class="fbf-node decision {state}">{escape(question)}<small>{escape(hint)}</small></div>')
        failed = failed or not passed
    parts.append(f'<div class="fbf-edge on"><span>{"NO" if failed else "YES"}</span></div>')
    parts.append(f'<div class="fbf-result {kind}">{title}<small>{escape(detail)}</small></div></div>')
    with chart:
        style.html(f"<style>{FLOW_CSS}</style>{''.join(parts)}")


# ---------------------------------------------------------------------------
# 3. How we choose the NGO  (live matching score)
# ---------------------------------------------------------------------------
FACTOR_NAMES = {"distance": "Distance", "capacity": "Free capacity", "demand": "Unmet demand", "time": "Time margin"}


def match_explainer() -> None:
    inputs, result = st.columns([1, 1.2], gap="large")
    with inputs, st.container(border=True):
        st.subheader("Try it: one NGO, one donation", anchor=False)
        servings = st.slider("Servings donated", 5, 200, 40, 5, key="mx_serv")
        distance = st.slider("NGO distance (km)", 0.5, float(MAX_RADIUS_KM), 4.0, 0.5, key="mx_dist")
        capacity = st.slider("NGO free capacity today (meals)", 0, 400, 120, 10, key="mx_cap")
        demand = st.slider("NGO unmet demand today (meals)", 0, 400, 60, 10, key="mx_dem")
        hours = st.slider("Hours until the food's pickup deadline", 0.5, 12.0, 4.0, 0.5, key="mx_hours")

    scored = score_candidate(distance, capacity, demand, servings, hours)
    with result, st.container(border=True):
        st.subheader("Match Priority Score", anchor=False)
        if scored is None:
            eta = travel_minutes(distance) + HANDLING_MINUTES
            reason = ("the NGO has no free capacity today" if capacity <= 0 else
                      f"it would take ~{eta:.0f} min to arrive, after the deadline")
            style.html(f'<div class="fbf-result no">Not eligible<small>This NGO is skipped because {reason}.</small></div>')
            return
        level = "low" if scored["score"] >= 70 else "medium" if scored["score"] >= 45 else "high"
        style.html(f'<div style="display:flex;align-items:baseline;gap:10px"><span style="font-size:3rem;font-weight:800;'
                   f'color:var(--fb-bright)">{scored["score"]:.0f}</span><span class="fb-muted">/ 100 · arrives in ~'
                   f'{scored["eta_minutes"]} min</span></div>{style.meter(scored["score"], level)}')
        rows = [{"factor": FACTOR_NAMES[k], "points": round(WEIGHTS[k] * v * 100, 1),
                 "max": WEIGHTS[k] * 100} for k, v in scored["breakdown"].items()]
        df = pd.DataFrame(rows)
        base = alt.Chart(df).encode(y=alt.Y("factor:N", sort=None, title=None))
        chart = (base.mark_bar(color="#ece5d8", cornerRadiusEnd=4).encode(x=alt.X("max:Q", title="Points"))
                 + base.mark_bar(color="#1daa55", cornerRadiusEnd=4).encode(
                     x="points:Q", tooltip=["factor:N", "points:Q", alt.Tooltip("max:Q", title="out of")]))
        st.altair_chart(chart.properties(height=170), width="stretch")
        best = max(rows, key=lambda r: r["points"] / r["max"])
        weakest = min(rows, key=lambda r: r["points"] / r["max"])
        st.caption(f"Strongest factor: **{best['factor']}** · weakest: **{weakest['factor']}**. "
                   "The NGO with the highest score among all eligible ones gets the match.")
