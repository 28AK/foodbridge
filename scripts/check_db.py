"""Check the MongoDB connection without printing any secrets.

Run:  python -m scripts.check_db
"""
import re
import sys

from pymongo import MongoClient

from app.config import get_settings

URI_PATTERN = re.compile(r"mongodb(\+srv)?://\S+")


def redact(text: str) -> str:
    return URI_PATTERN.sub("mongodb://<redacted>", text)


def main() -> int:
    try:
        settings = get_settings()
    except Exception as exc:
        print(f"❌ Could not load settings – is DB_HOST set in .env? ({type(exc).__name__})")
        return 1

    try:
        client = MongoClient(settings.db_host, serverSelectionTimeoutMS=10_000)
        client.admin.command("ping")
        info = client.server_info()
        db = client[settings.db_name]
        print("✅ Connected to MongoDB")
        print(f"   server version : {info.get('version')}")
        print(f"   database       : {settings.db_name}")
        print(f"   collections    : {sorted(db.list_collection_names()) or '(none yet)'}")
        client.close()
        return 0
    except Exception as exc:
        print(f"❌ Connection failed: {type(exc).__name__}: {redact(str(exc))[:300]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
