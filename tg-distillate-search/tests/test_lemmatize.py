"""Tests for lemmatization."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tg_search.import_json import import_export
from tg_search.lemmatize import lemmatize_text, lemmatize_word
from tg_search.search import search

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestLemmatize(unittest.TestCase):
    def test_word_forms(self) -> None:
        self.assertEqual(lemmatize_word("сухопарника"), "сухопарник")
        self.assertEqual(lemmatize_word("колонну"), "колонна")

    def test_text(self) -> None:
        self.assertIn("сухопарник", lemmatize_text("купил сухопарника"))


class TestLemmaSearch(unittest.TestCase):
    def test_query_matches_inflected_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            hits = search(db, "колонна", limit=5)
            self.assertEqual(len(hits), 1)
            self.assertIn("колонну", hits[0].text.lower())


if __name__ == "__main__":
    unittest.main()
