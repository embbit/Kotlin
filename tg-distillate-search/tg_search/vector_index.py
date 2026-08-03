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


@dataclass
class VectorIndex:
    ids: np.ndarray
    dates: np.ndarray
    embeddings: np.ndarray  # (N, D) float32, L2-normalized rows

    @property
    def count(self) -> int:
        return len(self.ids)

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
                SELECT v.message_id, m.date_unixtime, v.embedding
                FROM message_vectors v
                JOIN messages m ON m.id = v.message_id
                ORDER BY v.message_id
                """
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        dim = len(rows[0]["embedding"]) // 4
        n = len(rows)
        ids = np.empty(n, dtype=np.int64)
        dates = np.empty(n, dtype=np.int64)
        embeddings = np.empty((n, dim), dtype=np.float32)

        for i, row in enumerate(rows):
            ids[i] = row["message_id"]
            dates[i] = row["date_unixtime"]
            embeddings[i] = np.frombuffer(row["embedding"], dtype=np.float32, count=dim)

        cls._normalize_rows(embeddings)
        return cls(ids=ids, dates=dates, embeddings=embeddings)

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

        return [(int(self.ids[i]), float(scores[i])) for i in top_idx]


def build_vectors(
    db_path: Path,
    *,
    model_name: str = DEFAULT_MODEL,
    batch_size: int = BATCH_SIZE,
    replace: bool = False,
) -> dict[str, int | str]:
    conn = connect(db_path)
    try:
        conn.executescript(VECTOR_SCHEMA_SQL)
        if replace:
            conn.execute("DELETE FROM message_vectors")

        existing = conn.execute(
            "SELECT message_id FROM message_vectors"
        ).fetchall()
        done = {row["message_id"] for row in existing}

        rows = conn.execute(
            "SELECT id, text FROM messages ORDER BY id"
        ).fetchall()
        pending = [row for row in rows if row["id"] not in done]

        if not pending and done:
            return {
                "built": 0,
                "total_vectors": len(done),
                "model": get_meta(conn, META_MODEL) or model_name,
            }

        started = time.perf_counter()
        built = 0
        dim: int | None = None

        for offset in range(0, len(pending), batch_size):
            batch = pending[offset : offset + batch_size]
            texts = [row["text"] for row in batch]
            vectors = embed_passages(texts, model_name=model_name)
            if not vectors:
                continue
            if dim is None:
                dim = len(vectors[0])

            conn.executemany(
                "INSERT OR REPLACE INTO message_vectors(message_id, embedding) VALUES (?, ?)",
                [
                    (batch[i]["id"], np.asarray(vectors[i], dtype=np.float32).tobytes())
                    for i in range(len(batch))
                ],
            )
            conn.commit()
            built += len(batch)
            print(f"  embedded {built + len(done):,} / {len(rows):,}", flush=True)

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
