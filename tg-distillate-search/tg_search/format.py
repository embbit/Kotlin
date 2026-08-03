"""Format search results for Telegram messages."""

from __future__ import annotations

import html

from tg_search.search import SearchHit

MAX_MESSAGE_LEN = 4000
MAX_SNIPPET_LEN = 280


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def format_hits(hits: list[SearchHit], query: str) -> str:
    if not hits:
        return f"По запросу «{_esc(query)}» ничего не найдено."

    lines = [f"Найдено: <b>{len(hits)}</b> · «{_esc(query)}»", ""]
    for i, hit in enumerate(hits, 1):
        author = _esc(hit.from_name or "Unknown")
        date = _esc(hit.date_iso[:10])
        snippet = _esc(hit.snippet)
        if len(snippet) > MAX_SNIPPET_LEN:
            snippet = snippet[: MAX_SNIPPET_LEN - 1] + "…"
        lines.append(f"<b>{i}.</b> [{_esc(hit.source_label)}] {date} — {author}")
        lines.append(snippet)
        lines.append(f'<a href="{hit.link}">открыть</a>')
        lines.append("")

    text = "\n".join(lines).strip()
    if len(text) > MAX_MESSAGE_LEN:
        text = text[: MAX_MESSAGE_LEN - 20].rstrip() + "\n\n… (обрезано)"
    return text
