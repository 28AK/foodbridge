"""Module 3 – Donor -> recipient matching.

For a listing we find verified NGOs within MAX_RADIUS_KM (MongoDB $geoNear),
drop the ones that can't take it (veg-only, full for today, too far to reach
before the pickup deadline, already declined it), and rank the rest by a
Match Priority Score (0-100):

    distance  40%  closer is better
    capacity  25%  free capacity today vs. servings offered
    demand    25%  unmet demand today vs. servings offered
    time      10%  how comfortably the NGO can arrive before the deadline
"""
from datetime import datetime, timedelta, timezone

from pymongo.asynchronous.database import AsyncDatabase

from app.db import LISTINGS, NGOS
from app.services.geo import HANDLING_MINUTES, travel_minutes

MAX_RADIUS_KM = 15
WEIGHTS = {"distance": 0.40, "capacity": 0.25, "demand": 0.25, "time": 0.10}
NON_VEG_AI_CONFIDENCE = 0.6
ACTIVE_STATUSES = ("matched", "picked_up", "delivered")  # count towards today's load
IST = timezone(timedelta(hours=5, minutes=30))


def ist_day_start(now: datetime) -> datetime:
    local = now.astimezone(IST)
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def is_non_veg(listing: dict) -> bool:
    """Declared non-veg, or the AI is fairly sure it is (protects veg-only NGOs)."""
    if listing["food_category"] == "non_veg":
        return True
    ai = listing.get("ai")
    return bool(ai and ai["category"]["non_veg"]
                and ai["category"]["confidence"] >= NON_VEG_AI_CONFIDENCE)


def score_candidate(distance_km: float, free_capacity: int, unmet_demand: int,
                    servings: int, hours_left: float) -> dict | None:
    """Score one NGO for one listing; None if it can't take the listing."""
    if free_capacity <= 0:
        return None
    eta_min = travel_minutes(distance_km) + HANDLING_MINUTES
    if eta_min / 60 >= hours_left:
        return None
    breakdown = {
        "distance": max(0.0, 1 - distance_km / MAX_RADIUS_KM),
        "capacity": min(free_capacity / servings, 1.0),
        "demand": min(unmet_demand / servings, 1.0),
        "time": 1 - (eta_min / 60) / hours_left,
    }
    score = 100 * sum(WEIGHTS[k] * v for k, v in breakdown.items())
    return {
        "score": round(score, 1),
        "eta_minutes": round(eta_min),
        "breakdown": {k: round(v, 3) for k, v in breakdown.items()},
    }


async def todays_load(db: AsyncDatabase, ngo_ids: list, now: datetime) -> dict:
    """Servings already matched to each NGO today."""
    cursor = await db[LISTINGS].aggregate([
        {"$match": {
            "matched_ngo_id": {"$in": ngo_ids},
            "status": {"$in": list(ACTIVE_STATUSES)},
            "match.matched_at": {"$gte": ist_day_start(now)},
        }},
        {"$group": {"_id": "$matched_ngo_id", "servings": {"$sum": "$quantity_servings"}}},
    ])
    return {row["_id"]: row["servings"] async for row in cursor}


async def rank_candidates(db: AsyncDatabase, listing: dict, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    hours_left = (listing["pickup_deadline"] - now).total_seconds() / 3600
    if hours_left <= 0:
        return []

    query = {"verified": True, "_id": {"$nin": listing.get("declined_ngo_ids", [])}}
    if is_non_veg(listing):
        query["veg_only"] = False

    cursor = await db[NGOS].aggregate([{
        "$geoNear": {
            "near": listing["location"],
            "distanceField": "distance_m",
            "maxDistance": MAX_RADIUS_KM * 1000,
            "spherical": True,
            "query": query,
        },
    }])
    ngos = [ngo async for ngo in cursor]
    load = await todays_load(db, [n["_id"] for n in ngos], now)

    candidates = []
    for ngo in ngos:
        received = load.get(ngo["_id"], 0)
        distance_km = ngo["distance_m"] / 1000
        scored = score_candidate(
            distance_km=distance_km,
            free_capacity=ngo["capacity_meals"] - received,
            unmet_demand=max(ngo["current_demand"] - received, 0),
            servings=listing["quantity_servings"],
            hours_left=hours_left,
        )
        if scored:
            candidates.append({
                "ngo_id": ngo["_id"],
                "ngo_name": ngo["name"],
                "ngo_type": ngo["type"],
                "distance_km": round(distance_km, 2),
                **scored,
            })
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates


async def match_listing(db: AsyncDatabase, listing: dict) -> dict | None:
    """Assign the best NGO to a 'listed' listing. Returns the match, or None."""
    now = datetime.now(timezone.utc)
    candidates = await rank_candidates(db, listing, now)
    if not candidates:
        await db[LISTINGS].update_one(
            {"_id": listing["_id"], "status": "listed"},
            {"$set": {"last_match_attempt": now}},
        )
        return None

    best = candidates[0]
    match = {**best, "matched_at": now, "accepted_at": None}
    result = await db[LISTINGS].update_one(
        # Conditional update: only if nobody changed the listing meanwhile
        {"_id": listing["_id"], "status": "listed"},
        {
            "$set": {
                "status": "matched",
                "matched_ngo_id": best["ngo_id"],
                "match": match,
                "match_candidates": candidates[:3],
                "last_match_attempt": now,
                "updated_at": now,
            },
            "$push": {"status_history": {"status": "matched", "at": now, "by": "system",
                                         "ngo_id": best["ngo_id"]}},
        },
    )
    return match if result.modified_count else None


async def release_match(db: AsyncDatabase, listing_id, ngo_id, reason: str) -> None:
    """Undo a match (declined / not accepted in time) so the listing can be re-matched."""
    now = datetime.now(timezone.utc)
    await db[LISTINGS].update_one(
        {"_id": listing_id, "status": "matched", "matched_ngo_id": ngo_id},
        {
            "$set": {"status": "listed", "matched_ngo_id": None, "match": None, "updated_at": now},
            "$addToSet": {"declined_ngo_ids": ngo_id},
            "$push": {"status_history": {"status": "listed", "at": now, "by": "system",
                                         "reason": reason, "ngo_id": ngo_id}},
        },
    )


async def release_and_rematch(db: AsyncDatabase, listing_id, ngo_id, reason: str) -> dict | None:
    """Release a match and immediately offer the listing to the next-best NGO."""
    await release_match(db, listing_id, ngo_id, reason)
    listing = await db[LISTINGS].find_one({"_id": listing_id})
    if listing and listing["status"] == "listed":
        return await match_listing(db, listing)
    return None
