"""Tests for search pagination."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tg_search.import_json import import_export
from tg_search.pagination import (
    get_session,
    keyboard_spec,
    next_shown,
    parse_callback,
    save_session,
)
from tg_search.search import search_page

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"
CHANNEL_FIXTURE = Path(__file__).parent / "fixtures" / "sample_channel.json"


class TestSearchPage(unittest.TestCase):
    def test_growing_limit_accumulates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")
            import_export(CHANNEL_FIXTURE, db, username="distillate_club", append=True)

            p5 = search_page(db, "колонну", limit=5, offset=0)
            p10 = search_page(db, "колонну", limit=10, offset=0)
            self.assertGreaterEqual(len(p5.hits), 1)
            if p5.has_more:
                self.assertGreater(len(p10.hits), len(p5.hits))
                self.assertEqual(
                    [h.rowid for h in p5.hits],
                    [h.rowid for h in p10.hits[: len(p5.hits)]],
                )

    def test_offset_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")
            p1 = search_page(db, "колонну", limit=1, offset=0)
            p2 = search_page(db, "колонну", limit=1, offset=1)
            if p1.has_more:
                self.assertNotEqual(p1.hits[0].rowid, p2.hits[0].rowid)


class TestPaginationHelpers(unittest.TestCase):
    def test_callback_parse(self) -> None:
        self.assertEqual(parse_callback("p:n:abcd1234"), ("next", "abcd1234"))
        self.assertEqual(parse_callback("p:s:abcd1234"), ("stop", "abcd1234"))

    def test_session(self) -> None:
        ud: dict = {}
        save_session(ud, "abc", query="test", shown=5)
        self.assertEqual(get_session(ud, "abc")["shown"], 5)
        self.assertEqual(next_shown(5, 5), 10)
        kb = keyboard_spec("abc", has_more=True)
        self.assertIsNotNone(kb)
        self.assertIsNone(keyboard_spec("abc", has_more=False))


if __name__ == "__main__":
    unittest.main()
