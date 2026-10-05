"""NGO-side operations, shared by the FastAPI routes and the Streamlit UI."""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.db import LISTINGS, NGOS, get_db
from app.services.geo import lat_lng
from app.services.lifecycle import transition
from app.services.matching import release_and_rematch, todays_load
from app.services.routing import plan_route


async def ngo_for(user: dict) -> dict:
    ngo = await get_db()[NGOS].find_one({"_id": user.get("ngo_id")})
    if ngo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organisation profile not found")
    return ngo


async def profile(ngo: dict) -> dict:
    now = datetime.now(timezone.utc)
    received = (await todays_load(get_db(), [ngo["_id"]], now)).get(ngo["_id"], 0)
    return {
        **ngo,
        "today": {
            "received_servings": received,
            "free_capacity": max(ngo["capacity_meals"] - received, 0),
            "unmet_demand": max(ngo["current_demand"] - received, 0),
        },
    }


async def update(ngo: dict, changes: dict) -> dict:
    if changes:
        await get_db()[NGOS].update_one({"_id": ngo["_id"]}, {"$set": changes})
        ngo.update(changes)
    return await profile(ngo)


async def matches(ngo: dict, scope: str = "active") -> list[dict]:
    statuses = ["matched", "picked_up"] if scope == "active" else ["delivered"]
    cursor = (get_db()[LISTINGS]
              .find({"matched_ngo_id": ngo["_id"], "status": {"$in": statuses}})
              .sort("pickup_deadline", 1)
              .limit(100))
    return [doc async for doc in cursor]


async def _my_listing(ngo: dict, listing_id: ObjectId) -> dict:
    listing = await get_db()[LISTINGS].find_one({"_id": listing_id, "matched_ngo_id": ngo["_id"]})
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")
    return listing


async def accept(ngo: dict, listing_id: ObjectId) -> dict:
    listing = await _my_listing(ngo, listing_id)
    return await transition(
        get_db(),
        {"_id": listing["_id"], "status": "matched", "matched_ngo_id": ngo["_id"],
         "match.accepted_at": None},
        "matched", ngo["user_id"],
        extra_set={"match.accepted_at": datetime.now(timezone.utc)},
        error="This match can no longer be accepted",
    )


async def decline(ngo: dict, listing_id: ObjectId) -> bool:
    listing = await _my_listing(ngo, listing_id)
    if listing["status"] != "matched":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only unpicked matches can be declined")
    await release_and_rematch(get_db(), listing["_id"], ngo["_id"], "declined by NGO")
    return True


async def picked_up(ngo: dict, listing_id: ObjectId) -> dict:
    listing = await _my_listing(ngo, listing_id)
    return await transition(
        get_db(),
        {"_id": listing["_id"], "status": "matched", "matched_ngo_id": ngo["_id"],
         "match.accepted_at": {"$ne": None}},
        "picked_up", ngo["user_id"],
        error="Accept the match before marking it picked up",
    )


async def delivered(ngo: dict, listing_id: ObjectId) -> dict:
    listing = await _my_listing(ngo, listing_id)
    return await transition(
        get_db(),
        {"_id": listing["_id"], "status": "picked_up", "matched_ngo_id": ngo["_id"]},
        "delivered", ngo["user_id"],
        error="Only picked-up food can be marked delivered",
    )


async def route(ngo: dict) -> dict:
    """Suggested pickup order for accepted, not-yet-collected donations."""
    cursor = get_db()[LISTINGS].find({
        "matched_ngo_id": ngo["_id"], "status": "matched", "match.accepted_at": {"$ne": None},
    })
    stops = []
    async for listing in cursor:
        lat, lng = lat_lng(listing["location"])
        stops.append({
            "id": listing["_id"], "lat": lat, "lng": lng, "deadline": listing["pickup_deadline"],
            "food_name": listing["food_name"], "quantity_servings": listing["quantity_servings"],
            "address": listing["address"], "donor_name": listing["donor_name"],
            "donor_phone": listing["donor_phone"],
        })
    origin = lat_lng(ngo["location"])
    plan = plan_route(origin, stops, datetime.now(timezone.utc))
    return {"origin": {"lat": origin[0], "lng": origin[1]}, **plan}


async def list_all() -> list[dict]:
    """Admin: every organisation, pending ones first."""
    cursor = get_db()[NGOS].find().sort([("verified", 1), ("name", 1)])
    return [doc async for doc in cursor]


async def set_verified(ngo_id: ObjectId, verified: bool) -> None:
    result = await get_db()[NGOS].update_one({"_id": ngo_id}, {"$set": {"verified": verified}})
    if result.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NGO not found")
