"""Custom HTML/CSS for the Streamlit UI: theme polish, cards, badges, meters."""
import base64
from datetime import datetime, timedelta, timezone
from html import escape

import streamlit as st

IST = timezone(timedelta(hours=5, minutes=30))

# The Inter font is set in .streamlit/config.toml. Don't override font-family on Streamlit's
# own elements here: its icons use the Material Symbols font, and replacing it makes icon
# names ("arrow_right", "visibility", "upload") show up as overlapping text.
CSS = """
:root {
  --fb-forest: #3e6650; --fb-bright: #1daa55; --fb-terra: #d2553b; --fb-sand: #f1ece3;
  --fb-green: #2f9e5a; --fb-green-dark: #3e6650; --fb-green-light: #e7f4ea;
  --fb-bg: #faf6f0; --fb-card: #ffffff; --fb-border: #e9e2d6;
  --fb-text: #24332b; --fb-muted: #5c6b62; --fb-error: #c62828;
}
.stApp { background: var(--fb-bg); }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 5.5rem; padding-bottom: 0; max-width: 1240px; }

/* Header: flat full-width bar — logo left, page links centred, account / sign-in right */
header[data-testid="stHeader"] {
  background: rgba(255, 255, 255, 0.96); backdrop-filter: blur(8px); border-bottom: 1px solid var(--fb-border);
}
header [data-testid="stToolbar"] div:has(> div > div > [data-testid="stTopNavLinkContainer"]) {
  flex: 1; justify-content: center;
}
header [data-testid="stToolbar"], header [data-testid="stToolbar"] * { position: static; }
/* Sign-in link (logged out) or the account dropdown (logged in) sits at the far right */
header div:has(> div > [data-testid="stTopNavLinkContainer"] a[href$="sign-in"]),
header div:has(> button[data-testid="stTopNavSection"]) { position: absolute !important; right: 24px; top: 50%; transform: translateY(-50%); }
header a[data-testid="stTopNavLink"][href$="sign-in"] { background: var(--fb-forest); border-radius: 999px; padding: 6px 18px; }
header a[data-testid="stTopNavLink"][href$="sign-in"] * { color: #fff !important; }
h1, h2, h3 { color: var(--fb-forest); letter-spacing: -0.015em; font-weight: 700; }
.accent { color: var(--fb-bright); }

/* Bordered Streamlit containers become white cards */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
  background: var(--fb-card); border-radius: 14px; border-color: var(--fb-border) !important;
  box-shadow: 0 1px 3px rgba(31, 42, 31, 0.05);
}
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--fb-border); }
.stButton > button, .stLinkButton > a, .stFormSubmitButton > button { border-radius: 999px; font-weight: 600; padding-left: 1.2rem; padding-right: 1.2rem; }
/* Call-to-action links (page links inside a container keyed "fb-ctas-...") as pills */
[class*="st-key-fb-ctas"] [data-testid="stPageLink"] a {
  border: 1.5px solid var(--fb-forest); border-radius: 999px; padding: 8px 20px; background: #fff;
}
[class*="st-key-fb-ctas"] [data-testid="stPageLink"] a * { color: var(--fb-forest) !important; font-weight: 600; }
/* Only the first call-to-action is filled; the rest stay outlined */
[class*="st-key-fb-ctas"] > div:first-child [data-testid="stPageLink"] a { background: var(--fb-forest); }
[class*="st-key-fb-ctas"] > div:first-child [data-testid="stPageLink"] a * { color: #fff !important; }
/* Never shrink a button below its label (otherwise "Mark picked up" gets cut to "Mark picke…") */
.stButton > button, .stLinkButton > a { min-width: max-content; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }

/* ---------- Public site ---------- */
/* Hero: big two-tone heading on cream, line-art illustration inside a sand circle */
.fb-hero { position: relative; display: grid; grid-template-columns: 1.15fr 1fr; gap: 24px; align-items: center;
           padding: 18px 0 8px; }
.fb-hero .eyebrow { display: inline-block; color: var(--fb-terra); font-weight: 700; font-size: 0.8rem;
                    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 14px; }
.fb-hero h1 { font-size: clamp(2.1rem, 4.4vw, 3.4rem); line-height: 1.08; margin: 0 0 18px; font-weight: 800; }
.fb-hero p { color: var(--fb-muted); font-size: 1.08rem; line-height: 1.7; max-width: 560px; margin: 0;
             padding-top: 16px; border-top: 1px solid #d9cfbf; }
.fb-hero .art { position: relative; aspect-ratio: 1; max-width: 480px; justify-self: end; width: 100%; }
.fb-hero .art::before { content: ""; position: absolute; inset: 6%; border-radius: 50%; background: var(--fb-sand); }
.fb-hero .art img { position: relative; width: 100%; height: 100%; }
@media (max-width: 860px) { .fb-hero { grid-template-columns: minmax(0, 1fr); } .fb-hero .art { justify-self: center; max-width: 340px; } }

/* Thin terracotta arc used as a decorative divider */
.fb-arc { height: 64px; margin: 8px 0 -8px; background: no-repeat center / 100% 100% url("__ARC_URI__"); }

.fb-page-head { position: relative; display: grid; grid-template-columns: 1.6fr 1fr; gap: 20px; align-items: center;
                padding: 8px 0 18px; margin-bottom: 18px; border-bottom: 1px solid #d9cfbf; }
.fb-page-head.no-art { grid-template-columns: minmax(0, 1fr); }
.fb-page-head .kicker, .fb-section .kicker { color: var(--fb-terra); font-weight: 700; font-size: 0.78rem;
                                              letter-spacing: 0.1em; text-transform: uppercase; }
.fb-page-head h1 { margin: 6px 0 10px; font-size: clamp(1.9rem, 3.4vw, 2.8rem); font-weight: 800; line-height: 1.1; }
.fb-page-head p { margin: 0; color: var(--fb-muted); max-width: 680px; line-height: 1.65; }
.fb-page-head img { max-height: 190px; justify-self: end; }
@media (max-width: 760px) { .fb-page-head { grid-template-columns: minmax(0, 1fr); } .fb-page-head img { display: none; } }

.fb-section { margin: 52px 0 18px; }
.fb-section h2 { margin: 6px 0 8px; font-size: clamp(1.6rem, 3vw, 2.3rem); font-weight: 800; line-height: 1.12; }
.fb-section p { color: var(--fb-muted); margin: 0; max-width: 700px; line-height: 1.65; }

/* Full-width forest band (no horizontal scroll: shadow + clip-path bleed trick) */
.fb-band { background: var(--fb-forest); color: #fff; padding: 46px 0; margin: 44px 0 10px;
           box-shadow: 0 0 0 100vmax var(--fb-forest); clip-path: inset(0 -100vmax); }
.fb-band h2 { color: #fff; margin: 6px 0 10px; font-size: clamp(1.6rem, 3vw, 2.3rem); font-weight: 800; }
.fb-band .kicker { color: #ffc9a8; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.1em; text-transform: uppercase; }
.fb-band p { color: rgba(255, 255, 255, 0.82); line-height: 1.65; }
.fb-band .accent { color: #6fe39a; }

.fb-counters { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; }
.fb-counter { padding: 6px 22px; border-left: 1px solid #d9cfbf; }
.fb-counter:first-child { border-left: none; padding-left: 0; }
.fb-counter .num { font-size: clamp(1.8rem, 3vw, 2.6rem); font-weight: 800; color: var(--fb-bright); line-height: 1.15; }
.fb-counter .lbl { color: var(--fb-muted); font-size: 0.92rem; }
.fb-band .fb-counter { border-color: rgba(255, 255, 255, 0.2); }
.fb-band .fb-counter .num { color: #6fe39a; } .fb-band .fb-counter .lbl { color: rgba(255, 255, 255, 0.8); }
@media (max-width: 900px) { .fb-counters { grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 18px; }
                            .fb-counter:nth-child(3) { border-left: none; padding-left: 0; } }

/* Feature columns with circular icon badges (like "Greenhouse emission / Water wastage / Pollution") */
.fb-steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 28px; }
.fb-step { position: relative; padding: 4px 4px 4px 0; }
.fb-step .n, .fb-badge-icon { width: 76px; height: 76px; border-radius: 50%; background: #fff; border: 1px solid var(--fb-border);
              display: flex; align-items: center; justify-content: center; margin-bottom: 14px;
              color: var(--fb-bright); font-weight: 800; font-size: 1.5rem; box-shadow: 0 6px 18px rgba(36, 51, 43, 0.06); }
.fb-step h4 { margin: 0 0 8px; color: var(--fb-forest); font-size: 1.15rem; font-weight: 700; }
.fb-step p { margin: 0; color: var(--fb-muted); font-size: 0.95rem; line-height: 1.65; }
@media (max-width: 760px) { .fb-steps { grid-template-columns: minmax(0, 1fr); } }

.fb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 270px), 1fr)); gap: 18px; }
.fb-grid.four { grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr)); }

.fb-card { background: #fff; border: 1px solid var(--fb-border); border-radius: 18px; overflow: hidden;
           display: flex; flex-direction: column; transition: box-shadow 0.2s, transform 0.2s; }
.fb-card:hover { box-shadow: 0 14px 30px rgba(36, 51, 43, 0.09); transform: translateY(-3px); }
.fb-card > img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; background: var(--fb-sand); display: block; }
.fb-card .body { padding: 16px 18px 18px; display: flex; flex-direction: column; gap: 7px; }
.fb-card .title { font-weight: 700; font-size: 1.05rem; color: var(--fb-forest); }
.fb-card .meta { color: var(--fb-muted); font-size: 0.88rem; }
.fb-card .row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.fb-card .head { display: flex; gap: 12px; align-items: flex-start; }
.fb-card .head > div { min-width: 0; }
.fb-card .title, .fb-card .meta { overflow-wrap: anywhere; }
.fb-icon-tile { width: 48px; height: 48px; border-radius: 50%; background: var(--fb-sand); flex-shrink: 0;
                display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; color: var(--fb-forest); }

.fb-chip { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 0.76rem; font-weight: 600;
           background: var(--fb-sand); color: var(--fb-forest); white-space: nowrap; }
.fb-chip.veg { background: #e7f4ea; color: #1b6b3a; }
.fb-chip.nonveg { background: #fbe9e5; color: #a33a24; }
.fb-chip.gold { background: #fff1d6; color: #8a5a00; }
.fb-chip.blue { background: #e6f0f7; color: #245b84; }
.fb-countdown { font-weight: 700; color: var(--fb-terra); }

.fb-cta { border-radius: 22px; padding: 28px 32px; background: #fff; border: 1px solid var(--fb-border);
          border-left: 5px solid var(--fb-terra); }
.fb-cta h3 { margin: 0 0 6px; color: var(--fb-forest); }
.fb-cta p { margin: 0; color: var(--fb-muted); }

.fb-empty { text-align: center; padding: 42px 20px; border: 1px dashed #d9cfbf; border-radius: 18px; background: #fff; }
.fb-empty .big { font-size: 2.4rem; }
.fb-empty b { display: block; margin: 6px 0 4px; color: var(--fb-forest); }
.fb-empty span { color: var(--fb-muted); font-size: 0.92rem; }

.fb-info { background: #fff; border: 1px solid var(--fb-border); border-radius: 18px; padding: 22px 24px; height: 100%; box-sizing: border-box; }
.fb-info h4 { margin: 0 0 8px; color: var(--fb-forest); }
.fb-info p, .fb-info li { color: var(--fb-muted); font-size: 0.94rem; line-height: 1.65; }
.fb-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.fb-table th { text-align: left; color: var(--fb-muted); font-weight: 600; border-bottom: 1px solid var(--fb-border); padding: 9px; }
.fb-table td { border-bottom: 1px solid var(--fb-border); padding: 9px; }

/* Timeline accordion with a vertical terracotta line (like the reference "Solutions" list) */
.fb-timeline { position: relative; padding-left: 34px; }
.fb-timeline::before { content: ""; position: absolute; left: 11px; top: 6px; bottom: 6px; width: 1.5px; background: var(--fb-terra); }
.fb-timeline details { position: relative; margin: 0 0 14px; }
.fb-timeline details::before { content: ""; position: absolute; left: -29px; top: 16px; width: 12px; height: 12px;
                               border-radius: 50%; background: var(--fb-bg); border: 2px solid var(--fb-terra); }
.fb-timeline details[open]::before { background: var(--fb-terra); }
.fb-timeline summary { list-style: none; cursor: pointer; display: inline-flex; align-items: center; gap: 12px;
                       background: var(--fb-forest); color: #fff; border-radius: 999px; padding: 10px 22px;
                       font-weight: 600; transition: background 0.2s; }
.fb-timeline summary::-webkit-details-marker { display: none; }
.fb-timeline summary::after { content: "+"; font-size: 1.2rem; line-height: 1; }
.fb-timeline details[open] summary::after { content: "–"; }
.fb-timeline summary:hover { background: #2f5240; }
.fb-timeline .content { padding: 12px 6px 4px 6px; color: var(--fb-muted); line-height: 1.7; max-width: 760px; }

/* Footer (a keyed Streamlit container, so it can hold page links) */
.st-key-fb-footer { margin-top: 72px; background: var(--fb-forest); padding: 44px 0 20px;
                    box-shadow: 0 0 0 100vmax var(--fb-forest); clip-path: inset(0 -100vmax -100vmax); }
.st-key-fb-footer h4 { color: #fff; margin: 0 0 10px; font-size: 0.95rem; }
.st-key-fb-footer p, .st-key-fb-footer span, .st-key-fb-footer li { color: rgba(255, 255, 255, 0.78); }
.st-key-fb-footer a, .st-key-fb-footer a * { color: rgba(255, 255, 255, 0.88) !important; }
.st-key-fb-footer a:hover, .st-key-fb-footer a:hover * { color: #ffc9a8 !important; background: transparent !important; }
.st-key-fb-footer [data-testid="stPageLink"] a { padding: 2px 0; }
.fb-footer-brand { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.fb-footer-brand b { color: #fff; font-size: 1.2rem; }
.fb-footer-bottom { border-top: 1px solid rgba(255, 255, 255, 0.14); margin-top: 18px; padding-top: 14px;
                    font-size: 0.82rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }

.fb-stat { background: var(--fb-card); border: 1px solid var(--fb-border); border-radius: 14px; padding: 14px 18px;
           min-height: 124px; box-sizing: border-box; }
.fb-stat .label { color: var(--fb-muted); font-size: 0.85rem; }
.fb-stat .value { font-size: 1.7rem; font-weight: 700; color: var(--fb-green-dark); line-height: 1.3; }
.fb-stat .sub { color: var(--fb-muted); font-size: 0.82rem; }

.fb-muted { color: var(--fb-muted); font-size: 0.88rem; }
.fb-banner { background: #fff8e1; border: 1px solid #ffe082; border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; }

.fb-badge, .fb-risk { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; white-space: nowrap; }
.fb-badge.listed { background: #e3f2fd; color: #1565c0; }
.fb-badge.matched { background: #fff8e1; color: #b26a00; }
.fb-badge.picked_up { background: #ede7f6; color: #5e35b1; }
.fb-badge.delivered { background: var(--fb-green-light); color: var(--fb-green-dark); }
.fb-badge.expired, .fb-badge.cancelled { background: #eceff1; color: #546e7a; }
.fb-badge.rejected { background: #ffebee; color: var(--fb-error); }
.fb-badge.verified { background: var(--fb-green-light); color: var(--fb-green-dark); }
.fb-badge.pending { background: #fff8e1; color: #b26a00; }
.fb-risk.low { background: var(--fb-green-light); color: var(--fb-green-dark); }
.fb-risk.medium { background: #fff8e1; color: #b26a00; }
.fb-risk.high { background: #fff3e0; color: #e65100; }
.fb-risk.critical { background: #ffebee; color: var(--fb-error); }

.fb-meter { height: 8px; background: #eceff1; border-radius: 999px; overflow: hidden; margin: 6px 0; }
.fb-meter > div { height: 100%; border-radius: 999px; }
.fb-meter .low { background: #43a047; } .fb-meter .medium { background: #fbc02d; }
.fb-meter .high { background: #fb8c00; } .fb-meter .critical { background: #e53935; }

.fb-ai { border: 1px dashed var(--fb-green); border-radius: 12px; padding: 12px 14px; background: #fbfdfa; }
.fb-ai-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 8px; }
.fb-ai-grid > div { display: flex; flex-direction: column; }
@media (max-width: 760px) { .fb-ai-grid { grid-template-columns: minmax(0, 1fr); } }
.fb-ai ul { margin: 6px 0 0; padding-left: 18px; }
.fb-warn { background: #fff8e1; border-radius: 8px; padding: 6px 12px; margin-top: 8px; font-size: 0.86rem; }

.fb-pipeline { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.fb-pipeline figure { margin: 0; text-align: center; }
.fb-pipeline img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 10px; border: 1px solid var(--fb-border); }
.fb-pipeline figcaption { font-size: 0.8rem; color: var(--fb-muted); margin-top: 4px; }

.fb-item { display: flex; gap: 12px; align-items: flex-start; }
.fb-item img { width: 76px; height: 76px; object-fit: cover; border-radius: 10px; flex-shrink: 0; }
.fb-item .body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.fb-item .title { font-weight: 600; }
"""


