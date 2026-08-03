"""Tests for fuzzy word matching."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sqlite3

from tg_search.fuzzy import fuzzy_token_match, text_matches_query_word
from tg_search.import_json import import_export
from tg_search.lemmatize import lemmatize_word
from tg_search.search import search

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestFuzzyTokenMatch(unittest.TestCase):
    def test_slang_variants(self) -> None:
        self.assertTrue(fuzzy_token_match("жинжинья", "жинья"))
        self.assertTrue(fuzzy_token_match("жиньжинья", "жинья"))

    def test_unrelated_words(self) -> None:
        self.assertFalse(fuzzy_token_match("жинжинья", "гравицапа"))
        self.assertFalse(fuzzy_token_match("сухопарник", "колонна"))

    def test_short_token_not_substring_of_query(self) -> None:
        self.assertFalse(fuzzy_token_match("нюанс", "а"))
        self.assertFalse(fuzzy_token_match("работа", "а"))
        self.assertFalse(fuzzy_token_match("бочка", "а"))


class TestFuzzySearch(unittest.TestCase):
    def test_query_finds_slang_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            conn = sqlite3.connect(db)
            conn.execute(
                """
                INSERT INTO messages (
                    chat_id, message_id, date_unixtime, date_iso, text, text_lemma
                ) VALUES (1663164507, 500, 1658493000, '2022-07-22',
                    'обсуждаем жинья для дистилляции', ?)
                """,
                ("обсуждаем жинья для дистилляции",),
            )
            conn.commit()
            conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            conn.commit()
            conn.close()

            hits = search(db, "жинжинья", limit=5)
            self.assertGreaterEqual(len(hits), 1)
            self.assertIn("жинья", hits[0].text.lower())

    def test_text_matches_query_word(self) -> None:
        self.assertTrue(
            text_matches_query_word(
                "тут жинья и всё",
                "жинжинья",
                lemmatize_word=lemmatize_word,
            )
        )


if __name__ == "__main__":
    unittest.main()
