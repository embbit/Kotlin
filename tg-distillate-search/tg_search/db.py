"""SQLite schema and connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS chat_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    date_unixtime INTEGER NOT NULL,
    date_iso TEXT NOT NULL,
    from_name TEXT,
    from_id TEXT,
    reply_to_id INTEGER,
    text TEXT NOT NULL,
    edited_unixtime INTEGER
);

CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date_unixtime);
CREATE INDEX IF NOT EXISTS idx_messages_from_id ON messages(from_id);
CREATE INDEX IF NOT EXISTS idx_messages_reply ON messages(reply_to_id);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text,
    from_name,
    content='messages',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    return conn


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO chat_meta(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute(
        "SELECT value FROM chat_meta WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else None


def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
