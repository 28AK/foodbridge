"""Registration and login, shared by the FastAPI routes and the Streamlit UI."""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password
from app.db import NGOS, USERS, get_db
from app.schemas import RegisterIn


async def register(data: RegisterIn) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)
    user = {
        "name": data.name.strip(),
        "email": data.email,
        "phone": data.phone.strip(),
        "role": data.role,
        "password_hash": hash_password(data.password),
        "created_at": now,
    }
    if data.role == "donor":
        user["donor_type"] = data.donor_type

    try:
        result = await db[USERS].insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user["_id"] = result.inserted_id

    if data.role == "ngo":
        ngo = {
            "name": user["name"],
            "type": data.org_type,
            "area": "",
            "address": data.address.strip(),
            "location": {"type": "Point", "coordinates": [data.lng, data.lat]},
            "capacity_meals": data.capacity_meals,
            "current_demand": data.capacity_meals,
            "veg_only": data.veg_only,
            "phone": user["phone"],
            # New organisations must be approved by an admin before receiving matches
            "verified": False,
            "user_id": user["_id"],
            "created_at": now,
        }
        ngo_result = await db[NGOS].insert_one(ngo)
        user["ngo_id"] = ngo_result.inserted_id
        await db[USERS].update_one({"_id": user["_id"]}, {"$set": {"ngo_id": user["ngo_id"]}})

    return user


async def authenticate(email: str, password: str) -> dict:
    user = await get_db()[USERS].find_one({"email": email.strip().lower()})
    if user is None or not verify_password(password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return user


async def get_user(user_id: ObjectId) -> dict | None:
    return await get_db()[USERS].find_one({"_id": user_id})
