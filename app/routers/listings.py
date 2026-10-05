"""Surplus food listings: donor upload -> preprocessing -> AI analysis -> stored listing."""
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.deps import get_current_user, require_role
from app.core.utils import parse_object_id, to_jsonable
from app.schemas import FoodCategory
from app.services import listing_ops
from app.services.pipeline import read_photo

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.post("/analyze")
async def analyze(
    photo: UploadFile = File(...),
    prepared_at: datetime = Form(...),
    quantity_servings: int | None = Form(None, ge=1, le=5000),
    food_category: FoodCategory | None = Form(None),
    user: dict = Depends(require_role("donor")),
):
    """Preview the AI result for a photo without creating a listing."""
    result = await listing_ops.preview(await read_photo(photo), prepared_at,
                                       quantity_servings, food_category)
    return to_jsonable(result)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_listing(
    food_name: str = Form(..., min_length=2, max_length=100),
    food_category: FoodCategory = Form(...),
    quantity_servings: int = Form(..., ge=1, le=5000),
    prepared_at: datetime = Form(...),
    address: str = Form(..., min_length=5, max_length=200),
    lat: float = Form(..., ge=-90, le=90),
    lng: float = Form(..., ge=-180, le=180),
    description: str = Form("", max_length=500),
    pickup_notes: str = Form("", max_length=300),
    photo: UploadFile = File(...),
    user: dict = Depends(require_role("donor")),
):
    listing = await listing_ops.create(
        user, photo=await read_photo(photo), food_name=food_name, food_category=food_category,
        quantity_servings=quantity_servings, prepared_at=prepared_at, address=address,
        lat=lat, lng=lng, description=description, pickup_notes=pickup_notes,
    )
    return to_jsonable(listing)


@router.get("/mine")
async def my_listings(user: dict = Depends(require_role("donor"))):
    return to_jsonable(await listing_ops.mine(user))


@router.post("/{listing_id}/cancel")
async def cancel_listing(listing_id: str, user: dict = Depends(require_role("donor"))):
    return to_jsonable(await listing_ops.cancel(user, parse_object_id(listing_id)))


@router.get("/{listing_id}")
async def get_listing(listing_id: str, user: dict = Depends(get_current_user)):
    return to_jsonable(await listing_ops.get_for(user, parse_object_id(listing_id)))
