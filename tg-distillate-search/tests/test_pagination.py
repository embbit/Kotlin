"""Tests for search pagination."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tg_search.import_json import import_export
from tg_search.pagination import keyboard_spec, parse_callback, save_session, get_session
from tg_search.search import search_page

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"
CHANNEL_FIXTURE = Path(__file__).parent / "fixtures" / "sample_channel.json"


class TestSearchPage(unittest.TestCase):
    def test_offset_pagination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")
            import_export(CHANNEL_FIXTURE, db, username="distillate_club", append=True)

            p1 = search_page(db, "колонну", limit=1, offset=0)
            p2 = search_page(db, "колонну", limit=1, offset=1)
            self.assertEqual(len(p1.hits), 1)
            if p1.has_more:
                self.assertEqual(len(p2.hits), 1)
                self.assertNotEqual(p1.hits[0].rowid, p2.hits[0].rowid)


class TestPaginationHelpers(unittest.TestCase):
    def test_callback_parse(self) -> None:
        self.assertEqual(parse_callback("p:n:abcd1234"), ("next", "abcd1234"))
        self.assertEqual(parse_callback("p:s:abcd1234"), ("stop", "abcd1234"))

    def test_session(self) -> None:
        ud: dict = {}
        save_session(ud, "abc", query="test", offset=5)
        self.assertEqual(get_session(ud, "abc")["query"], "test")
        kb = keyboard_spec("abc", has_more=True)
        self.assertIsNotNone(kb)
        self.assertIsNone(keyboard_spec("abc", has_more=False))


if __name__ == "__main__":
    unittest.main()
