"""Tests for bot access control helpers."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from pathlib import Path

from tg_search.access import admin_user, allowed_user
from tg_search.config import BotConfig


def _cfg(**overrides) -> BotConfig:
    base = {
        "token": "t",
        "db_path": Path("x.db"),
        "allowed_user_ids": frozenset({100}),
        "allowed_usernames": frozenset({"alice"}),
        "admin_user_ids": frozenset({100}),
        "admin_usernames": frozenset({"admin"}),
        "search_limit": 5,
    }
    base.update(overrides)
    return BotConfig(**base)


@dataclass
class FakeUser:
    id: int
    username: str | None


class TestBotAccess(unittest.TestCase):
    def test_allowed_by_id(self) -> None:
        cfg = _cfg()
        self.assertTrue(allowed_user(cfg, FakeUser(100, None)))
        self.assertFalse(allowed_user(cfg, FakeUser(999, "bob")))

    def test_admin_by_username(self) -> None:
        cfg = _cfg(admin_user_ids=frozenset(), admin_usernames=frozenset({"admin"}))
        self.assertTrue(admin_user(cfg, FakeUser(1, "Admin")))
        self.assertFalse(admin_user(cfg, FakeUser(1, "alice")))

    def test_search_allowed_admin_denied(self) -> None:
        cfg = _cfg(
            allowed_user_ids=frozenset({1, 2}),
            allowed_usernames=frozenset(),
            admin_user_ids=frozenset({1}),
            admin_usernames=frozenset(),
        )
        user = FakeUser(2, None)
        self.assertTrue(allowed_user(cfg, user))
        self.assertFalse(admin_user(cfg, user))


if __name__ == "__main__":
    unittest.main()
