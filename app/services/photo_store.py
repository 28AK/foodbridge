"""Food photos stored in MongoDB GridFS.

Free hosting (Hugging Face Spaces) has no permanent disk, so files written
locally would vanish on every restart. GridFS keeps them in Atlas instead.
"""
from bson import ObjectId
from gridfs import AsyncGridFSBucket

from app.db import get_db

BUCKET = "photos"


def bucket() -> AsyncGridFSBucket:
    return AsyncGridFSBucket(get_db(), bucket_name=BUCKET)


async def save_photo(data: bytes, filename: str, metadata: dict) -> str:
    """Store JPEG bytes; returns the URL path the browser can load."""
    file_id = await bucket().upload_from_stream(filename, data, metadata=metadata)
    return f"/photos/{file_id}"


async def read_photo(file_id: ObjectId) -> bytes:
    """Raises gridfs.errors.NoFile if it doesn't exist."""
    stream = await bucket().open_download_stream(file_id)
    return await stream.read()


async def delete_listing_photos(listing_id: ObjectId) -> int:
    deleted = 0
    async for grid_file in bucket().find({"metadata.listing_id": listing_id}):
        await bucket().delete(grid_file._id)
        deleted += 1
    return deleted
