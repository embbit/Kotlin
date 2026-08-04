"""Tests for vector build progress stats."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sqlite3

from tg_search.db import set_meta
from tg_search.import_json import import_export
from tg_search.vector_index import META_BUILD_TOTAL, META_IN_PROGRESS, build_vectors, vector_build_stats

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestVectorBuildStats(unittest.TestCase):
    def test_stats_from_database_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            set_meta(conn, META_BUILD_TOTAL, "10")
            set_meta(conn, META_IN_PROGRESS, "1")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS message_vectors ("
                "message_rowid INTEGER PRIMARY KEY, embedding BLOB NOT NULL)"
            )
            conn.execute(
                "INSERT INTO message_vectors(message_rowid, embedding) VALUES (1, X'0000')"
            )
            conn.commit()
            stats = vector_build_stats(conn)
            conn.close()

            self.assertEqual(stats["built"], 1)
            self.assertEqual(stats["total"], 10)
            self.assertTrue(stats["in_progress"])

    def test_build_updates_progress_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            from unittest.mock import patch

            fake_vec = [0.1, 0.2, 0.3]

            with patch(
                "tg_search.vector_index.embed_passages",
                return_value=[fake_vec],
            ):
                build_vectors(db, batch_size=1)

            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            stats = vector_build_stats(conn)
            in_progress = conn.execute(
                "SELECT value FROM chat_meta WHERE key = ?", (META_IN_PROGRESS,)
            ).fetchone()["value"]
            conn.close()

            self.assertEqual(stats["built"], stats["total"])
            self.assertFalse(stats["in_progress"])
            self.assertEqual(in_progress, "0")


if __name__ == "__main__":
    unittest.main()
