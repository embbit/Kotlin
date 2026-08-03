"""Pagination session helpers for the Telegram bot."""

from __future__ import annotations

import secrets
from typing import Any

SESSIONS_KEY = "search_sessions"
CALLBACK_NEXT = "p:n:"
CALLBACK_STOP = "p:s:"


def new_session_id() -> str:
    return secrets.token_hex(4)


def save_session(
    user_data: dict[str, Any],
    session_id: str,
    *,
    query: str,
    shown: int,
) -> None:
    sessions = user_data.setdefault(SESSIONS_KEY, {})
    sessions[session_id] = {"query": query, "shown": shown}
    if len(sessions) > 5:
        oldest = next(iter(sessions))
        del sessions[oldest]


def get_session(user_data: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    return user_data.get(SESSIONS_KEY, {}).get(session_id)


def clear_sessions(user_data: dict[str, Any]) -> None:
    user_data.pop(SESSIONS_KEY, None)


def parse_callback(data: str) -> tuple[str, str] | None:
    if data.startswith(CALLBACK_NEXT):
        return ("next", data[len(CALLBACK_NEXT) :])
    if data.startswith(CALLBACK_STOP):
        return ("stop", data[len(CALLBACK_STOP) :])
    return None


def keyboard_spec(session_id: str, *, has_more: bool) -> list[list[tuple[str, str]]] | None:
    """Return inline keyboard rows as (label, callback_data) — built in bot layer."""
    if not has_more:
        return None
    return [
        [
            ("Дальше ➡️", f"{CALLBACK_NEXT}{session_id}"),
            ("Стоп", f"{CALLBACK_STOP}{session_id}"),
        ]
    ]


def next_shown(current_shown: int, page_size: int) -> int:
    return current_shown + page_size
