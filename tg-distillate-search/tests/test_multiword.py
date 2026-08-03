"""Tests for multi-word search relevance."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sqlite3

from tg_search.import_json import import_export
from tg_search.search import search
from tg_search.stopwords import content_words
from tg_search.lemmatize import lemmatize_word

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


class TestMultiWordSearch(unittest.TestCase):
    def test_content_words_drop_stopwords(self) -> None:
        words = content_words("нюансы в работе с новыми бочками", lemmatize_word)
        self.assertIn("бочка", words)
        self.assertNotIn("в", words)
        self.assertNotIn("с", words)

    def test_multi_word_excludes_single_keyword_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            conn = sqlite3.connect(db)
            conn.execute(
                """
                INSERT INTO messages (
                    chat_id, message_id, date_unixtime, date_iso, text, text_lemma
                ) VALUES (1663164507, 501, 1658494000, '2022-07-22',
                    'просто новая бочка стоит в углу', 'просто новый бочка стоить в угол')
                """
            )
            conn.execute(
                """
                INSERT INTO messages (
                    chat_id, message_id, date_unixtime, date_iso, text, text_lemma
                ) VALUES (1663164507, 502, 1658495000, '2022-07-23',
                    'нюансы работы с новыми бочками при первом использовании',
                    'нюанс работа с новый бочка при первый использование')
                """
            )
            conn.commit()
            conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            conn.commit()
            conn.close()

            hits = search(db, "нюансы в работе с новыми бочками", limit=10)
            texts = [h.text.lower() for h in hits]
            self.assertTrue(any("нюанс" in t for t in texts))
            self.assertFalse(any("стоит в углу" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
