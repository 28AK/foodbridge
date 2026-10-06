"""Read-only data for the public pages (no login), plus the contact form.

Privacy: public views never include a donor's address or phone number. Food
locations are reduced to the nearest known area name and a ~1 km rounded point;
exact details are only shown to the NGO that accepts the pickup.
"""
from datetime import datetime, timedelta, timezone

from app.db import CONTACT_MESSAGES, LISTINGS, NGOS, USERS, get_db
from app.services.geo import haversine_km, lat_lng

KG_PER_SERVING = 0.4      # rough average weight of one meal, used for "waste avoided"
AREA_RADIUS_KM = 6        # beyond this from any known area we just say "Lucknow"
IST_OFFSET = "+05:30"

PUBLIC_LISTING_FIELDS = {
    "food_name": 1, "food_category": 1, "quantity_servings": 1, "prepared_at": 1,
    "pickup_deadline": 1, "freshness.risk_score": 1, "freshness.risk_level": 1,
    "ai.dish.name": 1, "ai.category": 1, "images.processed": 1, "location": 1,
    "status": 1, "created_at": 1, "match.ngo_name": 1,
}


async def _areas() -> list[tuple[str, float, float]]:
    cursor = get_db()[NGOS].find({"area": {"$nin": ["", None]}}, {"area": 1, "location": 1})
    return [(n["area"], *lat_lng(n["location"])) async for n in cursor]


def _nearest_area(lat: float, lng: float, areas) -> str:
    best = min(areas, key=lambda a: haversine_km(lat, lng, a[1], a[2]), default=None)
    if best and haversine_km(lat, lng, best[1], best[2]) <= AREA_RADIUS_KM:
        return best[0]
    return "Lucknow"


async def available_food() -> list[dict]:
    """Food currently waiting for or on its way to an NGO, soonest deadline first."""
    now = datetime.now(timezone.utc)
    cursor = (get_db()[LISTINGS]
              .find({"status": {"$in": ["listed", "matched"]}, "pickup_deadline": {"$gt": now}},
                    PUBLIC_LISTING_FIELDS)
              .sort("pickup_deadline", 1)
              .limit(200))
    areas = await _areas()
    items = []
    async for doc in cursor:
        lat, lng = lat_lng(doc.pop("location"))
        doc["area"] = _nearest_area(lat, lng, areas)
        doc["approx_point"] = (round(lat, 2), round(lng, 2))  # ~1 km precision
        items.append(doc)
    return items


async def public_ngos() -> list[dict]:
    """Verified organisations with how many meals they've received through FoodBridge."""
    db = get_db()
    cursor = await db[LISTINGS].aggregate([
        {"$match": {"status": "delivered"}},
        {"$group": {"_id": "$matched_ngo_id", "meals": {"$sum": "$quantity_servings"}}},
    ])
    received = {row["_id"]: row["meals"] async for row in cursor}
    ngos = db[NGOS].find({"verified": True},
                         {"name": 1, "type": 1, "area": 1, "address": 1, "location": 1,
                          "capacity_meals": 1, "veg_only": 1}).sort("name", 1)
    return [{**n, "meals_received": received.get(n["_id"], 0)} async for n in ngos]


async def impact() -> dict:
    db = get_db()
    cursor = await db[LISTINGS].aggregate([
        {"$group": {"_id": "$status", "n": {"$sum": 1}, "servings": {"$sum": "$quantity_servings"}}},
    ])
    by_status = {row["_id"]: row async for row in cursor}
    delivered = by_status.get("delivered", {})
    meals = delivered.get("servings", 0)
    return {
        "meals_delivered": meals,
        "kg_saved": round(meals * KG_PER_SERVING),
        "deliveries": delivered.get("n", 0),
        "donations": sum(row["n"] for row in by_status.values()),
        "active_now": sum(by_status.get(s, {}).get("n", 0) for s in ("listed", "matched", "picked_up")),
        "ngos": await db[NGOS].count_documents({"verified": True}),
        "donors": await db[USERS].count_documents({"role": "donor"}),
        "by_status": {k: v["n"] for k, v in by_status.items() if k},
    }


async def journey_stats() -> dict:
    """Live numbers for each step of the 'journey of a donation' flowchart."""
    listings = get_db()[LISTINGS]
    stats = await impact()
    by_status = stats["by_status"]
    return {
        "donations": stats["donations"],
        "enhanced": await listings.count_documents({"preprocessing.enhanced": True}),
        "analysed": await listings.count_documents({"ai": {"$ne": None}}),
        "rejected": by_status.get("rejected", 0),
        "waiting": by_status.get("listed", 0),
        "matched": by_status.get("matched", 0),
        "in_transit": by_status.get("picked_up", 0),
        "meals_delivered": stats["meals_delivered"],
    }


async def delivered_per_day(days: int = 30) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    cursor = await get_db()[LISTINGS].aggregate([
        {"$match": {"status": "delivered", "updated_at": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at", "timezone": IST_OFFSET}},
            "meals": {"$sum": "$quantity_servings"}, "deliveries": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ])
    return [{"date": row["_id"], "meals": row["meals"], "deliveries": row["deliveries"]} async for row in cursor]


async def delivered_by_category() -> list[dict]:
    cursor = await get_db()[LISTINGS].aggregate([
        {"$match": {"status": "delivered"}},
        {"$group": {"_id": {"$ifNull": ["$ai.category.name", "Other"]},
                    "meals": {"$sum": "$quantity_servings"}}},
        {"$sort": {"meals": -1}},
    ])
    return [{"category": row["_id"], "meals": row["meals"]} async for row in cursor]


async def delivered_by_area() -> list[dict]:
    cursor = await get_db()[LISTINGS].aggregate([
        {"$match": {"status": "delivered"}},
        {"$lookup": {"from": NGOS, "localField": "matched_ngo_id", "foreignField": "_id", "as": "ngo"}},
        {"$unwind": "$ngo"},
        {"$group": {"_id": {"$cond": [{"$in": ["$ngo.area", ["", None]]}, "Other", "$ngo.area"]},
                    "meals": {"$sum": "$quantity_servings"}}},
        {"$sort": {"meals": -1}},
    ])
    return [{"area": row["_id"], "meals": row["meals"]} async for row in cursor]


# ---------- contact form ----------
async def save_contact_message(name: str, email: str, subject: str, message: str) -> None:
    await get_db()[CONTACT_MESSAGES].insert_one({
        "name": name.strip(), "email": email.strip().lower(), "subject": subject.strip(),
        "message": message.strip(), "status": "new", "created_at": datetime.now(timezone.utc),
    })


async def contact_messages(limit: int = 200) -> list[dict]:
    cursor = get_db()[CONTACT_MESSAGES].find().sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]


async def mark_message(message_id, status: str) -> None:
    await get_db()[CONTACT_MESSAGES].update_one({"_id": message_id}, {"$set": {"status": status}})
