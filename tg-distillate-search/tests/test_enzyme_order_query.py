"""Tests for natural-language enzyme order queries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tg_search.db import connect, rebuild_fts
from tg_search.external_sources import HRTZ_CHAT_ID
from tg_search.search import search_page
from tg_search.stopwords import content_words
from tg_search.lemmatize import lemmatize_word
from tg_search.lemmas import lemmas_indexed


class TestEnzymeOrderQuery(unittest.TestCase):
    def test_question_words_stripped(self) -> None:
        words = content_words("Где заказать энзимы", lemmatize_word)
        self.assertNotIn("где", words)
        self.assertIn("заказать", words)

    def test_order_enzymes_query_returns_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            conn = connect(db)
            conn.execute(
                """
                INSERT INTO sources (chat_id, type, name, username, label)
                VALUES (?, 'web', 'hrtz.store', 'hrtz', 'сайт')
                """,
                (HRTZ_CHAT_ID,),
            )
            conn.execute(
                """
                INSERT INTO sources (chat_id, type, name, username, label)
                VALUES (100, 'supergroup', 'chat', 'distillate_club_chat', 'чат')
                """
            )
            conn.execute(
                """
                INSERT INTO messages (
                    message_id, chat_id, date_iso, date_unixtime, from_name,
                    text, text_lemma, url
                ) VALUES (1, ?, '2024-01-01', 1704067200, 'Поговорим о ферментах',
                          ?, ?, 'https://hrtz.store/page130762566.html')
                """,
                (
                    HRTZ_CHAT_ID,
                    "Поговорим о ферментах\n\nФерменты можно заказать в hrtz.store.",
                    "поговорить о фермент фермент можно заказать hrtz store",
                ),
            )
            conn.execute(
                """
                INSERT INTO messages (
                    message_id, chat_id, date_iso, date_unixtime, from_name,
                    text, text_lemma
                ) VALUES (2, 100, '2026-01-01', 1767225600, 'Evgeny',
                          ?, ?)
                """,
                (
                    "Пошел заказывать энзим EN-06 в hrtz.store",
                    "пойти заказывать энзим en 06 hrtz store",
                ),
            )
            rebuild_fts(conn)
            conn.commit()
            conn.close()

            page = search_page(db, "Где заказать энзимы", limit=5)
            self.assertTrue(page.hits, "expected results for order query")
            labels = {h.source_label for h in page.hits}
            self.assertTrue(labels & {"сайт", "чат"})


if __name__ == "__main__":
    unittest.main()
