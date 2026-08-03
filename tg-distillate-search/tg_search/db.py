"""SQLite schema and connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = "3"

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS chat_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    chat_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    username TEXT,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    date_unixtime INTEGER NOT NULL,
    date_iso TEXT NOT NULL,
    from_name TEXT,
    from_id TEXT,
    reply_to_id INTEGER,
    text TEXT NOT NULL,
    text_lemma TEXT,
    edited_unixtime INTEGER,
    UNIQUE(chat_id, message_id),
    FOREIGN KEY (chat_id) REFERENCES sources(chat_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date_unixtime);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_from_id ON messages(from_id);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text_lemma,
    from_name,
    content='messages',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
"""


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    old_rows = conn.execute("SELECT * FROM messages").fetchall()
    chat_id = int(get_meta(conn, "chat_id") or (old_rows[0]["chat_id"] if old_rows else 0))
    chat_name = get_meta(conn, "chat_name") or "Unknown"
    chat_type = get_meta(conn, "chat_type") or "unknown"
    username = get_meta(conn, "username")
    label = "чат" if "group" in chat_type else "канал" if "channel" in chat_type else "источник"

    conn.execute("DROP TABLE IF EXISTS messages_fts")
    conn.execute("DROP TABLE IF EXISTS message_vectors")
    conn.execute("DROP TABLE IF EXISTS messages")
    conn.execute("DROP TABLE IF EXISTS sources")
    conn.executescript(SCHEMA_SQL)

    conn.execute(
        "INSERT INTO sources(chat_id, name, type, username, label) VALUES (?, ?, ?, ?, ?)",
        (chat_id, chat_name, chat_type, username, label),
    )

    insert = """
        INSERT INTO messages (
            chat_id, message_id, date_unixtime, date_iso, from_name, from_id,
            reply_to_id, text, text_lemma, edited_unixtime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
    """
    for row in old_rows:
        conn.execute(
            insert,
            (
                row["chat_id"],
                row["id"],
                row["date_unixtime"],
                row["date_iso"],
                row["from_name"],
                row["from_id"],
                row["reply_to_id"],
                row["text"],
                row["edited_unixtime"],
            ),
        )

    set_meta(conn, "schema_version", "2")


def _ensure_v3_columns(conn: sqlite3.Connection) -> None:
    cols = _table_columns(conn, "messages")
    if "text_lemma" not in cols:
        conn.execute("ALTER TABLE messages ADD COLUMN text_lemma TEXT")


def ensure_schema(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "messages"):
        conn.executescript(SCHEMA_SQL)
        set_meta(conn, "schema_version", SCHEMA_VERSION)
        return

    cols = _table_columns(conn, "messages")
    if "message_id" not in cols and "id" in cols:
        _migrate_v1_to_v2(conn)
        cols = _table_columns(conn, "messages")

    _ensure_v3_columns(conn)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS chat_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
            chat_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            username TEXT,
            label TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date_unixtime);
        CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
        CREATE INDEX IF NOT EXISTS idx_messages_from_id ON messages(from_id);
        """
    )

    version = get_meta(conn, "schema_version") or "2"
    if version != SCHEMA_VERSION:
        set_meta(conn, "schema_version", SCHEMA_VERSION)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_schema(conn)
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


def count_messages(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()
    return int(row["c"]) if row else 0


def list_sources(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT chat_id, name, type, username, label FROM sources ORDER BY chat_id"
    ).fetchall()
