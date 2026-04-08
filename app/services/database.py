import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Optional

from app.models.email_model import (
    RfiEmail, RfiEmailCreate, Attachment, AttachmentCreate,
)

DB_PATH = os.getenv("DB_PATH", "data.db")

def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                title TEXT DEFAULT '',
                message TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rfi_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT,
                email_date DATETIME NOT NULL,
                received_at DATETIME NOT NULL,
                is_read BOOLEAN DEFAULT FALSE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfi_email_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT,
                file_size INTEGER,
                s3_key TEXT,
                uploaded_at DATETIME NOT NULL,
                FOREIGN KEY (rfi_email_id) REFERENCES rfi_emails(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


# --- RFI Email CRUD ---

def _row_to_attachment(row: sqlite3.Row) -> Attachment:
    return Attachment(
        id=row["id"],
        rfi_email_id=row["rfi_email_id"],
        filename=row["filename"],
        content_type=row["content_type"],
        file_size=row["file_size"],
        s3_key=row["s3_key"],
        uploaded_at=row["uploaded_at"],
    )


def _row_to_rfi(row: sqlite3.Row, attachments: List[Attachment] = None) -> RfiEmail:
    return RfiEmail(
        id=row["id"],
        message_id=row["message_id"],
        sender=row["sender"],
        subject=row["subject"],
        body=row["body"],
        email_date=row["email_date"],
        received_at=row["received_at"],
        is_read=bool(row["is_read"]),
        attachments=attachments or [],
    )


def rfi_exists(message_id: str) -> bool:
    """Return True if an RFI email with this message_id is already stored."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM rfi_emails WHERE message_id = ?", (message_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def save_rfi_email(entry: RfiEmailCreate) -> Optional[RfiEmail]:
    """Insert an RFI email and its attachments. Returns the saved RfiEmail,
    or None if a duplicate message_id already exists."""
    if entry.message_id and rfi_exists(entry.message_id):
        return None

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    conn = get_connection()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute(
            """INSERT INTO rfi_emails (message_id, sender, subject, body, email_date, received_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (entry.message_id, entry.sender, entry.subject, entry.body, entry.email_date, now),
        )
        rfi_id = cursor.lastrowid

        saved_attachments = []
        for att in entry.attachments:
            att_cursor = conn.execute(
                """INSERT INTO attachments (rfi_email_id, filename, content_type, file_size, s3_key, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (rfi_id, att.filename, att.content_type, att.file_size, att.s3_key, now),
            )
            saved_attachments.append(Attachment(
                id=att_cursor.lastrowid,
                rfi_email_id=rfi_id,
                uploaded_at=now,
                **att.model_dump(),
            ))

        conn.commit()

        row = conn.execute("SELECT * FROM rfi_emails WHERE id = ?", (rfi_id,)).fetchone()
        return _row_to_rfi(row, saved_attachments)
    finally:
        conn.close()


def get_all_rfis() -> List[RfiEmail]:
    """Return all RFI emails with their attachments, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM rfi_emails ORDER BY received_at DESC").fetchall()
        rfis = []
        for row in rows:
            att_rows = conn.execute(
                "SELECT * FROM attachments WHERE rfi_email_id = ?", (row["id"],)
            ).fetchall()
            attachments = [_row_to_attachment(a) for a in att_rows]
            rfis.append(_row_to_rfi(row, attachments))
        return rfis
    finally:
        conn.close()


def get_rfi_by_id(rfi_id: int) -> Optional[RfiEmail]:
    """Return a single RFI email by ID, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM rfi_emails WHERE id = ?", (rfi_id,)).fetchone()
        if row is None:
            return None
        att_rows = conn.execute(
            "SELECT * FROM attachments WHERE rfi_email_id = ?", (rfi_id,)
        ).fetchall()
        attachments = [_row_to_attachment(a) for a in att_rows]
        return _row_to_rfi(row, attachments)
    finally:
        conn.close()


def mark_as_read(rfi_id: int) -> Optional[RfiEmail]:
    """Mark an RFI email as read. Returns the updated RfiEmail, or None if not found."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE rfi_emails SET is_read = TRUE WHERE id = ?", (rfi_id,)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return get_rfi_by_id(rfi_id)
    finally:
        conn.close()
