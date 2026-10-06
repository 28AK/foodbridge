"""Module 4 – alerts to NGOs and donors.

Alerts are recorded in the `notifications` collection and shown on the admin
dashboard. SMS delivery (Twilio) is not connected yet: plug a sender into
`send_sms` to deliver them. Alert failures never interrupt the donation flow.
"""
import logging
import re
from datetime import datetime, timedelta, timezone

from app.db import NGOS, NOTIFICATIONS, get_db

log = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))


def fmt_dt(value: datetime) -> str:
    return value.astimezone(IST).strftime("%d %b %I:%M %p")


def normalize_phone(phone: str) -> str | None:
    """'+91 98765 43210' / '9876543210' / '09876543210' -> '+919876543210' (E.164)."""
    phone = (phone or "").strip()
    digits = re.sub(r"\D", "", phone)
    if phone.startswith("+") and 10 <= len(digits) <= 15:
        return "+" + digits
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    return None


async def send_sms(phone: str, body: str, kind: str, listing_id=None) -> dict:
    to = normalize_phone(phone)
    record = {"to": to or phone, "body": body, "kind": kind, "listing_id": listing_id,
              "created_at": datetime.now(timezone.utc), "sid": None, "error": None}
    if to is None:
        record["status"] = "failed"
        record["error"] = "invalid phone number"
    else:
        record["status"] = "logged"  # no SMS provider connected yet
    await get_db()[NOTIFICATIONS].insert_one(record)
    return record


async def _safely(coro) -> None:
    try:
        await coro
    except Exception:
        log.exception("Notification failed")


# ---------- events ----------
async def on_matched(listing: dict, match: dict) -> None:
    ngo = await get_db()[NGOS].find_one({"_id": match["ngo_id"]}, {"phone": 1})
    if not ngo:
        return
    body = (f"FoodBridge: New donation for you - {listing['quantity_servings']} servings of "
            f"{listing['food_name']}, {match['distance_km']} km away. Pick up by "
            f"{fmt_dt(listing['pickup_deadline'])}. Log in to accept.")
    await _safely(send_sms(ngo["phone"], body, "ngo_matched", listing["_id"]))


async def on_accepted(listing: dict, ngo: dict) -> None:
    body = (f"FoodBridge: {ngo['name']} accepted your {listing['food_name']} and will pick it up by "
            f"{fmt_dt(listing['pickup_deadline'])}. Their phone: {ngo['phone']}.")
    await _safely(send_sms(listing["donor_phone"], body, "donor_accepted", listing["_id"]))


async def on_delivered(listing: dict, ngo: dict) -> None:
    body = (f"FoodBridge: Your {listing['food_name']} was delivered to {ngo['name']}. "
            f"{listing['quantity_servings']} meals served - thank you!")
    await _safely(send_sms(listing["donor_phone"], body, "donor_delivered", listing["_id"]))


async def recent(limit: int = 50) -> list[dict]:
    cursor = get_db()[NOTIFICATIONS].find().sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]
