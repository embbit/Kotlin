"""Build outbound links for indexed documents."""

from __future__ import annotations

import sqlite3

from tg_search.import_json import message_link


def hit_link(row: sqlite3.Row) -> str:
    url = row["url"] if "url" in row.keys() else None
    if url:
        return str(url)
    return message_link(row["username"], int(row["chat_id"]), int(row["message_id"]))
