"""Tests for bot command menu and group mention parsing."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field

from tg_search.bot_commands import query_from_mention

MENTION = "mention"


@dataclass
class FakeEntity:
    type: str
    offset: int
    length: int


@dataclass
class FakeMessage:
    text: str
    entities: list[FakeEntity] = field(default_factory=list)


class TestQueryFromMention(unittest.TestCase):
    def test_query_after_mention(self) -> None:
        msg = FakeMessage(
            text="@DistillateClubSearch_bot вишневая ратафия",
            entities=[
                FakeEntity(MENTION, 0, 25),
            ],
        )
        self.assertEqual(
            query_from_mention(msg, "DistillateClubSearch_bot"),  # type: ignore[arg-type]
            "вишневая ратафия",
        )

    def test_query_before_mention(self) -> None:
        msg = FakeMessage(
            text="вишневая @bot",
            entities=[FakeEntity(MENTION, 9, 4)],
        )
        self.assertEqual(query_from_mention(msg, "bot"), "вишневая")  # type: ignore[arg-type]

    def test_wrong_mention_ignored(self) -> None:
        msg = FakeMessage(
            text="@other вишневая",
            entities=[FakeEntity(MENTION, 0, 6)],
        )
        self.assertIsNone(query_from_mention(msg, "bot"))  # type: ignore[arg-type]

    def test_empty_query_returns_none(self) -> None:
        msg = FakeMessage(
            text="@bot",
            entities=[FakeEntity(MENTION, 0, 4)],
        )
        self.assertIsNone(query_from_mention(msg, "bot"))  # type: ignore[arg-type]

    def test_no_entities_returns_none(self) -> None:
        msg = FakeMessage(text="@bot query")
        self.assertIsNone(query_from_mention(msg, "bot"))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
