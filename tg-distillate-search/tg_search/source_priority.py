"""Source priority for mixed search results."""

from __future__ import annotations

from tg_search.external_sources import HRTZ_CATALOG_CHAT_ID, HRTZ_CHAT_ID, YOUTUBE_CHAT_ID

SOURCE_KIND_YOUTUBE = "youtube"
SOURCE_KIND_CHANNEL = "channel"
SOURCE_KIND_WEB = "web"
SOURCE_KIND_CHAT = "chat"

# Higher boost → higher in results when relevance is comparable.
SOURCE_SCORE_BOOST = {
    SOURCE_KIND_YOUTUBE: 1.18,
    SOURCE_KIND_WEB: 1.12,
    SOURCE_KIND_CHANNEL: 1.06,
    SOURCE_KIND_CHAT: 1.0,
}

SOURCE_SORT_TIER = {
    SOURCE_KIND_YOUTUBE: 4,
    SOURCE_KIND_WEB: 3,
    SOURCE_KIND_CHANNEL: 2,
    SOURCE_KIND_CHAT: 1,
}


def source_kind(
    chat_id: int,
    source_label: str,
    source_type: str | None = None,
) -> str:
    if chat_id == YOUTUBE_CHAT_ID:
        return SOURCE_KIND_YOUTUBE
    if chat_id in (HRTZ_CHAT_ID, HRTZ_CATALOG_CHAT_ID):
        return SOURCE_KIND_WEB

    label = (source_label or "").lower()
    stype = (source_type or "").lower()

    if label == "youtube" or stype == "youtube":
        return SOURCE_KIND_YOUTUBE
    if label in {"сайт", "каталог"} or stype == "web":
        return SOURCE_KIND_WEB
    if "канал" in label or "channel" in stype:
        return SOURCE_KIND_CHANNEL
    if "чат" in label or "group" in stype or "supergroup" in stype:
        return SOURCE_KIND_CHAT
    return SOURCE_KIND_CHAT


def source_score_boost(
    chat_id: int,
    source_label: str,
    source_type: str | None = None,
) -> float:
    return SOURCE_SCORE_BOOST[source_kind(chat_id, source_label, source_type)]


def source_sort_tier(
    chat_id: int,
    source_label: str,
    source_type: str | None = None,
) -> int:
    return SOURCE_SORT_TIER[source_kind(chat_id, source_label, source_type)]
