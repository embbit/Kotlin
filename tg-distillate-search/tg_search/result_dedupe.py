"""Collapse chunked external documents to one hit per parent item."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tg_search.external_sources import HRTZ_CHAT_ID, YOUTUBE_CHAT_ID

if TYPE_CHECKING:
    from tg_search.search import SearchHit

YOUTUBE_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?(?:[^#]*&)?v=|youtu\.be/)([A-Za-z0-9_-]{11})"
)


def hit_dedupe_key(hit: SearchHit) -> str:
    if hit.chat_id == YOUTUBE_CHAT_ID:
        match = YOUTUBE_VIDEO_ID_RE.search(hit.link)
        if match:
            return f"yt:{match.group(1)}"
    if hit.chat_id == HRTZ_CHAT_ID:
        return f"web:{hit.link.split('#', 1)[0]}"
    return f"tg:{hit.chat_id}:{hit.message_id}"


def dedupe_search_hits(hits: list[SearchHit]) -> list[SearchHit]:
    """Keep the first (best-scored) hit for each parent document."""
    seen: set[str] = set()
    unique: list[SearchHit] = []
    for hit in hits:
        key = hit_dedupe_key(hit)
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique
