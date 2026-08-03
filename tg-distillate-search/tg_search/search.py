"""Hybrid FTS + vector search with recency bias."""

from __future__ import annotations

import math
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from tg_search.db import connect, get_meta
from tg_search.import_json import message_link
from tg_search.vector_index import VectorIndex

# Higher recency weight → newer messages rank above old ones with similar relevance.
WEIGHT_VECTOR = 0.40
WEIGHT_FTS = 0.25
WEIGHT_RECENCY = 0.35
RECENCY_HALF_LIFE_DAYS = 90


@dataclass
class SearchHit:
    id: int
    date_iso: str
    date_unixtime: int
    from_name: str | None
    text: str
    reply_to_id: int | None
    link: str
    snippet: str
    score: float = 0.0


def _fts_query(raw: str) -> str:
    words = re.findall(r"[\w\u0400-\u04FF]+", raw, flags=re.UNICODE)
    if not words:
        return ""
    return " ".join(f'"{w}"' for w in words)


def _recency_score(date_unixtime: int, now: int | None = None) -> float:
    now = now or int(time.time())
    age_days = max(0.0, (now - date_unixtime) / 86400.0)
    return math.exp(-age_days / RECENCY_HALF_LIFE_DAYS)


def _fts_score(rank: float) -> float:
    # FTS5 bm25 rank: lower is better → map to (0, 1]
    return 1.0 / (1.0 + max(float(rank), 0.0))


def _vector_score(sim: float) -> float:
    # Cosine similarity for normalized vectors in [-1, 1] → [0, 1]
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


def _fetch_messages(conn: sqlite3.Connection, ids: list[int]) -> dict[int, sqlite3.Row]:
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM messages WHERE id IN ({placeholders})",
        ids,
    ).fetchall()
    return {row["id"]: row for row in rows}


def _fts_hits(conn: sqlite3.Connection, query: str, *, pool: int) -> dict[int, tuple[float, str]]:
    fts_q = _fts_query(query)
    if not fts_q:
        return {}

    rows = conn.execute(
        """
        SELECT
            m.id,
            rank AS fts_rank,
            snippet(messages_fts, 0, '[', ']', ' … ', 24) AS snippet
        FROM messages_fts fts
        JOIN messages m ON m.id = fts.rowid
        WHERE messages_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_q, pool),
    ).fetchall()

    return {
        row["id"]: (_fts_score(row["fts_rank"]), row["snippet"])
        for row in rows
    }


def search(
    db_path: Path,
    query: str,
    *,
    limit: int = 10,
    vector_index: VectorIndex | None = None,
) -> list[SearchHit]:
    query = query.strip()
    if not query:
        return []

    conn = connect(db_path)
    try:
        username = get_meta(conn, "username")
        chat_id = int(get_meta(conn, "chat_id") or 0)
        pool = max(limit * 10, 50)

        fts_map = _fts_hits(conn, query, pool=pool)
        vector_map: dict[int, float] = {}
        if vector_index is not None:
            for msg_id, sim in vector_index.search(query, limit=pool):
                vector_map[msg_id] = sim

        candidate_ids = set(fts_map) | set(vector_map)
        if not candidate_ids:
            return []

        messages = _fetch_messages(conn, list(candidate_ids))
        now = int(time.time())
        scored: list[SearchHit] = []

        for msg_id in candidate_ids:
            row = messages.get(msg_id)
            if row is None:
                continue

            v = _vector_score(vector_map[msg_id]) if msg_id in vector_map else 0.0
            if msg_id in fts_map:
                f, snippet = fts_map[msg_id]
            else:
                f, snippet = 0.0, row["text"][:200]
            r = _recency_score(int(row["date_unixtime"]), now)

            if vector_index is None and msg_id not in fts_map:
                continue

            if vector_index is None:
                total = WEIGHT_FTS * f + (WEIGHT_RECENCY + WEIGHT_VECTOR) * r
            elif msg_id not in fts_map:
                total = WEIGHT_VECTOR * v + (WEIGHT_FTS + WEIGHT_RECENCY) * r
            else:
                total = WEIGHT_VECTOR * v + WEIGHT_FTS * f + WEIGHT_RECENCY * r

            scored.append(
                SearchHit(
                    id=msg_id,
                    date_iso=row["date_iso"],
                    date_unixtime=int(row["date_unixtime"]),
                    from_name=row["from_name"],
                    text=row["text"],
                    reply_to_id=row["reply_to_id"],
                    link=message_link(username, chat_id, msg_id),
                    snippet=snippet,
                    score=total,
                )
            )

        scored.sort(key=lambda h: (-h.score, -h.date_unixtime))
        return scored[:limit]
    finally:
        conn.close()
