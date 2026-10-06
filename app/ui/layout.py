"""Page building blocks shared by every page: headings, counters, empty states, footer."""
import base64
from datetime import datetime
from functools import lru_cache
from html import escape

import streamlit as st

from app.config import BASE_DIR
from app.ui import style

CONTACT_EMAIL = "foodbridge@gmail.com"

# Filled in by streamlit_app.py so any page can link to any other page
PAGES: dict[str, "st.Page"] = {}


@lru_cache
def logo_mark_uri() -> str:
    data = (BASE_DIR / "assets" / "logo-mark.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode()


@lru_cache
def illustration(name: str) -> str:
    """Line-art illustration from assets/illustrations as a data: URI."""
    data = (BASE_DIR / "assets" / "illustrations" / f"{name}.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode()


def two_tone(text: str) -> str:
    """Escape text and turn **words** into the bright-green accent (two-tone headings)."""
    parts = escape(text).split("**")
    return "".join(f'<span class="accent">{p}</span>' if i % 2 else p for i, p in enumerate(parts))


def page_head(kicker: str, title: str, subtitle: str = "", art: str | None = None) -> None:
    img = f'<img src="{illustration(art)}" alt="">' if art else ""
    style.html(f'<div class="fb-page-head{"" if art else " no-art"}"><div><div class="kicker">{escape(kicker)}</div>'
               f'<h1>{two_tone(title)}</h1><p>{escape(subtitle)}</p></div>{img}</div>')


def section(kicker: str, title: str, subtitle: str = "") -> None:
    style.html(f'<div class="fb-section"><div class="kicker">{escape(kicker)}</div>'
               f'<h2>{two_tone(title)}</h2><p>{escape(subtitle)}</p></div>')


def arc() -> None:
    style.html('<div class="fb-arc"></div>')


def counters_html(items: list[tuple[str, str]]) -> str:
    cells = "".join(f'<div class="fb-counter"><div class="num">{escape(value)}</div>'
                    f'<div class="lbl">{escape(label)}</div></div>' for value, label in items)
    return f'<div class="fb-counters">{cells}</div>'


COUNT_UP_JS = """<script>
document.querySelectorAll('.fb-counter .num:not([data-done])').forEach(el => {
  el.dataset.done = 1;
  const m = el.textContent.match(/^([\\d,]+)(.*)$/); if (!m) return;
  const target = +m[1].replace(/,/g, ''), suffix = m[2], t0 = performance.now();
  const tick = t => { const k = Math.min((t - t0) / 1200, 1), v = Math.round(target * (1 - Math.pow(1 - k, 3)));
    el.textContent = v.toLocaleString('en-IN') + suffix; if (k < 1) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
});</script>"""


def count_up() -> None:
    """Animate any counters on the page from 0 to their value."""
    st.html(COUNT_UP_JS, unsafe_allow_javascript=True)


def counters(items: list[tuple[str, str]]) -> None:
    style.html(counters_html(items))
    count_up()


def band(kicker: str, title: str, subtitle: str = "", inner_html: str = "") -> None:
    """Full-width forest-green band section."""
    style.html(f'<div class="fb-band"><div class="kicker">{escape(kicker)}</div><h2>{two_tone(title)}</h2>'
               f'<p>{escape(subtitle)}</p>{inner_html}</div>')
    if "fb-counter" in inner_html:
        count_up()


def empty(icon: str, title: str, text: str) -> None:
    style.html(f'<div class="fb-empty"><div class="big">{icon}</div><b>{escape(title)}</b>'
               f'<span>{escape(text)}</span></div>')


def link(name: str, label: str | None = None, icon: str | None = None, **kwargs) -> None:
    """st.page_link to a registered page (no-op if that page isn't available)."""
    page = PAGES.get(name)
    if page is not None:
        st.page_link(page, label=label or page.title, icon=icon, **kwargs)


def go(name: str) -> None:
    """Switch to a registered page."""
    st.switch_page(PAGES[name])


def footer() -> None:
    with st.container(key="fb-footer"):
        brand, explore, account, contact = st.columns([1.6, 1, 1, 1.2], gap="large")
        with brand:
            style.html(f'<div class="fb-footer-brand"><img src="{logo_mark_uri()}" width="36" height="36" alt="">'
                       '<b>FoodBridge</b></div>'
                       '<p>Connecting surplus food with people who need it — checked by AI, '
                       'matched to the nearest NGO before it spoils.</p>')
        with explore:
            style.html("<h4>Explore</h4>")
            for name in ("food", "ngos", "impact", "how"):
                link(name)
        with account:
            style.html("<h4>Get involved</h4>")
            if st.session_state.get("user_id"):
                link("dashboard", "My dashboard")
            else:
                link("signin", "Donate food")
                link("signin", "Register your NGO")
            link("about")
        with contact:
            style.html(f'<h4>Contact</h4><p>✉️ <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>'
                       '<p>Lucknow, Uttar Pradesh, India</p>')
            link("contact", "Send us a message")
        style.html(f'<div class="fb-footer-bottom"><span>© {datetime.now().year} FoodBridge · '
                   'Final-year B.Tech project, BBD University, Lucknow</span>'
                   '<span>Food is checked by AI as guidance — always follow food-safety practice.</span></div>')
