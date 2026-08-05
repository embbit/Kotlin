"""Tests for deduplicating chunked search hits."""

from __future__ import annotations

import unittest

from tg_search.external_sources import HRTZ_CHAT_ID, YOUTUBE_CHAT_ID
from tg_search.result_dedupe import dedupe_search_hits, hit_dedupe_key
from tg_search.search import SearchHit


def _hit(
    *,
    rowid: int,
    chat_id: int = YOUTUBE_CHAT_ID,
    link: str,
    score: float,
    source_label: str = "youtube",
    source_type: str | None = "youtube",
) -> SearchHit:
    return SearchHit(
        rowid=rowid,
        message_id=rowid,
        chat_id=chat_id,
        source_label=source_label,
        source_type=source_type,
        date_iso="2024-01-01",
        date_unixtime=1704067200,
        from_name="Test",
        text="sample",
        reply_to_id=None,
        link=link,
        snippet="sample",
        score=score,
    )


class TestResultDedupe(unittest.TestCase):
    def test_youtube_key_ignores_timestamp(self) -> None:
        hit = _hit(
            rowid=1,
            link="https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s",
            score=1.0,
        )
        self.assertEqual(hit_dedupe_key(hit), "yt:dQw4w9WgXcQ")

    def test_dedupe_keeps_best_youtube_chunk(self) -> None:
        hits = [
            _hit(
                rowid=1,
                link="https://www.youtube.com/watch?v=abc12345678&t=0s",
                score=0.9,
            ),
            _hit(
                rowid=2,
                link="https://www.youtube.com/watch?v=abc12345678&t=90s",
                score=0.8,
            ),
            _hit(
                rowid=3,
                link="https://www.youtube.com/watch?v=xyz98765432&t=0s",
                score=0.7,
            ),
        ]
        deduped = dedupe_search_hits(hits)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].rowid, 1)
        self.assertEqual(deduped[1].rowid, 3)

    def test_web_dedupe_by_article_url(self) -> None:
        hits = [
            _hit(
                rowid=1,
                chat_id=HRTZ_CHAT_ID,
                source_label="сайт",
                source_type="web",
                link="https://hrtz.store/page1.html#chunk-1",
                score=0.9,
            ),
            _hit(
                rowid=2,
                chat_id=HRTZ_CHAT_ID,
                source_label="сайт",
                source_type="web",
                link="https://hrtz.store/page1.html#chunk-2",
                score=0.85,
            ),
        ]
        self.assertEqual(len(dedupe_search_hits(hits)), 1)

    def test_telegram_messages_not_deduped(self) -> None:
        hits = [
            _hit(
                rowid=1,
                chat_id=100,
                source_label="чат",
                source_type="supergroup",
                link="https://t.me/chat/1",
                score=0.9,
            ),
            _hit(
                rowid=2,
                chat_id=100,
                source_label="чат",
                source_type="supergroup",
                link="https://t.me/chat/2",
                score=0.8,
            ),
        ]
        self.assertEqual(len(dedupe_search_hits(hits)), 2)


if __name__ == "__main__":
    unittest.main()
