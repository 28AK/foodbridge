"""NGO side: profile & daily demand, incoming matches, pickup lifecycle, route."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import require_role
from app.core.utils import parse_object_id, to_jsonable
from app.services import ngo_ops

router = APIRouter(prefix="/api/ngo", tags=["ngo"])


class NgoUpdate(BaseModel):
    current_demand: int | None = Field(None, ge=0, le=10_000)
    capacity_meals: int | None = Field(None, ge=1, le=10_000)
    veg_only: bool | None = None


async def current_ngo(user: dict = Depends(require_role("ngo"))) -> dict:
    return await ngo_ops.ngo_for(user)


@router.get("/me")
async def get_me(ngo: dict = Depends(current_ngo)):
    return to_jsonable(await ngo_ops.profile(ngo))


@router.patch("/me")
async def update_me(data: NgoUpdate, ngo: dict = Depends(current_ngo)):
    return to_jsonable(await ngo_ops.update(ngo, data.model_dump(exclude_none=True)))


@router.get("/matches")
async def list_matches(scope: str = "active", ngo: dict = Depends(current_ngo)):
    return to_jsonable(await ngo_ops.matches(ngo, scope))


@router.post("/matches/{listing_id}/accept")
async def accept(listing_id: str, ngo: dict = Depends(current_ngo)):
    return to_jsonable(await ngo_ops.accept(ngo, parse_object_id(listing_id)))


@router.post("/matches/{listing_id}/decline")
async def decline(listing_id: str, ngo: dict = Depends(current_ngo)):
    await ngo_ops.decline(ngo, parse_object_id(listing_id))
    return {"ok": True}


@router.post("/matches/{listing_id}/picked-up")
async def picked_up(listing_id: str, ngo: dict = Depends(current_ngo)):
    return to_jsonable(await ngo_ops.picked_up(ngo, parse_object_id(listing_id)))


@router.post("/matches/{listing_id}/delivered")
async def delivered(listing_id: str, ngo: dict = Depends(current_ngo)):
    return to_jsonable(await ngo_ops.delivered(ngo, parse_object_id(listing_id)))


@router.get("/route")
async def route(ngo: dict = Depends(current_ngo)):
    """Suggested pickup order for accepted, not-yet-collected donations."""
    return to_jsonable(await ngo_ops.route(ngo))
