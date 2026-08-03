"""Import Telegram Desktop JSON export into SQLite."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterator

from tg_search.db import connect, count_messages, list_sources, rebuild_fts, set_meta
from tg_search.lemmatize import lemmatize_text
from tg_search.lemmas import META_LEMMAS_INDEXED, fts_uses_lemmas, rebuild_lemma_fts
from tg_search.text import flatten_text

BATCH_SIZE = 2000


def default_label(export_type: str) -> str:
    if "channel" in export_type:
        return "канал"
    if "group" in export_type or "chat" in export_type:
        return "чат"
    return "источник"


def message_link(username: str | None, chat_id: int, message_id: int) -> str:
    if username:
        return f"https://t.me/{username.lstrip('@')}/{message_id}"
    return f"https://t.me/c/{chat_id}/{message_id}"


def iter_message_rows(
    export: dict[str, Any],
    chat_id: int,
) -> Iterator[tuple[Any, ...]]:
    for raw in export.get("messages", []):
        if raw.get("type") != "message":
            continue
        text = flatten_text(raw.get("text"))
        if not text:
            continue

        edited = raw.get("edited_unixtime")
        yield (
            chat_id,
            int(raw["id"]),
            int(raw["date_unixtime"]),
            raw.get("date", ""),
            raw.get("from"),
            raw.get("from_id"),
            raw.get("reply_to_message_id"),
            text,
            lemmatize_text(text),
            int(edited) if edited else None,
        )


def import_export(
    json_path: Path,
    db_path: Path,
    *,
    username: str | None = None,
    replace: bool = False,
    append: bool = False,
) -> dict[str, int | str | float]:
    if replace and db_path.exists():
        db_path.unlink()

    started = time.perf_counter()
    with json_path.open(encoding="utf-8") as fh:
        export = json.load(fh)

    chat_id = int(export["id"])
    chat_name = export.get("name", "")
    chat_type = export.get("type", "")
    label = default_label(chat_type)

    conn = connect(db_path)
    try:
        existing_count = count_messages(conn)
        if existing_count and not append and not replace:
            raise RuntimeError(
                "Database already has messages. Use --append to add a source "
                "or --replace to rebuild from scratch."
            )

        conn.execute(
            """
            INSERT INTO sources(chat_id, name, type, username, label)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                username = excluded.username,
                label = excluded.label
            """,
            (chat_id, chat_name, chat_type, username.lstrip("@") if username else None, label),
        )

        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))

        insert_sql = """
            INSERT INTO messages (
                chat_id, message_id, date_unixtime, date_iso, from_name, from_id,
                reply_to_id, text, text_lemma, edited_unixtime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        batch: list[tuple[Any, ...]] = []
        imported = 0

        for row in iter_message_rows(export, chat_id):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                conn.executemany(insert_sql, batch)
                imported += len(batch)
                batch.clear()
                print(f"  [{label}] imported {imported:,} messages...", flush=True)

        if batch:
            conn.executemany(insert_sql, batch)
            imported += len(batch)

        skipped = len(export.get("messages", [])) - imported

        print(f"  [{label}] rebuilding FTS index...", flush=True)
        if fts_uses_lemmas(conn):
            rebuild_fts(conn)
            set_meta(conn, META_LEMMAS_INDEXED, "1")
        else:
            rebuild_lemma_fts(conn)

        set_meta(conn, "imported_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        set_meta(conn, "message_count", str(count_messages(conn)))
        set_meta(conn, "last_import", f"{label}:{json_path.name}")
        conn.commit()

        elapsed = time.perf_counter() - started
        return {
            "imported": imported,
            "skipped": skipped,
            "total_in_json": len(export.get("messages", [])),
            "source": label,
            "chat_id": chat_id,
            "elapsed_sec": round(elapsed, 1),
            "total_in_db": count_messages(conn),
        }
    finally:
        conn.close()
