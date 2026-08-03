"""Tests for hybrid scoring and recency."""

from __future__ import annotations

import math
import time
import unittest

from tg_search.search import _recency_score


class TestRecency(unittest.TestCase):
    def test_recent_scores_higher(self) -> None:
        now = int(time.time())
        old = _recency_score(now - 365 * 86400, now)
        recent = _recency_score(now - 7 * 86400, now)
        self.assertGreater(recent, old)

    def test_decay_at_scale(self) -> None:
        now = int(time.time())
        at_scale = _recency_score(now - 90 * 86400, now)
        self.assertAlmostEqual(at_scale, math.exp(-1), places=3)


if __name__ == "__main__":
    unittest.main()
