"""Tests for source priority in ranked search output."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tg_search.db import connect, rebuild_fts
from tg_search.external_sources import HRTZ_CHAT_ID, YOUTUBE_CHAT_ID
from tg_search.search import SearchHit, search_page
from tg_search.source_priority import source_kind, source_sort_tier


class TestSourcePriorityOrder(unittest.TestCase):
    def test_kind_order_matches_requirements(self) -> None:
        kinds = [
            source_kind(YOUTUBE_CHAT_ID, "youtube", "youtube"),
            source_kind(1, "канал", "channel"),
            source_kind(HRTZ_CHAT_ID, "сайт", "web"),
            source_kind(1, "чат", "supergroup"),
        ]
        self.assertEqual(kinds, ["youtube", "channel", "web", "chat"])

    def test_equal_score_sorts_by_source_tier(self) -> None:
        hits = [
            SearchHit(
                rowid=1,
                message_id=1,
                chat_id=1,
                source_label="чат",
                source_type="supergroup",
                date_iso="2024-01-01",
                date_unixtime=1,
                from_name="a",
                text="дистилляция бочки",
                reply_to_id=None,
                link="https://t.me/chat/1",
                snippet="s",
                score=1.0,
            ),
            SearchHit(
                rowid=2,
                message_id=2,
                chat_id=YOUTUBE_CHAT_ID,
                source_label="youtube",
                source_type="youtube",
                date_iso="2024-01-01",
                date_unixtime=2,
                from_name="b",
                text="дистилляция бочки",
                reply_to_id=None,
                link="https://www.youtube.com/watch?v=abc12345678",
                snippet="s",
                score=1.0,
            ),
            SearchHit(
                rowid=3,
                message_id=3,
                chat_id=HRTZ_CHAT_ID,
                source_label="сайт",
                source_type="web",
                date_iso="2024-01-01",
                date_unixtime=3,
                from_name="c",
                text="дистилляция бочки",
                reply_to_id=None,
                link="https://hrtz.store/page1.html",
                snippet="s",
                score=1.0,
            ),
            SearchHit(
                rowid=4,
                message_id=4,
                chat_id=2,
                source_label="канал",
                source_type="channel",
                date_iso="2024-01-01",
                date_unixtime=4,
                from_name="d",
                text="дистилляция бочки",
                reply_to_id=None,
                link="https://t.me/channel/1",
                snippet="s",
                score=1.0,
            ),
        ]
        hits.sort(
            key=lambda h: (
                -h.score,
                -source_sort_tier(h.chat_id, h.source_label, h.source_type),
                -h.date_unixtime,
            )
        )
        order = [h.source_label for h in hits]
        self.assertEqual(order, ["youtube", "канал", "сайт", "чат"])


class TestSearchDedupeIntegration(unittest.TestCase):
    def test_search_returns_one_hit_per_youtube_video(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            conn = connect(db)
            conn.execute(
                """
                INSERT INTO sources (chat_id, type, name, username, label)
                VALUES (?, 'youtube', 'YouTube', 'distillate_youtube', 'youtube')
                """,
                (YOUTUBE_CHAT_ID,),
            )
            for index, start in enumerate((0, 90, 180)):
                body = f"бочки дубовые часть {index + 1}"
                conn.execute(
                    """
                    INSERT INTO messages (
                        message_id, chat_id, date_iso, date_unixtime, from_name,
                        text, text_lemma, url
                    ) VALUES (?, ?, '2024-01-01', 1704067200, 'YouTube',
                              ?, ?, ?)
                    """,
                    (
                        1000 + index,
                        YOUTUBE_CHAT_ID,
                        body,
                        body,
                        f"https://www.youtube.com/watch?v=abc12345678&t={start}s",
                    ),
                )
            rebuild_fts(conn)
            conn.commit()
            conn.close()

            page = search_page(db, "бочки", limit=10)
            yt_links = [
                h.link
                for h in page.hits
                if h.chat_id == YOUTUBE_CHAT_ID
            ]
            self.assertEqual(len(yt_links), 1)
            self.assertIn("abc12345678", yt_links[0])


if __name__ == "__main__":
    unittest.main()
