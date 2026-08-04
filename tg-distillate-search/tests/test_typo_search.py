"""Tests for typo-tolerant multi-word search."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tg_search.import_json import import_export
from tg_search.lemmatize import lemmatize_text
from tg_search.search import search

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestTypoMultiWordSearch(unittest.TestCase):
    def test_double_letter_typo_finds_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            text = "30 литров вишневой ратафии на зиму"
            conn = sqlite3.connect(db)
            conn.execute(
                """
                INSERT INTO messages (
                    chat_id, message_id, date_unixtime, date_iso, text, text_lemma
                ) VALUES (1663164507, 700, 1658500000, '2022-07-26', ?, ?)
                """,
                (text, lemmatize_text(text)),
            )
            conn.commit()
            conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            conn.commit()
            conn.close()

            correct = search(db, "вишневая ратафия", limit=5)
            typo = search(db, "вишневая раттафия", limit=5)

            self.assertGreaterEqual(len(correct), 1)
            self.assertIn("ратаф", correct[0].text.lower())
            self.assertGreaterEqual(len(typo), 1)
            self.assertIn("ратаф", typo[0].text.lower())

    def test_unrelated_typo_still_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            hits = search(db, "гравицапа колонна", limit=5)
            self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
