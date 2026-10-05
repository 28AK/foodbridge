"""Background job, runs every minute:

  1. expire listings whose pickup deadline has passed
  2. release matches the NGO didn't accept within ACCEPT_TIMEOUT (-> next NGO)
  3. retry matching for listings that are still waiting for an NGO
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db import LISTINGS, get_db
from app.services.matching import match_listing, release_and_rematch

log = logging.getLogger(__name__)

INTERVAL_SECONDS = 60
ACCEPT_TIMEOUT = timedelta(minutes=15)
REMATCH_EVERY = timedelta(minutes=2)


async def run_once(now: datetime | None = None) -> dict:
    db = get_db()
    now = now or datetime.now(timezone.utc)

    expired = await db[LISTINGS].update_many(
        {"status": {"$in": ["listed", "matched"]}, "pickup_deadline": {"$lt": now}},
        {
            "$set": {"status": "expired", "updated_at": now},
            "$push": {"status_history": {"status": "expired", "at": now, "by": "system",
                                         "reason": "pickup deadline passed"}},
        },
    )

    released = 0
    stale = db[LISTINGS].find({
        "status": "matched",
        "match.accepted_at": None,
        "match.matched_at": {"$lt": now - ACCEPT_TIMEOUT},
    })
    async for listing in stale:
        await release_and_rematch(db, listing["_id"], listing["matched_ngo_id"], "not accepted in time")
        released += 1

    rematched = 0
    waiting = db[LISTINGS].find({
        "status": "listed",
        "pickup_deadline": {"$gt": now},
        "$or": [{"last_match_attempt": {"$lt": now - REMATCH_EVERY}},
                {"last_match_attempt": {"$exists": False}}],
    })
    async for listing in waiting:
        if await match_listing(db, listing):
            rematched += 1

    return {"expired": expired.modified_count, "released": released, "rematched": rematched}


async def run_forever() -> None:
    while True:
        try:
            result = await run_once()
            if any(result.values()):
                log.info("Scheduler: %s", result)
        except Exception:
            log.exception("Scheduler run failed")
        await asyncio.sleep(INTERVAL_SECONDS)
