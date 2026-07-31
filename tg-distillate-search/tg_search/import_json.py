"""Import Telegram Desktop JSON export into SQLite."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterator

from tg_search.db import connect, rebuild_fts, set_meta
from tg_search.text import flatten_text

BATCH_SIZE = 2000


def message_link(username: str | None, chat_id: int, message_id: int) -> str:
    if username:
        return f"https://t.me/{username.lstrip('@')}/{message_id}"
    return f"https://t.me/c/{chat_id}/{message_id}"


def iter_message_rows(
    export: dict[str, Any],
) -> Iterator[tuple[Any, ...]]:
    chat_id = int(export["id"])
    for raw in export.get("messages", []):
        if raw.get("type") != "message":
            continue
        text = flatten_text(raw.get("text"))
        if not text:
            continue

        edited = raw.get("edited_unixtime")
        yield (
            int(raw["id"]),
            chat_id,
            int(raw["date_unixtime"]),
            raw.get("date", ""),
            raw.get("from"),
            raw.get("from_id"),
            raw.get("reply_to_message_id"),
            text,
            int(edited) if edited else None,
        )


def import_export(
    json_path: Path,
    db_path: Path,
    *,
    username: str | None = "distillate_club_chat",
    replace: bool = False,
) -> dict[str, int]:
    if replace and db_path.exists():
        db_path.unlink()

    started = time.perf_counter()
    with json_path.open(encoding="utf-8") as fh:
        export = json.load(fh)

    chat_id = int(export["id"])
    chat_name = export.get("name", "")

    conn = connect(db_path)
    try:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM chat_meta")

        set_meta(conn, "chat_id", str(chat_id))
        set_meta(conn, "chat_name", chat_name)
        set_meta(conn, "chat_type", export.get("type", ""))
        if username:
            set_meta(conn, "username", username.lstrip("@"))
        set_meta(conn, "source_json", str(json_path.resolve()))
        set_meta(conn, "imported_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

        insert_sql = """
            INSERT OR REPLACE INTO messages (
                id, chat_id, date_unixtime, date_iso, from_name, from_id,
                reply_to_id, text, edited_unixtime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        batch: list[tuple[Any, ...]] = []
        imported = 0
        skipped = 0

        for row in iter_message_rows(export):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                conn.executemany(insert_sql, batch)
                imported += len(batch)
                batch.clear()
                print(f"  imported {imported:,} messages...", flush=True)

        if batch:
            conn.executemany(insert_sql, batch)
            imported += len(batch)

        skipped = len(export.get("messages", [])) - imported

        print("  rebuilding FTS index...", flush=True)
        rebuild_fts(conn)
        conn.commit()

        elapsed = time.perf_counter() - started
        stats = {
            "imported": imported,
            "skipped": skipped,
            "total_in_json": len(export.get("messages", [])),
            "elapsed_sec": round(elapsed, 1),
        }
        set_meta(conn, "message_count", str(imported))
        conn.commit()
        return stats
    finally:
        conn.close()
