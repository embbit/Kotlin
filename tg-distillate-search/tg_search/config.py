"""Bot configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BotConfig:
    token: str
    db_path: Path
    allowed_user_ids: frozenset[int]
    search_limit: int

    @classmethod
    def from_env(cls) -> BotConfig:
        token = os.environ.get("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is not set")

        raw_ids = os.environ.get("ALLOWED_USER_IDS", "").strip()
        if not raw_ids:
            raise RuntimeError("ALLOWED_USER_IDS is not set (comma-separated Telegram user ids)")

        allowed = frozenset(int(x.strip()) for x in raw_ids.split(",") if x.strip())

        db_path = Path(os.environ.get("DB_PATH", "distillate.db"))
        search_limit = int(os.environ.get("SEARCH_LIMIT", "5"))

        return cls(
            token=token,
            db_path=db_path,
            allowed_user_ids=allowed,
            search_limit=max(1, min(search_limit, 10)),
        )
