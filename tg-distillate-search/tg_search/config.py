"""Bot configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _parse_usernames(raw: str) -> frozenset[str]:
    names: set[str] = set()
    for part in raw.split(","):
        name = part.strip().lstrip("@").lower()
        if name:
            names.add(name)
    return frozenset(names)


@dataclass(frozen=True)
class BotConfig:
    token: str
    db_path: Path
    allowed_user_ids: frozenset[int]
    allowed_usernames: frozenset[str]
    admin_user_ids: frozenset[int]
    admin_usernames: frozenset[str]
    search_limit: int

    @classmethod
    def from_env(cls) -> BotConfig:
        token = os.environ.get("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is not set")

        raw_ids = os.environ.get("ALLOWED_USER_IDS", "").strip()
        allowed_ids = frozenset(
            int(x.strip()) for x in raw_ids.split(",") if x.strip()
        )

        raw_names = os.environ.get("ALLOWED_USERNAMES", "").strip()
        allowed_names = _parse_usernames(raw_names)

        if not allowed_ids and not allowed_names:
            raise RuntimeError(
                "Set ALLOWED_USER_IDS and/or ALLOWED_USERNAMES (comma-separated)"
            )

        raw_admin_ids = os.environ.get("ADMIN_USER_IDS", "").strip()
        admin_ids = frozenset(int(x.strip()) for x in raw_admin_ids.split(",") if x.strip())
        raw_admin_names = os.environ.get("ADMIN_USERNAMES", "").strip()
        admin_names = _parse_usernames(raw_admin_names)
        if not admin_ids and not admin_names:
            admin_ids = allowed_ids
            admin_names = allowed_names

        db_path = Path(os.environ.get("DB_PATH", "distillate.db"))
        search_limit = int(os.environ.get("SEARCH_LIMIT", "5"))

        return cls(
            token=token,
            db_path=db_path,
            allowed_user_ids=allowed_ids,
            allowed_usernames=allowed_names,
            admin_user_ids=admin_ids,
            admin_usernames=admin_names,
            search_limit=max(1, min(search_limit, 10)),
        )
