"""Tests for message length handling."""

from __future__ import annotations

import unittest

from tg_search.format import MAX_MESSAGE_LEN, format_hits
from tg_search.search import SearchHit


def _make_hit(i: int) -> SearchHit:
    return SearchHit(
        rowid=i,
        message_id=1000 + i,
        chat_id=1663164507,
        source_label="чат",
        date_iso="2026-01-14T12:00:00",
        date_unixtime=1768387200,
        from_name="User",
        text="x" * 500,
        reply_to_id=None,
        link=f"https://t.me/distillate_club_chat/{1000 + i}",
        snippet="[" + "сухопарник" + "] " + ("подробный текст " * 20),
    )


class TestFormatTruncation(unittest.TestCase):
    def test_stops_at_complete_results(self) -> None:
        hits = [_make_hit(i) for i in range(1, 41)]
        result = format_hits(hits, "сухопарник", show_total=True)
        self.assertLess(result.fitted, len(hits))
        self.assertTrue(result.truncated)
        self.assertLessEqual(len(result.text), MAX_MESSAGE_LEN)
        self.assertNotIn("… (обрезано)", result.text)
        self.assertIn("Лимит Telegram", result.text)
        self.assertIn("<b>1.</b>", result.text)
        self.assertNotIn("<b>41.</b>", result.text)


if __name__ == "__main__":
    unittest.main()
