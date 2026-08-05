"""Tests for search query analytics."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from tg_search.db import connect
from tg_search.search_analytics import (
    build_search_stats,
    format_search_stats,
    log_search,
    normalize_query,
)


class TestSearchAnalytics(unittest.TestCase):
    def test_normalize_query_strips_stopwords(self) -> None:
        norm = normalize_query("Где заказать энзимы")
        self.assertIn("заказать", norm)
        self.assertIn("энзим", norm)
        self.assertNotIn("где", norm.split())

    def test_log_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            conn = connect(db)
            now = int(time.time())
            log_search(
                conn,
                user_id=100,
                username="alice",
                query_raw="Где заказать энзимы",
                hits_count=5,
                ts=now,
            )
            log_search(
                conn,
                user_id=100,
                username="alice",
                query_raw="бочка дуб",
                hits_count=3,
                ts=now,
            )
            log_search(
                conn,
                user_id=200,
                username="bob",
                query_raw="энзим EN-06",
                hits_count=1,
                ts=now,
            )
            conn.close()

            conn = connect(db)
            report = build_search_stats(conn, days=30)
            conn.close()

            self.assertEqual(report.total_searches, 3)
            self.assertEqual(report.unique_users, 2)
            self.assertEqual(report.top_users[0][1], 2)
            self.assertTrue(any("энзим" in word for word, _ in report.top_words))
            self.assertTrue(
                any("энзим" in query.lower() for query, _ in report.top_queries)
            )

            text = format_search_stats(report)
            self.assertIn("alice", text)
            self.assertIn("энзим", text)


if __name__ == "__main__":
    unittest.main()