# Decorative terracotta arc, base64-encoded: raw "<svg>" tags inside <style> make
# Streamlit's HTML sanitiser drop the whole stylesheet.
ARC_SVG = (b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 64' preserveAspectRatio='none'>"
           b"<path d='M0 8 Q600 110 1200 8' fill='none' stroke='#d2553b' stroke-width='1.4'/></svg>")
CSS = CSS.replace("__ARC_URI__", "data:image/svg+xml;base64," + base64.b64encode(ARC_SVG).decode())


def inject_css() -> None:
    st.html(f"<style>{CSS}</style>")


def html(markup: str) -> None:
    st.html(markup)


# ---------- formatting ----------
STATUS_LABELS = {
    "listed": "Listed", "matched": "Matched", "picked_up": "Picked up", "delivered": "Delivered",
    "expired": "Expired", "cancelled": "Cancelled", "rejected": "Rejected (unsafe)",
}
RISK_LABELS = {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}


def fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST).strftime("%d %b, %I:%M %p")


def fmt_hours(hours: float) -> str:
    return f"{round(hours * 60)} min" if hours < 1 else f"{hours:.1f} h"


def time_left(deadline: datetime) -> str:
    hours = (deadline - datetime.now(timezone.utc)).total_seconds() / 3600
    return "overdue" if hours <= 0 else f"in {fmt_hours(hours)}"


