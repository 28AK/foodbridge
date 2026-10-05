"""FastAPI dependencies: current user from the Bearer token, role checks."""
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.db import USERS, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

UNAUTHORIZED = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Invalid or expired login, please log in again",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_access_token(token)
        user_id = ObjectId(payload["sub"])
    except (jwt.PyJWTError, InvalidId, KeyError):
        raise UNAUTHORIZED
    user = await get_db()[USERS].find_one({"_id": user_id})
    if user is None:
        raise UNAUTHORIZED
    return user


def require_role(*roles: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to this")
        return user

    return checker
