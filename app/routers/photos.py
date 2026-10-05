"""Serve food photos from GridFS."""
from fastapi import APIRouter, HTTPException, Response, status
from gridfs.errors import NoFile

from app.core.utils import parse_object_id
from app.services.photo_store import read_photo

router = APIRouter(include_in_schema=False)


@router.get("/photos/{file_id}")
async def get_photo(file_id: str):
    try:
        data = await read_photo(parse_object_id(file_id))
    except NoFile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")
    # Photos never change once stored, so browsers may cache them forever
    return Response(data, media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})
