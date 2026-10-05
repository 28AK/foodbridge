"""Listing status transitions (Listed -> Matched -> Picked Up -> Delivered)."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.db import LISTINGS


async def transition(db: AsyncDatabase, query: dict, to_status: str, by,
                     extra_set: dict | None = None, error: str = "This action isn't allowed now") -> dict:
    """Atomically move a listing matching `query` to `to_status`; 409 if it no longer matches."""
    now = datetime.now(timezone.utc)
    updated = await db[LISTINGS].find_one_and_update(
        query,
        {
            "$set": {"status": to_status, "updated_at": now, **(extra_set or {})},
            "$push": {"status_history": {"status": to_status, "at": now, "by": by}},
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(status.HTTP_409_CONFLICT, error)
    return updated
