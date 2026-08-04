"""Search query logging and admin statistics."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from html import escape as html_esc

from tg_search.lemmatize import lemmatize_word
from tg_search.stopwords import content_words

SEARCH_LOG_SQL = """
CREATE TABLE IF NOT EXISTS search_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT,
    query_raw TEXT NOT NULL,
    query_norm TEXT NOT NULL,
    hits_count INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_log_ts ON search_log(ts);
CREATE INDEX IF NOT EXISTS idx_search_log_user ON search_log(user_id);
CREATE INDEX IF NOT EXISTS idx_search_log_query_norm ON search_log(query_norm);
"""


def ensure_search_log(conn: sqlite3.Connection) -> None:
    conn.executescript(SEARCH_LOG_SQL)


def normalize_query(raw: str) -> str:
    words = content_words(raw, lemmatize_word)
    if words:
        return " ".join(words)
    stripped = raw.strip().lower()
    return stripped or raw.strip()


def log_search(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    username: str | None,
    query_raw: str,
    hits_count: int,
    ts: int | None = None,
) -> None:
    ensure_search_log(conn)
    query = query_raw.strip()
    if not query:
        return
    conn.execute(
        """
        INSERT INTO search_log (
            ts, user_id, username, query_raw, query_norm, hits_count
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ts if ts is not None else int(time.time()),
            user_id,
            (username or "").strip() or None,
            query,
            normalize_query(query),
            max(0, hits_count),
        ),
    )
    conn.commit()


@dataclass(frozen=True)
class SearchStatsReport:
    days: int
    total_searches: int
    unique_users: int
    top_users: list[tuple[str, int]]
    top_words: list[tuple[str, int]]
    top_queries: list[tuple[str, int]]


def _since_ts(days: int) -> int:
    return int(time.time()) - max(1, days) * 86400


def build_search_stats(conn: sqlite3.Connection, *, days: int = 30) -> SearchStatsReport:
    ensure_search_log(conn)
    since = _since_ts(days)

    summary = conn.execute(
        """
        SELECT COUNT(*) AS searches, COUNT(DISTINCT user_id) AS users
        FROM search_log
        WHERE ts >= ?
        """,
        (since,),
    ).fetchone()

    top_users_rows = conn.execute(
        """
        SELECT
            COALESCE(NULLIF(username, ''), 'id:' || user_id) AS label,
            COUNT(*) AS cnt
        FROM search_log
        WHERE ts >= ?
        GROUP BY user_id
        ORDER BY cnt DESC, label
        LIMIT 10
        """,
        (since,),
    ).fetchall()

    word_rows = conn.execute(
        """
        SELECT query_norm
        FROM search_log
        WHERE ts >= ?
        """,
        (since,),
    ).fetchall()
    word_counts: dict[str, int] = {}
    for row in word_rows:
        for word in str(row["query_norm"]).split():
            if len(word) < 2:
                continue
            word_counts[word] = word_counts.get(word, 0) + 1
    top_words = sorted(word_counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    top_query_rows = conn.execute(
        """
        SELECT query_raw, COUNT(*) AS cnt
        FROM search_log
        WHERE ts >= ?
        GROUP BY LOWER(TRIM(query_raw))
        ORDER BY cnt DESC, query_raw
        LIMIT 10
        """,
        (since,),
    ).fetchall()

    return SearchStatsReport(
        days=days,
        total_searches=int(summary["searches"] or 0),
        unique_users=int(summary["users"] or 0),
        top_users=[(str(row["label"]), int(row["cnt"])) for row in top_users_rows],
        top_words=top_words,
        top_queries=[(str(row["query_raw"]), int(row["cnt"])) for row in top_query_rows],
    )


def format_search_stats(report: SearchStatsReport) -> str:
    lines = [
        f"<b>Поиск за {report.days} дн.</b>",
        f"Запросов: <b>{report.total_searches}</b> · "
        f"Пользователей: <b>{report.unique_users}</b>",
    ]

    if report.total_searches == 0:
        lines.append("\nПока нет данных.")
        return "\n".join(lines)

    lines.append("\n<b>Топ пользователей:</b>")
    if report.top_users:
        for label, count in report.top_users:
            if label.startswith("id:"):
                user = html_esc(label)
            else:
                user = f"@{html_esc(label)}"
            lines.append(f"• {user} — {count}")
    else:
        lines.append("• —")

    lines.append("\n<b>Топ слов:</b>")
    if report.top_words:
        for word, count in report.top_words:
            lines.append(f"• {html_esc(word)} — {count}")
    else:
        lines.append("• —")

    lines.append("\n<b>Топ запросов:</b>")
    if report.top_queries:
        for query, count in report.top_queries:
            lines.append(f"• «{html_esc(query)}» — {count}×")
    else:
        lines.append("• —")

    return "\n".join(lines)
