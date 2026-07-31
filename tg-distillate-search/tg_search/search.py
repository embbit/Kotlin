"""Full-text search over imported messages."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from tg_search.db import connect, get_meta
from tg_search.import_json import message_link


@dataclass
class SearchHit:
    id: int
    date_iso: str
    from_name: str | None
    text: str
    reply_to_id: int | None
    link: str
    snippet: str


def _fts_query(raw: str) -> str:
    """Build a safe FTS5 query: words joined with AND."""
    words = re.findall(r"[\w\u0400-\u04FF]+", raw, flags=re.UNICODE)
    if not words:
        return ""
    return " ".join(f'"{w}"' for w in words)


def search(
    db_path: Path,
    query: str,
    *,
    limit: int = 10,
) -> list[SearchHit]:
    fts_q = _fts_query(query)
    if not fts_q:
        return []

    conn = connect(db_path)
    try:
        username = get_meta(conn, "username")
        chat_id = int(get_meta(conn, "chat_id") or 0)

        rows = conn.execute(
            """
            SELECT
                m.id,
                m.date_iso,
                m.from_name,
                m.text,
                m.reply_to_id,
                snippet(messages_fts, 0, '[', ']', ' … ', 24) AS snippet
            FROM messages_fts fts
            JOIN messages m ON m.id = fts.rowid
            WHERE messages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_q, limit),
        ).fetchall()

        hits: list[SearchHit] = []
        for row in rows:
            hits.append(
                SearchHit(
                    id=row["id"],
                    date_iso=row["date_iso"],
                    from_name=row["from_name"],
                    text=row["text"],
                    reply_to_id=row["reply_to_id"],
                    link=message_link(username, chat_id, row["id"]),
                    snippet=row["snippet"],
                )
            )
        return hits
    finally:
        conn.close()
