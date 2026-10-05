"""Admin: verify NGOs so they can receive matches."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import require_role
from app.core.utils import parse_object_id, to_jsonable
from app.services import ngo_ops

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])


class VerifyIn(BaseModel):
    verified: bool


@router.get("/ngos")
async def list_ngos():
    return to_jsonable(await ngo_ops.list_all())


@router.post("/ngos/{ngo_id}/verify")
async def verify_ngo(ngo_id: str, data: VerifyIn):
    await ngo_ops.set_verified(parse_object_id(ngo_id), data.verified)
    return {"ok": True, "verified": data.verified}
