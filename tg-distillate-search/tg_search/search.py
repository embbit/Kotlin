"""Hybrid FTS + vector search with recency bias."""

from __future__ import annotations

import math
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from tg_search.db import connect
from tg_search.document_links import hit_link
from tg_search.fuzzy import (
    best_match_needle,
    proximity_match_ratio,
    short_prefixes,
    text_matches_query_word,
)
from tg_search.external_sources import HRTZ_CATALOG_CHAT_ID, HRTZ_CHAT_ID, YOUTUBE_CHAT_ID
from tg_search.lemmatize import lemmatize_word
from tg_search.lemmas import lemmas_indexed
from tg_search.query_synonyms import (
    expand_word_groups,
    fts_query_from_groups,
    text_matches_multi_word_synonyms,
    text_matches_synonym_word,
    title_topic_boost,
)
from tg_search.result_dedupe import dedupe_search_hits
from tg_search.source_priority import source_score_boost, source_sort_tier
from tg_search.stopwords import content_words, query_tokens
from tg_search.vector_index import VectorIndex

WEIGHT_VECTOR = 0.40
WEIGHT_FTS = 0.25
WEIGHT_RECENCY = 0.35
RECENCY_HALF_LIFE_DAYS = 90
MIN_VECTOR_ONLY_SIM = 0.52
MIN_VECTOR_ONLY_SIM_MULTI = 0.62
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
    source_type: str | None = None

    @property
    def id(self) -> int:
        """Backward-compatible alias for message_id."""
        return self.message_id


def _query_words(raw: str) -> list[str]:
    return query_tokens(raw)


def _search_words(raw: str, *, lemmatize: bool) -> list[str]:
    if lemmatize:
        words = content_words(raw, lemmatize_word)
    else:
        words = content_words(raw, lambda w: w)
    if not words:
        return _query_words(raw)
    return words


def _fts_query_words(words: list[str], *, prefix: bool = False) -> str:
    if not words:
        return ""
    groups = expand_word_groups(words)
    if len(groups) == 1 and prefix:
        return fts_query_from_groups(groups, prefix=True)
    return fts_query_from_groups(groups, prefix=False)


def _single_word_variants(word: str) -> set[str]:
    variants = {word.lower()}
    variants.add(lemmatize_word(word).lower())
    for alt in expand_word_groups([word])[0]:
        variants.add(alt)
    return variants


def _text_matches_single_word(text: str, word: str) -> bool:
    return text_matches_synonym_word(text, word, lemmatize_word=lemmatize_word)


def _make_snippet(text: str, words: list[str], *, max_len: int = 200) -> str:
    lower = text.lower()
    needles: list[str] = []
    for word in words:
        needles.append(word.lower())
        needles.extend(_single_word_variants(word))
        matched = best_match_needle(text, word)
        if matched:
            needles.append(matched)
    for needle in dict.fromkeys(needles):
        idx = lower.find(needle)
        if idx >= 0:
            start = max(0, idx - 60)
            end = min(len(text), idx + len(needle) + 100)
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
    if len(words) <= 1:
        return set(fts_map)
    if not vector_map:
        return set(fts_map)
    min_sim = MIN_VECTOR_ONLY_SIM_MULTI if len(words) >= 2 else MIN_VECTOR_ONLY_SIM
    candidates = set(fts_map) | set(vector_map)
    return {
        rowid
        for rowid in candidates
        if rowid in fts_map or vector_map.get(rowid, -1.0) >= min_sim
    }