# ---------- small components (return HTML strings) ----------
def status_badge(status: str) -> str:
    return f'<span class="fb-badge {escape(status)}">{STATUS_LABELS.get(status, escape(status))}</span>'


def risk_badge(freshness: dict | None) -> str:
    if not freshness:
        return ""
    level = freshness["risk_level"]
    return f'<span class="fb-risk {level}">{freshness["risk_score"]} · {RISK_LABELS[level]}</span>'


def meter(percent: float, level: str = "low") -> str:
    return f'<div class="fb-meter"><div class="{level}" style="width:{max(0, min(percent, 100)):.0f}%"></div></div>'


def stat(label: str, value: str, sub: str = "", extra: str = "") -> str:
    return (f'<div class="fb-stat"><div class="label">{escape(label)}</div>'
            f'<div class="value">{escape(value)}</div>{extra}'
            f'<div class="sub">{escape(sub)}</div></div>')


def ai_summary(result: dict) -> str:
    """Card with what the AI found + the spoilage risk (preview or stored listing)."""
    ai, freshness = result.get("ai"), result.get("freshness")
    parts = []
    if ai:
        others = ", ".join(escape(p["name"]) for p in ai["top_predictions"][1:])
        spoiled = round(ai["freshness"]["spoiled_probability"] * 100)
        q = ai["quantity_estimate"]
        parts.append(f"""
        <div class="fb-ai-grid">
          <div><span class="fb-muted">Detected food</span>
            <b>{escape(ai['dish']['name'])} <span class="fb-muted">{round(ai['dish']['confidence'] * 100)}%</span></b>
            <span class="fb-muted">{escape(ai['category']['name'])}{f' · or: {others}' if others else ''}</span></div>
          <div><span class="fb-muted">Looks</span>
            <b>{'⚠️ Spoiled' if spoiled >= 50 else '✅ Fresh'}</b>
            <span class="fb-muted">{spoiled}% spoilage signal</span></div>
          <div><span class="fb-muted">Quantity in photo</span>
            <b>{escape(q['label'])}</b>
            <span class="fb-muted">~{q['min_servings']}–{q['max_servings']} servings</span></div>
        </div>""")
    elif result.get("ai_error"):
        parts.append(f'<p class="fb-muted">⚠️ {escape(result["ai_error"])}</p>')
    if freshness:
        window = (f"Pick up by <b>{fmt_dt(freshness['pickup_deadline'])}</b> "
                  f"(within {fmt_hours(freshness['remaining_hours'])})"
                  if freshness["safe_to_donate"] else "<b>Not safe to donate</b>")
        reasons = "".join(f"<li>{escape(r)}</li>" for r in freshness["reasons"])
        parts.append(f"""
        <div><span class="fb-muted">Spoilage risk</span> {risk_badge(freshness)}</div>
        {meter(freshness['risk_score'], freshness['risk_level'])}
        <div class="fb-muted">{window}</div>
        <ul class="fb-muted">{reasons}</ul>""")
    for warning in result.get("warnings") or []:
        parts.append(f'<div class="fb-warn">⚠️ {escape(warning)}</div>')
    return f'<div class="fb-ai">{"".join(parts)}</div>'


def item(thumb_uri: str | None, title: str, lines: list[str]) -> str:
    """Thumbnail + title + pre-built HTML lines (callers escape user text)."""
    img = f'<img src="{thumb_uri}" alt="">' if thumb_uri else ""
    body = "".join(f"<div>{line}</div>" for line in lines)
    return (f'<div class="fb-item">{img}<div class="body">'
            f'<div class="title">{escape(title)}</div>{body}</div></div>')
