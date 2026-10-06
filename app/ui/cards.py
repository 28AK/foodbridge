"""HTML cards for the public pages (food and organisations)."""
from html import escape

from app.ui import style
from app.ui.components import thumb_uri

ORG_TYPES = {"ngo": ("NGO", "🤝"), "shelter": ("Shelter", "🏠"), "community_kitchen": ("Community kitchen", "🍲")}


def food_card(item: dict) -> str:
    veg = item["food_category"] == "veg"
    chip = '<span class="fb-chip veg">🟢 Veg</span>' if veg else '<span class="fb-chip nonveg">🔴 Non-veg</span>'
    category = ((item.get("ai") or {}).get("category") or {}).get("name")
    category_chip = f'<span class="fb-chip">{escape(category)}</span>' if category else ""
    status = ('<span class="fb-chip blue">NGO assigned</span>' if item["status"] == "matched"
              else '<span class="fb-chip gold">Awaiting NGO</span>')
    img = thumb_uri(item["images"]["processed"], 480) or ""
    return f"""
    <div class="fb-card">
      <img src="{img}" alt="{escape(item['food_name'])}">
      <div class="body">
        <div class="row">{chip}{category_chip}{style.risk_badge(item.get('freshness'))}</div>
        <div class="title">{escape(item['food_name'])}</div>
        <div class="meta">🍽️ {item['quantity_servings']} servings · 📍 Near {escape(item['area'])}</div>
        <div class="meta">Pick up by {style.fmt_dt(item['pickup_deadline'])} ·
          <span class="fb-countdown">{style.time_left(item['pickup_deadline'])}</span></div>
        <div class="row">{status}</div>
      </div>
    </div>"""


def ngo_card(ngo: dict) -> str:
    label, icon = ORG_TYPES.get(ngo["type"], (ngo["type"], "🤝"))
    veg = '<span class="fb-chip veg">Veg only</span>' if ngo.get("veg_only") else ""
    received = (f'<span class="fb-chip gold">{ngo["meals_received"]} meals received</span>'
                if ngo.get("meals_received") else "")
    area = ngo.get("area") or "Lucknow"
    return f"""
    <div class="fb-card">
      <div class="body">
        <div class="head"><div class="fb-icon-tile">{icon}</div>
          <div><div class="title">{escape(ngo['name'])}</div>
          <div class="meta">{escape(label)} · 📍 {escape(area)}</div></div></div>
        <div class="meta">{escape(ngo.get('address', ''))}</div>
        <div class="row"><span class="fb-chip">Serves up to {ngo['capacity_meals']} meals/day</span>{veg}{received}</div>
      </div>
    </div>"""


def grid(cards: list[str], columns: int = 3) -> str:
    return f'<div class="fb-grid{" four" if columns == 4 else ""}">{"".join(cards)}</div>'
