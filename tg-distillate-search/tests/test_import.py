"""Tests for Telegram export import and search."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tg_search.import_json import import_export, message_link
from tg_search.search import search
from tg_search.text import flatten_text


FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestFlattenText(unittest.TestCase):
    def test_string(self) -> None:
        self.assertEqual(flatten_text("  hello  "), "hello")

    def test_array(self) -> None:
        raw = ["a ", {"type": "link", "text": "b"}, " c"]
        self.assertEqual(flatten_text(raw), "a b c")

    def test_null(self) -> None:
        self.assertIsNone(flatten_text(None))


class TestImportAndSearch(unittest.TestCase):
    def test_import_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            stats = import_export(FIXTURE, db, username="distillate_club_chat")
            self.assertEqual(stats["imported"], 2)
            self.assertEqual(stats["total_in_json"], 4)

            hits = search(db, "колонну", limit=5)
            self.assertEqual(len(hits), 1)
            self.assertIn("колонн", hits[0].snippet.lower())
            self.assertEqual(
                hits[0].link,
                message_link("distillate_club_chat", 1663164507, 2),
            )

            hits = search(db, "дефлегматор", limit=5)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].id, 3)


if __name__ == "__main__":
    unittest.main()
