"""Tests for Telegram message formatting."""

from __future__ import annotations

import unittest

from tg_search.format import format_hits
from tg_search.search import SearchHit


class TestFormatHits(unittest.TestCase):
    def test_empty(self) -> None:
        text = format_hits([], "колонна")
        self.assertIn("ничего не найдено", text)
        self.assertIn("колонна", text)

    def test_hit_with_link(self) -> None:
        hit = SearchHit(
            id=105,
            date_iso="2022-09-27T15:33:14",
            from_name="Viktor",
            text="full text",
            reply_to_id=94,
            link="https://t.me/distillate_club_chat/105",
            snippet="[брожение] в процессе",
        )
        text = format_hits([hit], "брожение")
        self.assertIn("Viktor", text)
        self.assertIn("distillate_club_chat/105", text)
        self.assertIn("открыть в чате", text)


if __name__ == "__main__":
    unittest.main()
