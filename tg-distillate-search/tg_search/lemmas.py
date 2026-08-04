"""Backfill lemmatized text and rebuild lemma-aware FTS index."""

from __future__ import annotations

import sqlite3
import time

from tg_search.db import connect, get_meta, rebuild_fts, set_meta
from tg_search.lemmatize import lemmatize_text

BATCH_SIZE = 500
META_LEMMAS_INDEXED = "lemmas_indexed"
META_LEMMAS_BUILT_AT = "lemmas_built_at"

FTS_LEMMA_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text_lemma,
    from_name,
    content='messages',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
"""

FTS_LEGACY_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text,
    from_name,
    content='messages',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
"""


def fts_uses_lemmas(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='messages_fts'"
    ).fetchone()
    return bool(row and row[0] and "text_lemma" in row[0])


def lemmas_indexed(conn: sqlite3.Connection) -> bool:
    return get_meta(conn, META_LEMMAS_INDEXED) == "1" and fts_uses_lemmas(conn)


def ensure_lemma_column(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(messages)")}
    if "text_lemma" not in cols:
        conn.execute("ALTER TABLE messages ADD COLUMN text_lemma TEXT")


def backfill_lemmas(conn: sqlite3.Connection, *, batch_size: int = BATCH_SIZE) -> int:
    ensure_lemma_column(conn)
    pending = conn.execute(
        "SELECT rowid, text FROM messages WHERE text_lemma IS NULL OR text_lemma = ''"
    ).fetchall()
    if not pending:
        return 0

    updated = 0
    batch: list[tuple[str, int]] = []
    for row in pending:
        batch.append((lemmatize_text(row["text"]), int(row["rowid"])))
        if len(batch) >= batch_size:
            conn.executemany(
                "UPDATE messages SET text_lemma = ? WHERE rowid = ?",
                batch,
            )
            updated += len(batch)
            batch.clear()
            print(f"  lemmatized {updated:,} / {len(pending):,}", flush=True)

    if batch:
        conn.executemany("UPDATE messages SET text_lemma = ? WHERE rowid = ?", batch)
        updated += len(batch)

    return updated


def rebuild_lemma_fts(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS messages_fts")
    conn.executescript(FTS_LEMMA_SQL)
    rebuild_fts(conn)
    set_meta(conn, META_LEMMAS_INDEXED, "1")
    set_meta(conn, META_LEMMAS_BUILT_AT, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def build_lemmas(db_path, *, batch_size: int = BATCH_SIZE) -> dict[str, int | str | float]:
    started = time.perf_counter()
    conn = connect(db_path)
    try:
        updated = backfill_lemmas(conn, batch_size=batch_size)
        rebuild_lemma_fts(conn)
        conn.commit()
        elapsed = round(time.perf_counter() - started, 1)
        return {"updated": updated, "elapsed_sec": elapsed}
    finally:
        conn.close()
