"""Shared helpers for external source synchronization."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass

from tg_search.db import rebuild_fts, set_meta
from tg_search.external_sources import META_SOURCES_UPDATED_AT
from tg_search.lemmatize import lemmatize_text


@dataclass(frozen=True)
class DocumentChunk:
    message_id: int
    external_id: str
    title: str
    text: str
    url: str
    date_unixtime: int
    date_iso: str
    content_hash: str


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def ensure_source(
    conn: sqlite3.Connection,
    *,
    chat_id: int,
    name: str,
    source_type: str,
    label: str,
    username: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO sources(chat_id, name, type, username, label)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            name = excluded.name,
            type = excluded.type,
            username = excluded.username,
            label = excluded.label
        """,
        (chat_id, name, source_type, username, label),
    )


def delete_external_documents(conn: sqlite3.Connection, chat_id: int, external_id: str) -> None:
    conn.execute(
        "DELETE FROM messages WHERE chat_id = ? AND from_id = ?",
        (chat_id, external_id),
    )


def upsert_chunks(conn: sqlite3.Connection, chat_id: int, chunks: list[DocumentChunk]) -> int:
    if not chunks:
        return 0

    delete_external_documents(conn, chat_id, chunks[0].external_id)
    insert_sql = """
        INSERT INTO messages (
            chat_id, message_id, date_unixtime, date_iso, from_name, from_id,
            reply_to_id, text, text_lemma, edited_unixtime, url, content_hash
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, ?, ?)
    """
    rows = [
        (
            chat_id,
            chunk.message_id,
            chunk.date_unixtime,
            chunk.date_iso,
            chunk.title,
            chunk.external_id,
            chunk.text,
            lemmatize_text(chunk.text),
            chunk.url,
            chunk.content_hash,
        )
        for chunk in chunks
    ]
    conn.executemany(insert_sql, rows)
    return len(rows)


def document_unchanged(conn: sqlite3.Connection, chat_id: int, external_id: str, doc_hash: str) -> bool:
    row = conn.execute(
        """
        SELECT content_hash FROM messages
        WHERE chat_id = ? AND from_id = ?
        LIMIT 1
        """,
        (chat_id, external_id),
    ).fetchone()
    return row is not None and row["content_hash"] == doc_hash


def finalize_sync(conn: sqlite3.Connection, *, rebuild_index: bool = True) -> None:
    if rebuild_index:
        rebuild_fts(conn)
    set_meta(conn, META_SOURCES_UPDATED_AT, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    conn.commit()
