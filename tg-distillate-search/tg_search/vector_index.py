"""Vector index stored in SQLite, loaded to numpy for search."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tg_search.db import connect, get_meta, set_meta
from tg_search.embeddings import DEFAULT_MODEL, embed_passages, embed_query
from tg_search.vector_schema import VECTOR_SCHEMA_SQL

BATCH_SIZE = 128
META_MODEL = "vector_model"
META_DIM = "vector_dim"
META_BUILT_AT = "vectors_built_at"
META_BUILD_TOTAL = "vector_build_total"
META_UPDATED_AT = "vectors_updated_at"
META_IN_PROGRESS = "vector_build_in_progress"
LOCK_RETRIES = 12


def _is_locked(exc: sqlite3.OperationalError) -> bool:
    msg = str(exc).lower()
    return "locked" in msg or "busy" in msg


def _write_batch(
    conn: sqlite3.Connection,
    batch: list,
    vectors: list,
) -> None:
    payload = [
        (batch[i]["rowid"], np.asarray(vectors[i], dtype=np.float32).tobytes())
        for i in range(len(batch))
    ]
    for attempt in range(LOCK_RETRIES):
        try:
            conn.executemany(
                "INSERT OR REPLACE INTO message_vectors(message_rowid, embedding) VALUES (?, ?)",
                payload,
            )
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            if not _is_locked(exc) or attempt == LOCK_RETRIES - 1:
                raise
            wait = min(2**attempt, 30)
            print(f"  database locked, retry in {wait}s …", flush=True)
            time.sleep(wait)


@dataclass
class VectorIndex:
    rowids: np.ndarray
    dates: np.ndarray
    embeddings: np.ndarray

    @property
    def count(self) -> int:
        return len(self.rowids)

    @classmethod
    def load(cls, db_path: Path) -> VectorIndex | None:
        conn = connect(db_path)
        try:
            conn.executescript(VECTOR_SCHEMA_SQL)
            row = conn.execute("SELECT COUNT(*) AS c FROM message_vectors").fetchone()
            if not row or row["c"] == 0:
                return None

            rows = conn.execute(
                """
                SELECT v.message_rowid, m.date_unixtime, v.embedding
                FROM message_vectors v
                JOIN messages m ON m.rowid = v.message_rowid
                ORDER BY v.message_rowid
                """
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        dim = len(rows[0]["embedding"]) // 4
        n = len(rows)
        rowids = np.empty(n, dtype=np.int64)
        dates = np.empty(n, dtype=np.int64)
        embeddings = np.empty((n, dim), dtype=np.float32)

        for i, row in enumerate(rows):
            rowids[i] = row["message_rowid"]
            dates[i] = row["date_unixtime"]
            embeddings[i] = np.frombuffer(row["embedding"], dtype=np.float32, count=dim)

        cls._normalize_rows(embeddings)
        return cls(rowids=rowids, dates=dates, embeddings=embeddings)

    @staticmethod
    def _normalize_rows(matrix: np.ndarray) -> None:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix /= norms

    def search(self, query: str, *, limit: int = 100) -> list[tuple[int, float]]:
        if self.count == 0:
            return []

        q = np.asarray(embed_query(query), dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q /= q_norm

        scores = self.embeddings @ q
        if limit >= self.count:
            top_idx = np.argsort(-scores)
        else:
            top_idx = np.argpartition(-scores, limit)[:limit]
            top_idx = top_idx[np.argsort(-scores[top_idx])]

        return [(int(self.rowids[i]), float(scores[i])) for i in top_idx]


def count_vectors(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM message_vectors").fetchone()
    return int(row["c"]) if row else 0


def vector_build_stats(conn: sqlite3.Connection, *, message_count: int | None = None) -> dict[str, int | str | bool | None]:
    from tg_search.db import count_messages, get_meta

    messages = message_count if message_count is not None else count_messages(conn)
    built = count_vectors(conn)
    build_total_raw = get_meta(conn, META_BUILD_TOTAL)
    target = int(build_total_raw) if build_total_raw else messages
    return {
        "built": built,
        "total": target,
        "messages": messages,
        "in_progress": get_meta(conn, META_IN_PROGRESS) == "1",
        "updated_at": get_meta(conn, META_UPDATED_AT),
        "built_at": get_meta(conn, META_BUILT_AT),
        "model": get_meta(conn, META_MODEL),
    }


def build_vectors(
    db_path: Path,
    *,
    model_name: str = DEFAULT_MODEL,
    batch_size: int = BATCH_SIZE,
    replace: bool = False,
) -> dict[str, int | str | float]:
    conn = connect(db_path)
    try:
        conn.executescript(VECTOR_SCHEMA_SQL)
        if replace:
            conn.execute("DELETE FROM message_vectors")
            set_meta(conn, "vector_count", "0")

        existing = conn.execute(
            "SELECT message_rowid FROM message_vectors"
        ).fetchall()
        done = {row["message_rowid"] for row in existing}

        rows = conn.execute(
            "SELECT rowid, text FROM messages ORDER BY rowid"
        ).fetchall()
        pending = [row for row in rows if row["rowid"] not in done]

        if not pending and done:
            set_meta(conn, META_IN_PROGRESS, "0")
            set_meta(conn, META_BUILD_TOTAL, str(len(rows)))
            set_meta(conn, "vector_count", str(len(done)))
            conn.commit()
            return {
                "built": 0,
                "total_vectors": len(done),
                "model": get_meta(conn, META_MODEL) or model_name,
            }

        set_meta(conn, META_BUILD_TOTAL, str(len(rows)))
        set_meta(conn, META_IN_PROGRESS, "1")
        set_meta(conn, "vector_count", str(len(done)))
        conn.commit()

        started = time.perf_counter()
        built = 0
        dim: int | None = None

        try:
            for offset in range(0, len(pending), batch_size):
                batch = pending[offset : offset + batch_size]
                texts = [row["text"] for row in batch]
                vectors = embed_passages(texts, model_name=model_name)
                if not vectors:
                    continue
                if dim is None:
                    dim = len(vectors[0])

                _write_batch(conn, batch, vectors)
                built += len(batch)
                total_done = len(done) + built
                set_meta(conn, "vector_count", str(total_done))
                set_meta(
                    conn,
                    META_UPDATED_AT,
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                conn.commit()
                print(f"  embedded {total_done:,} / {len(rows):,}", flush=True)
        finally:
            set_meta(conn, META_IN_PROGRESS, "0")
            conn.commit()

        set_meta(conn, META_MODEL, model_name)
        if dim is not None:
            set_meta(conn, META_DIM, str(dim))
        set_meta(conn, META_BUILT_AT, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        set_meta(conn, "vector_count", str(len(done) + built))
        conn.commit()

        elapsed = round(time.perf_counter() - started, 1)
        return {
            "built": built,
            "total_vectors": len(done) + built,
            "model": model_name,
            "elapsed_sec": elapsed,
        }
    finally:
        conn.close()
