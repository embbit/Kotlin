"""Integration test: enzyme site article ranks for энзимы query."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tg_search.db import connect, rebuild_fts
from tg_search.external_sources import HRTZ_CHAT_ID, YOUTUBE_CHAT_ID
from tg_search.search import search_page


class TestEnzymeSiteRanking(unittest.TestCase):
    def test_site_ferment_article_ranks_for_enzymes_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            conn = connect(db)
            conn.execute(
                """
                INSERT INTO sources (chat_id, type, name, username, label)
                VALUES (?, 'web', 'hrtz.store', 'hrtz_store', 'сайт')
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
                ) VALUES (1, ?, '2024-06-01', 1717200000, 'Поговорим о ферментах',
                          ?, ?, 'https://hrtz.store/page130762566.html')
                """,
                (
                    HRTZ_CHAT_ID,
                    "Поговорим о ферментах\n\nФерменты помогают расщеплять крахмал и пектин.",
                    "поговорим о ферментах фермент помогать расщеплять крахмал пектин",
                ),
            )
            conn.execute(
                """
                INSERT INTO messages (
                    message_id, chat_id, date_iso, date_unixtime, from_name, text, text_lemma
                ) VALUES (2, 100, '2026-06-01', 1780000000, 'User',
                          'Тут все сыпят энзимы в брагу, а я против', 'ту все сыпать энзим в брaga а я против')
                """
            )
            rebuild_fts(conn)
            conn.commit()
            conn.close()

            page = search_page(db, "энзимы", limit=5)
            self.assertTrue(page.hits)
            self.assertEqual(page.hits[0].source_label, "сайт")
            self.assertIn("page130762566", page.hits[0].link)


if __name__ == "__main__":
    unittest.main()
