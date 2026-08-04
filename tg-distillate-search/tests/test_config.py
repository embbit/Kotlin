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
        self.assertEqual(cfg.admin_usernames, cfg.allowed_usernames)
        self.assertEqual(cfg.admin_user_ids, cfg.allowed_user_ids)

    def test_admin_lists_separate(self) -> None:
        env = {
            "BOT_TOKEN": "test:token",
            "ALLOWED_USER_IDS": "1,2",
            "ALLOWED_USERNAMES": "user1,user2",
            "ADMIN_USER_IDS": "1",
            "ADMIN_USERNAMES": "admin1",
            "DB_PATH": "distillate.db",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = BotConfig.from_env()
        self.assertEqual(cfg.allowed_user_ids, frozenset({1, 2}))
        self.assertEqual(cfg.admin_user_ids, frozenset({1}))
        self.assertEqual(cfg.admin_usernames, frozenset({"admin1"}))


if __name__ == "__main__":
    unittest.main()
