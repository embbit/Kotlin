"""Format search results for Telegram messages."""

from __future__ import annotations

import html
from dataclasses import dataclass

from tg_search.search import SearchHit

MAX_MESSAGE_LEN = 4000
MAX_SNIPPET_LEN = 280


@dataclass(frozen=True)
class FormatResult:
    text: str
    fitted: int
    truncated: bool


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def _hit_block(hit: SearchHit, index: int) -> list[str]:
    author = _esc(hit.from_name or "Unknown")
    date = _esc(hit.date_iso[:10])
    snippet = _esc(hit.snippet)
    if len(snippet) > MAX_SNIPPET_LEN:
        snippet = snippet[: MAX_SNIPPET_LEN - 1] + "…"
    return [
        f"<b>{index}.</b> [{_esc(hit.source_label)}] {date} — {author}",
        snippet,
        f'<a href="{hit.link}">открыть</a>',
        "",
    ]


def format_hits(
    hits: list[SearchHit],
    query: str,
    *,
    start_index: int = 1,
    page: int = 1,
    show_total: bool = False,
    continuation: bool = False,
    scope: str | None = None,
) -> FormatResult:
    if not hits:
        empty = f"По запросу «{_esc(query)}» ничего не найдено."
        if scope:
            empty += f" ({_esc(scope)})"
        return FormatResult(text=empty, fitted=0, truncated=False)

    scope_suffix = f" · {_esc(scope)}" if scope else ""
    if continuation:
        lines = [f"«{_esc(query)}»{scope_suffix} · продолжение", ""]
    elif show_total:
        lines = [f"«{_esc(query)}»{scope_suffix} · показано <b>{len(hits)}</b>", ""]
    elif page > 1:
        lines = [f"«{_esc(query)}»{scope_suffix} · стр. <b>{page}</b>", ""]
    else:
        lines = [f"«{_esc(query)}»{scope_suffix}", ""]

    fitted = 0
    reserve = 80 if len(hits) > 3 else 20
    for i, hit in enumerate(hits, start_index):
        block = _hit_block(hit, i)
        candidate = "\n".join(lines + block).strip()
        if fitted > 0 and len(candidate) > MAX_MESSAGE_LEN - reserve:
            break
        lines.extend(block)
        fitted += 1

    if continuation and fitted > 0:
        end_index = start_index + fitted - 1
        header = (
            f"«{_esc(query)}» · <b>{start_index}</b>"
            if fitted == 1
            else f"«{_esc(query)}» · <b>{start_index}–{end_index}</b>"
        )
        lines[0] = header

    return FormatResult(
        text="\n".join(lines).strip(),
        fitted=fitted,
        truncated=fitted < len(hits),
    )


def split_hits_to_messages(
    hits: list[SearchHit],
    query: str,
    *,
    start_index: int = 1,
    scope: str | None = None,
) -> list[FormatResult]:
    """Split hits into one or more Telegram-sized message chunks."""
    if not hits:
        return [format_hits([], query, scope=scope)]

    chunks: list[FormatResult] = []
    remaining = hits
    idx = start_index
    first = True
    while remaining:
        chunk = format_hits(
            remaining,
            query,
            start_index=idx,
            continuation=not first,
            scope=scope if first else scope,
        )
        chunks.append(chunk)
        if not chunk.truncated:
            break
        remaining = remaining[chunk.fitted :]
        idx += chunk.fitted
        first = False
    return chunks
