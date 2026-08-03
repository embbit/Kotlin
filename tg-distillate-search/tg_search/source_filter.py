"""Resolve search scope to a Telegram source (chat / channel)."""

from __future__ import annotations

import sqlite3

from tg_search.db import list_sources

SOURCE_ALIASES = {
    "chat": "чат",
    "channel": "канал",
    "distillate_club_chat": "чат",
    "distillate_club": "канал",
}


def resolve_source(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    key = key.strip().lower().lstrip("@")
    if not key or key in {"all", "все", "*"}:
        return None

    key = SOURCE_ALIASES.get(key, key)

    for row in list_sources(conn):
        label = (row["label"] or "").lower()
        username = (row["username"] or "").lower()
        if key in {label, username}:
            return row
        if key in (row["type"] or "").lower():
            return row
    return None


def source_scope_label(source: sqlite3.Row | None) -> str | None:
    if source is None:
        return None
    return str(source["label"])
