"""Helpers for converting MongoDB documents to JSON-friendly dicts."""
from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def to_jsonable(value: Any) -> Any:
    """Recursively convert ObjectId/datetime values and rename `_id` to `id`."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {("id" if k == "_id" else k): to_jsonable(v) for k, v in value.items()}
    return value


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


def public_user(user: dict) -> dict:
    return to_jsonable({k: v for k, v in user.items() if k != "password_hash"})
