import sqlite3
import os

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