def _score_weights(words: list[str]) -> tuple[float, float, float]:
    if len(words) <= 1:
        return 0.50, 0.30, 0.20
    if len(words) >= 3:
        return 0.40, 0.40, 0.20
    return 0.35, 0.35, 0.30


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
        SELECT m.*, s.username, s.label AS source_label, s.type AS source_type
        FROM messages m
        JOIN sources s ON s.chat_id = m.chat_id
        WHERE m.rowid IN ({placeholders})
        """,
        rowids,
    ).fetchall()
    return {row["rowid"]: row for row in rows}


def _run_fts_query(
    conn: sqlite3.Connection,
    fts_q: str,
    words: list[str],
    *,
    pool: int,
) -> dict[int, tuple[float, str]]:
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


def _like_hits(
    conn: sqlite3.Connection,
    word: str,
    *,
    pool: int,
    prefix: str | None = None,
) -> dict[int, tuple[float, str]]:
    needle = (prefix or word).lower()
    rows = conn.execute(
        """
        SELECT rowid, text
        FROM messages
        WHERE lower(text) LIKE ?
        ORDER BY date_unixtime DESC
        LIMIT ?
        """,
        (f"%{needle}%", pool * 4),
    ).fetchall()
    hits: dict[int, tuple[float, str]] = {}
    for row in rows:
        if not _text_matches_single_word(row["text"], word):
            continue
        hits[int(row["rowid"])] = (
            0.45,
            _make_snippet(row["text"], [word]),
        )
        if len(hits) >= pool:
            break
    return hits


def _fts_hits(
    conn: sqlite3.Connection,
    query: str,
    *,
    pool: int,
    lemmatize: bool,
) -> dict[int, tuple[float, str]]:
    words = _search_words(query, lemmatize=lemmatize)
    if not words:
        return {}

    fts_q = _fts_query_words(words)
    hits: dict[int, tuple[float, str]] = {}
    if fts_q:
        hits = _run_fts_query(conn, fts_q, words, pool=pool)

    if len(words) >= 2:
        near_distance = 8 + 3 * len(words)
        quoted = " ".join(f'"{w}"' for w in words)
        near_q = f"NEAR({quoted}, {near_distance})"
        near_hits = _run_fts_query(conn, near_q, words, pool=pool)
        for rowid, (score, snippet) in near_hits.items():
            boosted = score * 1.8
            if rowid in hits:
                prev_score, _prev_snip = hits[rowid]
                hits[rowid] = (max(prev_score, boosted), snippet)
            else:
                hits[rowid] = (boosted, snippet)

    if len(words) == 1:
        word = words[0]

        if not hits:
            prefix_q = _fts_query_words(words, prefix=True)
            if prefix_q and prefix_q != fts_q:
                hits = _run_fts_query(conn, prefix_q, words, pool=pool)

        if not hits:
            for pfx in short_prefixes(word, lemmatize_word=lemmatize_word):
                hits = _run_fts_query(conn, f"{pfx}*", words, pool=pool)
                if hits:
                    break

        if not hits:
            for pfx in short_prefixes(word, lemmatize_word=lemmatize_word):
                hits = _like_hits(conn, word, pool=pool, prefix=pfx)
                if hits:
                    break

        if not hits:
            hits = _like_hits(conn, word, pool=pool)

    if fts_q:
        external = _external_fts_hits(
            conn, fts_q, words, pool=min(max(pool // 3, 5), 15)
        )
        hits = _merge_fts_hits(hits, external)

    return hits


def _external_fts_hits(
    conn: sqlite3.Connection,
    fts_q: str,
    words: list[str],
    *,
    pool: int,
) -> dict[int, tuple[float, str]]:
    """Top FTS hits from site/YouTube — not drowned out by chat volume."""
    hits: dict[int, tuple[float, str]] = {}
    for chat_id in (HRTZ_CHAT_ID, HRTZ_CATALOG_CHAT_ID, YOUTUBE_CHAT_ID):
        rows = conn.execute(
            """
            SELECT
                m.rowid,
                rank AS fts_rank,
                m.text AS message_text,
                m.from_name
            FROM messages_fts fts
            JOIN messages m ON m.rowid = fts.rowid
            WHERE messages_fts MATCH ? AND m.chat_id = ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_q, chat_id, pool),
        ).fetchall()
        for row in rows:
            rowid = int(row["rowid"])
            score = _fts_score(row["fts_rank"]) * 2.8
            score *= title_topic_boost(
                row["from_name"],
                words,
                lemmatize_word=lemmatize_word,
            )
            snippet = _make_snippet(row["message_text"], words)
            prev = hits.get(rowid)
            if prev is None or score > prev[0]:
                hits[rowid] = (score, snippet)
    return hits


def _merge_fts_hits(
    hits: dict[int, tuple[float, str]],
    extra: dict[int, tuple[float, str]],
) -> dict[int, tuple[float, str]]:
    for rowid, (score, snippet) in extra.items():
        if rowid in hits:
            prev_score, _prev_snip = hits[rowid]
            hits[rowid] = (max(prev_score, score), snippet)
        else:
            hits[rowid] = (score, snippet)
    return hits


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
        use_lemmas = lemmas_indexed(conn)
        words = _search_words(query, lemmatize=use_lemmas)

        fts_map = _fts_hits(conn, query, pool=pool, lemmatize=use_lemmas)
        vector_map: dict[int, float] = {}
        if vector_index is not None:
            for rowid, sim in vector_index.search(query, limit=pool):
                vector_map[rowid] = sim

        candidate_rowids = _select_candidates(fts_map, vector_map, words)
        if len(words) >= 3:
            candidate_rowids = {rowid for rowid in candidate_rowids if rowid in fts_map}
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

            if len(words) >= 3:
                prox = proximity_match_ratio(
                    row["text"], words, lemmatize_word=lemmatize_word
                )
                total *= 1.0 + 0.45 * prox

            total *= source_score_boost(
                int(row["chat_id"]),
                row["source_label"],
                row["source_type"],
            )

            if int(row["chat_id"]) in (HRTZ_CHAT_ID, HRTZ_CATALOG_CHAT_ID, YOUTUBE_CHAT_ID):
                total *= title_topic_boost(
                    row["from_name"],
                    words,
                    lemmatize_word=lemmatize_word,
                )

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
                    link=hit_link(row),
                    snippet=snippet,
                    score=total,
                    source_type=row["source_type"],
                )
            )

        if len(words) <= 1:
            if words:
                scored = [h for h in scored if _text_matches_single_word(h.text, words[0])]
        else:
            scored = [
                h
                for h in scored
                if text_matches_multi_word_synonyms(
                    h.text, words, lemmatize_word=lemmatize_word
                )
            ]

        scored.sort(
            key=lambda h: (
                -h.score,
                -source_sort_tier(
                    h.chat_id, h.source_label, h.source_type
                ),
                -h.date_unixtime,
            )
        )
        scored = dedupe_search_hits(scored)
        if scored:
            floor = scored[0].score * RELEVANCE_SCORE_RATIO
            scored = [h for h in scored if h.score >= floor]
        page = scored[offset : offset + limit]
        has_more = len(scored) > offset + limit
        return SearchPage(hits=page, has_more=has_more, offset=offset)
    finally:
        conn.close()
