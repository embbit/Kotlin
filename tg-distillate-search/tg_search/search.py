"""Hybrid FTS + vector search with recency bias."""

from __future__ import annotations

import math
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from tg_search.db import connect
from tg_search.import_json import message_link
from tg_search.lemmatize import lemmatize_word
from tg_search.lemmas import lemmas_indexed
from tg_search.vector_index import VectorIndex

WEIGHT_VECTOR = 0.40
WEIGHT_FTS = 0.25
WEIGHT_RECENCY = 0.35
RECENCY_HALF_LIFE_DAYS = 90
MIN_VECTOR_ONLY_SIM = 0.52
RELEVANCE_SCORE_RATIO = 0.42


@dataclass
class SearchHit:
    rowid: int
    message_id: int
    chat_id: int
    source_label: str
    date_iso: str
    date_unixtime: int
    from_name: str | None
    text: str
    reply_to_id: int | None
    link: str
    snippet: str
    score: float = 0.0

    @property
    def id(self) -> int:
        """Backward-compatible alias for message_id."""
        return self.message_id


def _query_words(raw: str) -> list[str]:
    return re.findall(r"[\w\u0400-\u04FF]+", raw, flags=re.UNICODE)


def _fts_query(raw: str, *, lemmatize: bool) -> str:
    words = _query_words(raw)
    if not words:
        return ""
    if lemmatize:
        words = [lemmatize_word(w) for w in words]
    return " ".join(f'"{w}"' for w in words)


def _make_snippet(text: str, words: list[str], *, max_len: int = 200) -> str:
    lower = text.lower()
    for word in words:
        idx = lower.find(word.lower())
        if idx >= 0:
            start = max(0, idx - 60)
            end = min(len(text), idx + len(word) + 100)
            chunk = text[start:end]
            if start > 0:
                chunk = "… " + chunk
            if end < len(text):
                chunk = chunk + " …"
            return chunk[:max_len]
    return text[:max_len]


def _select_candidates(
    fts_map: dict[int, tuple[float, str]],
    vector_map: dict[int, float],
    words: list[str],
) -> set[int]:
    if not fts_map and not vector_map:
        return set()
    if not vector_map:
        return set(fts_map)
    # Single specific term: keep only literal FTS matches (vector re-ranks them).
    if len(words) == 1 and fts_map:
        return set(fts_map)
    candidates = set(fts_map) | set(vector_map)
    return {
        rowid
        for rowid in candidates
        if rowid in fts_map or vector_map.get(rowid, -1.0) >= MIN_VECTOR_ONLY_SIM
    }


def _score_weights(words: list[str]) -> tuple[float, float, float]:
    if len(words) == 1:
        return 0.50, 0.30, 0.20
    return WEIGHT_FTS, WEIGHT_VECTOR, WEIGHT_RECENCY


def _recency_score(date_unixtime: int, now: int | None = None) -> float:
    now = now or int(time.time())
    age_days = max(0.0, (now - date_unixtime) / 86400.0)
    return math.exp(-age_days / RECENCY_HALF_LIFE_DAYS)


def _fts_score(rank: float) -> float:
    return 1.0 / (1.0 + max(float(rank), 0.0))


def _vector_score(sim: float) -> float:
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


def _fetch_messages(conn: sqlite3.Connection, rowids: list[int]) -> dict[int, sqlite3.Row]:
    if not rowids:
        return {}
    placeholders = ",".join("?" * len(rowids))
    rows = conn.execute(
        f"""
        SELECT m.*, s.username, s.label AS source_label
        FROM messages m
        JOIN sources s ON s.chat_id = m.chat_id
        WHERE m.rowid IN ({placeholders})
        """,
        rowids,
    ).fetchall()
    return {row["rowid"]: row for row in rows}


def _fts_hits(
    conn: sqlite3.Connection,
    query: str,
    *,
    pool: int,
    lemmatize: bool,
) -> dict[int, tuple[float, str]]:
    words = _query_words(query)
    fts_q = _fts_query(query, lemmatize=lemmatize)
    if not fts_q:
        return {}

    rows = conn.execute(
        """
        SELECT
            m.rowid,
            rank AS fts_rank,
            m.text AS message_text
        FROM messages_fts fts
        JOIN messages m ON m.rowid = fts.rowid
        WHERE messages_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_q, pool),
    ).fetchall()

    return {
        row["rowid"]: (
            _fts_score(row["fts_rank"]),
            _make_snippet(row["message_text"], words),
        )
        for row in rows
    }


@dataclass
class SearchPage:
    hits: list[SearchHit]
    has_more: bool
    offset: int


def search(
    db_path: Path,
    query: str,
    *,
    limit: int = 10,
    offset: int = 0,
    vector_index: VectorIndex | None = None,
) -> list[SearchHit]:
    return search_page(
        db_path, query, limit=limit, offset=offset, vector_index=vector_index
    ).hits


def search_page(
    db_path: Path,
    query: str,
    *,
    limit: int = 10,
    offset: int = 0,
    vector_index: VectorIndex | None = None,
) -> SearchPage:
    query = query.strip()
    if not query:
        return SearchPage(hits=[], has_more=False, offset=offset)

    conn = connect(db_path)
    try:
        pool = min(max((offset + limit) * 3, 50), 500)
        words = _query_words(query)
        use_lemmas = lemmas_indexed(conn)

        fts_map = _fts_hits(conn, query, pool=pool, lemmatize=use_lemmas)
        vector_map: dict[int, float] = {}
        if vector_index is not None:
            for rowid, sim in vector_index.search(query, limit=pool):
                vector_map[rowid] = sim

        candidate_rowids = _select_candidates(fts_map, vector_map, words)
        if not candidate_rowids:
            return SearchPage(hits=[], has_more=False, offset=offset)

        messages = _fetch_messages(conn, list(candidate_rowids))
        now = int(time.time())
        scored: list[SearchHit] = []
        w_fts, w_vec, w_rec = _score_weights(words)

        for rowid in candidate_rowids:
            row = messages.get(rowid)
            if row is None:
                continue

            v = _vector_score(vector_map[rowid]) if rowid in vector_map else 0.0
            if rowid in fts_map:
                f, snippet = fts_map[rowid]
            else:
                f, snippet = 0.0, row["text"][:200]
            r = _recency_score(int(row["date_unixtime"]), now)

            if vector_index is None and rowid not in fts_map:
                continue

            if vector_index is None:
                total = w_fts * f + (w_rec + w_vec) * r
            elif rowid not in fts_map:
                total = w_vec * v + (w_fts + w_rec) * r
            else:
                total = w_vec * v + w_fts * f + w_rec * r

            scored.append(
                SearchHit(
                    rowid=rowid,
                    message_id=int(row["message_id"]),
                    chat_id=int(row["chat_id"]),
                    source_label=row["source_label"],
                    date_iso=row["date_iso"],
                    date_unixtime=int(row["date_unixtime"]),
                    from_name=row["from_name"],
                    text=row["text"],
                    reply_to_id=row["reply_to_id"],
                    link=message_link(row["username"], int(row["chat_id"]), int(row["message_id"])),
                    snippet=snippet,
                    score=total,
                )
            )

        scored.sort(key=lambda h: (-h.score, -h.date_unixtime))
        if scored:
            floor = scored[0].score * RELEVANCE_SCORE_RATIO
            scored = [h for h in scored if h.score >= floor]
        page = scored[offset : offset + limit]
        has_more = len(scored) > offset + limit
        return SearchPage(hits=page, has_more=has_more, offset=offset)
    finally:
        conn.close()
