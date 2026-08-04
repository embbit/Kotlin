"""Synthetic Telegram sources for web and YouTube documents."""

from __future__ import annotations

import hashlib

HRTZ_CHAT_ID = -900_001
HRTZ_CATALOG_CHAT_ID = -900_003
YOUTUBE_CHAT_ID = -900_002

HRTZ_BASE_URL = "https://hrtz.store"
HRTZ_SITEMAP_URL = f"{HRTZ_BASE_URL}/sitemap.xml"
HRTZ_ARTICLE_PATH_RE = r"/page\d+\.html$"
HRTZ_CATALOG_PAGE_URL = f"{HRTZ_BASE_URL}/catalog"
HRTZ_CATALOG_RECID = "1102118231"

YOUTUBE_CHANNEL_ID = "UCFq7cnR71qNv14x0LSTbbdA"
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@DistillateClub"
YOUTUBE_RSS_URL = (
    f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
)

META_SOURCES_UPDATED_AT = "external_sources_updated_at"
META_HRTZ_ARTICLE_COUNT = "hrtz_article_count"
META_HRTZ_CATALOG_COUNT = "hrtz_catalog_count"
META_YOUTUBE_VIDEO_COUNT = "youtube_video_count"


def stable_message_id(key: str) -> int:
    digest = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def chunk_message_id(parent_key: str, chunk_index: int) -> int:
    return stable_message_id(f"{parent_key}#{chunk_index}")
