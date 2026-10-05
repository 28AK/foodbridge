"""Reusable Streamlit pieces: map picker, route map, photo thumbnails."""
import base64
from pathlib import Path

import cv2
import folium
import numpy as np
import streamlit as st
from bson import ObjectId
from gridfs.errors import NoFile
from streamlit_folium import st_folium

from app.config import BASE_DIR
from app.services.photo_store import read_photo
from app.ui.runtime import run

LUCKNOW = (26.8467, 80.9462)


def photo_bytes(url: str) -> bytes | None:
    """Load a stored photo: '/photos/<id>' (GridFS) or legacy '/uploads/...' (disk)."""
    try:
        if url.startswith("/photos/"):
            return run(read_photo(ObjectId(url.rsplit("/", 1)[1])))
        path = (BASE_DIR / url.lstrip("/")).resolve()
        if path.is_relative_to(BASE_DIR / "uploads") and path.exists():
            return Path(path).read_bytes()
    except (NoFile, ValueError, OSError):
        pass
    return None


@st.cache_data(max_entries=500, show_spinner=False)
def thumb_uri(url: str, size: int = 160) -> str | None:
    """Small square JPEG as a data: URI, for use inside HTML cards."""
    data = photo_bytes(url)
    if data is None:
        return None
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    side = min(h, w)
    top, left = (h - side) // 2, (w - side) // 2
    img = cv2.resize(img[top:top + side, left:left + side], (size, size), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode() if ok else None


def location_picker(key: str, height: int = 320) -> tuple[float, float] | None:
    """Click on the map to choose a location. Returns (lat, lng) or None."""
    state_key = f"{key}__pos"
    pos = st.session_state.get(state_key)
    m = folium.Map(location=pos or LUCKNOW, zoom_start=15 if pos else 12, control_scale=True)
    if pos:
        folium.Marker(pos, tooltip="Selected location",
                      icon=folium.Icon(color="green", icon="map-marker", prefix="fa")).add_to(m)
    out = st_folium(m, key=key, height=height, use_container_width=True,
                    returned_objects=["last_clicked"])
    click = (out or {}).get("last_clicked")
    if click:
        new = (round(click["lat"], 6), round(click["lng"], 6))
        if new != pos:
            st.session_state[state_key] = new
            st.rerun()
    return pos


def pin(label: str, color: str) -> folium.DivIcon:
    return folium.DivIcon(
        icon_size=(28, 28), icon_anchor=(14, 14),
        html=(f'<div style="width:28px;height:28px;border-radius:50%;background:{color};color:#fff;'
              f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;'
              f'border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35)">{label}</div>'),
    )


def show_map(m: folium.Map, key: str, height: int = 420) -> None:
    """Display-only map (no reruns on interaction)."""
    st_folium(m, key=key, height=height, use_container_width=True, returned_objects=[])
