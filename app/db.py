"""MongoDB connection (async) and collection/index setup."""
from pymongo import ASCENDING, DESCENDING, GEOSPHERE, AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import get_settings

# Collection names
USERS = "users"
NGOS = "ngos"
LISTINGS = "listings"
NOTIFICATIONS = "notifications"

_client: AsyncMongoClient | None = None


async def connect() -> None:
    global _client
    settings = get_settings()
    # tz_aware: return dates as UTC-aware datetimes (naive ones show up 5.5 h off in the browser)
    _client = AsyncMongoClient(settings.db_host, serverSelectionTimeoutMS=10_000, tz_aware=True)
    await _client.admin.command("ping")
    await ensure_indexes()


async def close() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_db() -> AsyncDatabase:
    if _client is None:
        raise RuntimeError("Database not connected; call connect() first")
    return _client[get_settings().db_name]


async def ensure_indexes() -> None:
    db = get_db()
    await db[USERS].create_index("email", unique=True)
    # GeoJSON points -> enables $near / $geoNear proximity queries for matching
    await db[NGOS].create_index([("location", GEOSPHERE)])
    await db[LISTINGS].create_index([("location", GEOSPHERE)])
    await db[LISTINGS].create_index([("status", ASCENDING), ("created_at", DESCENDING)])
    await db[LISTINGS].create_index("donor_id")
    await db[LISTINGS].create_index([("matched_ngo_id", ASCENDING), ("status", ASCENDING)])
    await db[LISTINGS].create_index([("status", ASCENDING), ("pickup_deadline", ASCENDING)])
    await db[NOTIFICATIONS].create_index([("recipient_id", ASCENDING), ("created_at", DESCENDING)])
