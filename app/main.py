"""FoodBridge – FastAPI application entry point.

Run:  uvicorn app.main:app --reload
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import db
from app.config import get_settings
from app.routers import admin, auth, listings, ngo, pages, photos
from app.services import scheduler
from app.services.classifier import get_analyzer

settings = get_settings()
log = logging.getLogger(__name__)


async def warm_up_ai():
    # Load the AI model in the background so startup isn't blocked
    try:
        await asyncio.to_thread(get_analyzer().load)
    except Exception:
        log.warning("AI model unavailable; listings will use time-only risk scoring")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    warm_up = asyncio.create_task(warm_up_ai())
    background = asyncio.create_task(scheduler.run_forever())
    yield
    warm_up.cancel()
    background.cancel()
    await db.close()


app = FastAPI(
    title="FoodBridge API",
    description="Smart Surplus Food Redistribution & Wastage Reduction Platform",
    version="0.1.0",
    lifespan=lifespan,
)

settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.frontend_dir / "static"), name="static")
# Legacy: photos of early listings were saved on disk; new ones live in GridFS (/photos)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(photos.router)
app.include_router(ngo.router)
app.include_router(admin.router)
app.include_router(pages.router)


@app.get("/api/health", tags=["system"])
async def health():
    database = db.get_db()
    await database.command("ping")
    counts = {
        name: await database[name].count_documents({})
        for name in (db.USERS, db.NGOS, db.LISTINGS, db.NOTIFICATIONS)
    }
    analyzer = get_analyzer()
    return {
        "status": "ok",
        "database": settings.db_name,
        "counts": counts,
        "ai": {"model": analyzer.model_name, "status": analyzer.status},
    }
