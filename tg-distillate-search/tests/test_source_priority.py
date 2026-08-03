"""Tests for source priority ranking."""

from __future__ import annotations

import unittest

from tg_search.external_sources import HRTZ_CHAT_ID, YOUTUBE_CHAT_ID
from tg_search.source_priority import (
    SOURCE_KIND_CHANNEL,
    SOURCE_KIND_CHAT,
    SOURCE_KIND_WEB,
    SOURCE_KIND_YOUTUBE,
    source_kind,
    source_score_boost,
    source_sort_tier,
)


class TestSourcePriority(unittest.TestCase):
    def test_kinds(self) -> None:
        self.assertEqual(source_kind(YOUTUBE_CHAT_ID, "youtube"), SOURCE_KIND_YOUTUBE)
        self.assertEqual(source_kind(HRTZ_CHAT_ID, "сайт"), SOURCE_KIND_WEB)
        self.assertEqual(source_kind(1, "канал", "channel"), SOURCE_KIND_CHANNEL)
        self.assertEqual(source_kind(2, "чат", "supergroup"), SOURCE_KIND_CHAT)

    def test_boost_order(self) -> None:
        yt = source_score_boost(YOUTUBE_CHAT_ID, "youtube")
        ch = source_score_boost(1663164507, "канал", "channel")
        web = source_score_boost(HRTZ_CHAT_ID, "сайт")
        chat = source_score_boost(1663164507, "чат", "supergroup")
        self.assertGreater(yt, web)
        self.assertGreater(web, ch)
        self.assertGreater(ch, chat)

    def test_sort_tier_order(self) -> None:
        tiers = [
            source_sort_tier(YOUTUBE_CHAT_ID, "youtube"),
            source_sort_tier(HRTZ_CHAT_ID, "сайт"),
            source_sort_tier(1, "канал", "channel"),
            source_sort_tier(1, "чат", "supergroup"),
        ]
        self.assertEqual(tiers, sorted(tiers, reverse=True))


if __name__ == "__main__":
    unittest.main()
