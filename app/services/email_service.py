from datetime import datetime, timezone
from typing import List

from app.models.email_model import EmailEntry, EmailEntryCreate
from app.services.database import get_connection


def get_all_entries() -> List[EmailEntry]:
    """Return all stored entries as validated EmailEntry objects."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT email, title, message, created_at FROM emails ORDER BY id DESC").fetchall()
        return [EmailEntry(email=row["email"], title=row["title"], message=row["message"], created_at=row["created_at"]) for row in rows]
    finally:
        conn.close()


def save_entry(entry: EmailEntryCreate) -> EmailEntry:
    """Insert a new entry into the database. Returns the saved EmailEntry."""
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO emails (email, title, message, created_at) VALUES (?, ?, ?, ?)",
            (entry.email, entry.title, entry.message, created_at),
        )
        conn.commit()
    finally:
        conn.close()

    return EmailEntry(**entry.model_dump(), created_at=created_at)
