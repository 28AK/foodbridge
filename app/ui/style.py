"""Custom HTML/CSS for the Streamlit UI: theme polish, cards, badges, meters."""
from datetime import datetime, timedelta, timezone
from html import escape

import streamlit as st

IST = timezone(timedelta(hours=5, minutes=30))

# The Inter font is set in .streamlit/config.toml. Don't override font-family on Streamlit's
# own elements here: its icons use the Material Symbols font, and replacing it makes icon
# names ("arrow_right", "visibility", "upload") show up as overlapping text.
CSS = """
:root {
  --fb-green: #2e7d32; --fb-green-dark: #1b5e20; --fb-green-light: #e8f5e9;
  --fb-bg: #f8fbf6; --fb-card: #ffffff; --fb-border: #e1e9dc;
  --fb-text: #1f2a1f; --fb-muted: #5f6b5f; --fb-error: #c62828;
}
.stApp { background: linear-gradient(180deg, #f3f9ef 0%, var(--fb-bg) 320px); }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1280px; }
h1, h2, h3 { color: var(--fb-green-dark); letter-spacing: -0.01em; }

/* Bordered Streamlit containers become white cards */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
  background: var(--fb-card); border-radius: 14px; border-color: var(--fb-border) !important;
  box-shadow: 0 1px 3px rgba(31, 42, 31, 0.05);
}
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--fb-border); }
.stButton > button, .stLinkButton > a, .stFormSubmitButton > button { border-radius: 10px; font-weight: 600; }
/* Never shrink a button below its label (otherwise "Mark picked up" gets cut to "Mark picke…") */
.stButton > button, .stLinkButton > a { min-width: max-content; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }

/* ---------- Components ---------- */
.fb-hero { padding: 8px 0 18px; }
.fb-hero h1 { font-size: 2.4rem; margin: 0 0 8px; color: var(--fb-green-dark); }
.fb-hero p { font-size: 1.08rem; color: var(--fb-muted); max-width: 620px; margin: 0; }
.fb-features { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 22px; }
.fb-feature { background: var(--fb-card); border: 1px solid var(--fb-border); border-radius: 14px; padding: 14px 16px; }
.fb-feature b { display: block; margin-bottom: 4px; }
.fb-feature span { color: var(--fb-muted); font-size: 0.9rem; }
@media (max-width: 760px) { .fb-features { grid-template-columns: minmax(0, 1fr); } }

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
