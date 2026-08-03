"""Tests for per-source search filtering."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tg_search.import_json import import_export
from tg_search.search import search_page
from tg_search.source_filter import resolve_source, source_scope_label

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestSourceFilter(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        import_export(CHAT_FIXTURE, self.db, username="distillate_club_chat")

        conn = sqlite3.connect(self.db)
        conn.execute(
            """
            INSERT INTO sources(chat_id, name, type, username, label)
            VALUES (2000000001, 'Distillate Club', 'channel', 'distillate_club', 'канал')
            """
        )
        conn.execute(
            """
            INSERT INTO messages (
                chat_id, message_id, date_unixtime, date_iso, text, text_lemma
            ) VALUES (
                2000000001, 1, 1658492000, '2022-07-22', 'уникальный канальный пост', 'уникальный канальный пост'
            )
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_resolve_source_by_alias(self) -> None:
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        try:
            chat = resolve_source(conn, "chat")
            channel = resolve_source(conn, "channel")
            self.assertIsNotNone(chat)
            self.assertIsNotNone(channel)
            self.assertEqual(chat["label"], "чат")
            self.assertEqual(channel["label"], "канал")
        finally:
            conn.close()

    def test_search_scoped_to_chat(self) -> None:
        page = search_page(self.db, "уникальный", limit=10, chat_id=2000000001)
        self.assertEqual(len(page.hits), 1)
        self.assertEqual(page.hits[0].source_label, "канал")

        page_all = search_page(self.db, "уникальный", limit=10)
        self.assertEqual(len(page_all.hits), 1)

        page_chat = search_page(self.db, "уникальный", limit=10, chat_id=1663164507)
        self.assertEqual(page_chat.hits, [])

    def test_source_scope_label(self) -> None:
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        try:
            row = resolve_source(conn, "канал")
            self.assertEqual(source_scope_label(row), "канал")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
