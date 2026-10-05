"""Application settings, loaded from environment variables / the .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MongoDB
    db_host: str
    db_name: str = "foodbridge"

    # Auth
    jwt_secret: str = "dev-only-insecure-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Seeded admin account
    admin_email: str = "admin@foodbridge.local"
    admin_password: str = "admin1234"

    # AI model (pretrained, downloaded once from Hugging Face, runs locally)
    ai_model: str = "openai/clip-vit-base-patch16"
    ai_device: str = "cpu"  # "mps" uses the Apple Silicon GPU

    # Paths
    upload_dir: Path = BASE_DIR / "uploads"
    model_dir: Path = BASE_DIR / "models"
    frontend_dir: Path = BASE_DIR / "frontend"


@lru_cache
def get_settings() -> Settings:
    return Settings()
