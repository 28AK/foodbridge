"""Donor-side listing operations, shared by the FastAPI routes and the Streamlit UI.

Errors are raised as fastapi.HTTPException (status + readable `detail`).
"""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.db import LISTINGS, get_db
from app.services.lifecycle import transition
from app.services.matching import match_listing
from app.services.photo_store import save_photo
from app.services.pipeline import analyze_photo, normalize_prepared_at
from app.services.preprocessing import encode_images


async def preview(photo: bytes, prepared_at: datetime, quantity_servings: int | None = None,
                  food_category: str | None = None) -> dict:
    """AI result for a photo without creating a listing."""
    result = await analyze_photo(photo, normalize_prepared_at(prepared_at),
                                 quantity_servings, food_category)
    return {
        "preprocessing": result.image.report,
        "ai": result.ai,
        "ai_error": result.ai_error,
        "freshness": result.freshness,
        "warnings": result.warnings,
    }


async def create(user: dict, *, photo: bytes, food_name: str, food_category: str,
                 quantity_servings: int, prepared_at: datetime, address: str,
                 lat: float, lng: float, description: str = "", pickup_notes: str = "") -> dict:
    prepared_utc = normalize_prepared_at(prepared_at)
    result = await analyze_photo(photo, prepared_utc, quantity_servings, food_category)

    listing_id = ObjectId()
    encoded = await run_in_threadpool(encode_images, result.image)
    images = {
        stage: await save_photo(jpeg, f"{listing_id}_{stage}.jpg",
                                {"listing_id": listing_id, "stage": stage})
        for stage, jpeg in encoded.items()
    }

    freshness = result.freshness
    safe = freshness["safe_to_donate"]
    status_ = "listed" if safe else "rejected"
    now = datetime.now(timezone.utc)
    listing = {
        "_id": listing_id,
        "donor_id": user["_id"],
        "donor_name": user["name"],
        "donor_phone": user.get("phone", ""),
        "food_name": food_name.strip(),
        "food_category": food_category,
        "description": description.strip(),
        "quantity_servings": quantity_servings,
        "prepared_at": prepared_utc,
        "address": address.strip(),
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "pickup_notes": pickup_notes.strip(),
        "images": images,
        "preprocessing": result.image.report,
        "ai": result.ai,
        "ai_error": result.ai_error,
        "freshness": freshness,
        "risk_score": freshness["risk_score"],
        "pickup_deadline": freshness["pickup_deadline"],
        "warnings": result.warnings,
        "rejection_reason": None if safe else "; ".join(freshness["reasons"]),
        "matched_ngo_id": None,  # filled by the matching engine (Module 3)
        "status": status_,
        "status_history": [{"status": status_, "at": now, "by": user["_id"]}],
        "created_at": now,
        "updated_at": now,
    }
    db = get_db()
    await db[LISTINGS].insert_one(listing)
    if safe:
        # Module 3: immediately look for the best nearby NGO
        await match_listing(db, listing)
        listing = await db[LISTINGS].find_one({"_id": listing_id})
    return listing


async def mine(user: dict, limit: int = 100) -> list[dict]:
    cursor = get_db()[LISTINGS].find({"donor_id": user["_id"]}).sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]


async def cancel(user: dict, listing_id: ObjectId) -> dict:
    return await transition(
        get_db(),
        {"_id": listing_id, "donor_id": user["_id"], "status": {"$in": ["listed", "matched"]}},
        "cancelled", user["_id"],
        error="Only listings that haven't been picked up can be cancelled",
    )


async def get_for(user: dict, listing_id: ObjectId) -> dict:
    listing = await get_db()[LISTINGS].find_one({"_id": listing_id})
    if listing is None or (user["role"] == "donor" and listing["donor_id"] != user["_id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return listing
