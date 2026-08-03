"""Tests for search relevance filtering."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from tg_search.import_json import import_export
from tg_search.search import (
    RELEVANCE_SCORE_RATIO,
    _select_candidates,
    search_page,
)

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


@dataclass
class MockVectorIndex:
    results: list[tuple[int, float]]

    @property
    def count(self) -> int:
        return len(self.results)

    def search(self, query: str, *, limit: int = 100) -> list[tuple[int, float]]:
        return self.results[:limit]


class TestCandidateSelection(unittest.TestCase):
    def test_single_word_uses_fts_only(self) -> None:
        fts = {1: (0.9, "snippet"), 2: (0.5, "snippet")}
        vector = {99: 0.95, 1: 0.8}
        selected = _select_candidates(fts, vector, ["сухопарник"])
        self.assertEqual(selected, {1, 2})
        self.assertNotIn(99, selected)

    def test_multi_word_allows_strong_vector_only(self) -> None:
        fts = {1: (0.4, "snippet")}
        vector = {1: 0.3, 2: 0.7, 3: 0.4}
        selected = _select_candidates(fts, vector, ["как", "гнать"])
        self.assertIn(1, selected)
        self.assertIn(2, selected)
        self.assertNotIn(3, selected)


class TestSearchRelevance(unittest.TestCase):
    def test_single_word_results_all_contain_term(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")
            conn_rowids = []
            import sqlite3

            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT rowid, text FROM messages").fetchall()
            conn.close()
            if not rows:
                self.skipTest("no fixture messages")

            mock = MockVectorIndex([(int(rows[0]["rowid"]), 0.99)])
            page = search_page(db, "колонну", limit=10, offset=0, vector_index=mock)
            for hit in page.hits:
                self.assertIn("колонну", hit.text.lower())

    def test_score_ratio_constant_sane(self) -> None:
        self.assertGreater(RELEVANCE_SCORE_RATIO, 0.2)
        self.assertLess(RELEVANCE_SCORE_RATIO, 0.8)


if __name__ == "__main__":
    unittest.main()
