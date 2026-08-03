"""Tests for bot configuration."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from tg_search.config import BotConfig


class TestBotConfig(unittest.TestCase):
    def test_usernames_only(self) -> None:
        env = {
            "BOT_TOKEN": "test:token",
            "ALLOWED_USER_IDS": "",
            "ALLOWED_USERNAMES": "@embbit, Other",
            "DB_PATH": "distillate.db",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = BotConfig.from_env()
        self.assertEqual(cfg.allowed_usernames, frozenset({"embbit", "other"}))
        self.assertEqual(cfg.allowed_user_ids, frozenset())


if __name__ == "__main__":
    unittest.main()
