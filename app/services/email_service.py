import json
import os
from datetime import datetime, timezone
from typing import List

from app.models.email_model import EmailEntry, EmailEntryCreate

DATA_FILE = "data.json"


def _sync_to_s3():
    """Upload data.json to S3 if S3_BUCKET is configured."""
    if os.getenv("S3_BUCKET"):
        from app.services.s3_service import upload_file
        upload_file(DATA_FILE, "data.json")


def _read_all() -> List[dict]:
    """Read all entries from the JSON file. Returns empty list if file is missing or invalid."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_all(entries: List[dict]) -> None:
    """Persist the full list of entries to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def get_all_entries() -> List[EmailEntry]:
    """Return all stored entries as validated EmailEntry objects."""
    raw = _read_all()
    return [EmailEntry(**entry) for entry in raw]


def save_entry(entry: EmailEntryCreate) -> EmailEntry:
    """
    Append a new entry (with timestamp) to the JSON store.
    Returns the saved EmailEntry including created_at.
    """
    entries = _read_all()

    new_entry = EmailEntry(
        **entry.model_dump(),
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    entries.append(new_entry.model_dump())
    _write_all(entries)
    _sync_to_s3()

    return new_entry
