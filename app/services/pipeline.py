"""Photo -> preprocessing (Module 1) -> AI analysis (Module 2) -> freshness risk.

Shared by listing creation and the "analyse photo" preview endpoint.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import cv2
from fastapi import HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.services.classifier import NOT_FOOD_REJECT, get_analyzer
from app.services.freshness import assess_freshness, quantity_check
from app.services.preprocessing import PreprocessResult, preprocess

log = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
IST = timezone(timedelta(hours=5, minutes=30))
MAX_FOOD_AGE = timedelta(hours=48)
FALLBACK_CATEGORY = "curry_dal"  # used for time-only risk if the AI is unavailable
VEG_MISMATCH_CONFIDENCE = 0.6


@dataclass
class PhotoAnalysis:
    image: PreprocessResult
    ai: dict | None
    ai_error: str | None
    freshness: dict
    warnings: list[str]


def check_photo(data: bytes, content_type: str | None) -> bytes:
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            "Photo must be a JPEG, PNG or WebP image")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Photo must be under 8 MB")
    return data


async def read_photo(photo: UploadFile) -> bytes:
    return check_photo(await photo.read(MAX_UPLOAD_BYTES + 1), photo.content_type)


def normalize_prepared_at(value: datetime) -> datetime:
    # Browser datetime-local inputs carry no timezone; donors are in India
    if value.tzinfo is None:
        value = value.replace(tzinfo=IST)
    value = value.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    if value > now + timedelta(minutes=10):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Preparation time cannot be in the future")
    if now - value > MAX_FOOD_AGE:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Food prepared more than 48 hours ago cannot be donated")
    return value


async def analyze_photo(data: bytes, prepared_at: datetime, declared_servings: int | None = None,
                        declared_category: str | None = None) -> PhotoAnalysis:
    """`prepared_at` must already be normalised to UTC."""
    try:
        image = await run_in_threadpool(preprocess, data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    ai, ai_error = None, None
    try:
        rgb = cv2.cvtColor(image.processed, cv2.COLOR_BGR2RGB)
        ai = await run_in_threadpool(get_analyzer().analyze, rgb)
    except Exception:
        log.exception("AI analysis failed")
        ai_error = "AI analysis is temporarily unavailable; risk is based on time only"

    if ai and 1 - ai["food_probability"] >= NOT_FOOD_REJECT:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "This photo doesn't look like food. Please upload a clear photo of the food.")

    now = datetime.now(timezone.utc)
    category = ai["category"]["key"] if ai else FALLBACK_CATEGORY
    spoiled = ai["freshness"]["spoiled_probability"] if ai else 0.0
    freshness = assess_freshness(category, prepared_at, spoiled, now)
    freshness["basis"] = "time + image" if ai else "time only"

    warnings = list(image.report["warnings"])
    if ai and not ai["is_food"]:
        warnings.append("The AI isn't sure this photo shows food – please check it")
    if ai and declared_servings:
        mismatch = quantity_check(declared_servings, ai["quantity_estimate"])
        if mismatch:
            warnings.append(mismatch)
    if (ai and declared_category == "veg" and ai["category"]["non_veg"]
            and ai["category"]["confidence"] >= VEG_MISMATCH_CONFIDENCE):
        warnings.append(f"Marked vegetarian, but the photo looks like {ai['dish']['name']} – please check")

    return PhotoAnalysis(image, ai, ai_error, freshness, warnings)
