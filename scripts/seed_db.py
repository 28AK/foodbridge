"""Seed MongoDB with demo NGOs/shelters around Lucknow and demo user accounts.

Safe to run multiple times (upserts by email / name).
Run:  python -m scripts.seed_db
"""
import json
from datetime import datetime, timezone

from pymongo import MongoClient

from app import db as dbnames
from app.config import BASE_DIR, get_settings
from app.core.security import hash_password

DEMO_PASSWORD = "demo1234"


def upsert_user(users, email: str, password: str, sync_password: bool = False, **fields):
    """Create or update a user. Demo passwords are only set on creation;
    `sync_password` re-applies it every run (used for the admin from .env)."""
    now = datetime.now(timezone.utc)
    hashed = hash_password(password)
    update = {"$set": {**fields, "email": email}, "$setOnInsert": {"created_at": now}}
    if sync_password:
        update["$set"]["password_hash"] = hashed
    else:
        update["$setOnInsert"]["password_hash"] = hashed
    users.update_one({"email": email}, update, upsert=True)
    return users.find_one({"email": email}, {"_id": 1})["_id"]


def main() -> None:
    settings = get_settings()
    client = MongoClient(settings.db_host, serverSelectionTimeoutMS=10_000)
    db = client[settings.db_name]
    users, ngos = db[dbnames.USERS], db[dbnames.NGOS]
    now = datetime.now(timezone.utc)

    upsert_user(users, settings.admin_email, settings.admin_password, sync_password=True,
                name="FoodBridge Admin", role="admin", phone="")
    upsert_user(users, "donor@foodbridge.local", DEMO_PASSWORD,
                name="Demo Restaurant", role="donor", donor_type="restaurant",
                phone="+919000000100")

    seed = json.loads((BASE_DIR / "data/seed/ngos.json").read_text())
    for item in seed:
        ngos.update_one(
            {"name": item["name"]},
            {
                "$set": {
                    "name": item["name"],
                    "type": item["type"],
                    "area": item["area"],
                    "address": item["address"],
                    # GeoJSON order is [longitude, latitude]
                    "location": {"type": "Point", "coordinates": [item["lng"], item["lat"]]},
                    "capacity_meals": item["capacity_meals"],
                    "current_demand": item["current_demand"],
                    "veg_only": item["veg_only"],
                    "phone": item["phone"],
                    "verified": True,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        ngo_id = ngos.find_one({"name": item["name"]}, {"_id": 1})["_id"]
        user_id = upsert_user(users, item["email"], DEMO_PASSWORD,
                              name=item["name"], role="ngo", ngo_id=ngo_id, phone=item["phone"])
        ngos.update_one({"_id": ngo_id}, {"$set": {"user_id": user_id}})

    print(f"✅ Seeded {len(seed)} NGOs/shelters and {users.count_documents({})} users "
          f"into '{settings.db_name}'")
    print(f"   admin login : {settings.admin_email} / (ADMIN_PASSWORD from .env)")
    print(f"   donor login : donor@foodbridge.local / {DEMO_PASSWORD}")
    print(f"   NGO logins  : <ngo email from data/seed/ngos.json> / {DEMO_PASSWORD}")
    client.close()


if __name__ == "__main__":
    main()
