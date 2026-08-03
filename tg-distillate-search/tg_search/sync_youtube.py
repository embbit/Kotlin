"""Sync YouTube channel videos into the search database."""

from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape

from tg_search.external_sources import (
    META_YOUTUBE_VIDEO_COUNT,
    YOUTUBE_CHANNEL_ID,
    YOUTUBE_CHANNEL_URL,
    YOUTUBE_CHAT_ID,
    YOUTUBE_RSS_URL,
    chunk_message_id,
)
from tg_search.sync_common import (
    DocumentChunk,
    content_hash,
    document_unchanged,
    ensure_source,
    upsert_chunks,
)
from tg_search.db import set_meta

USER_AGENT = (
    "Mozilla/5.0 (compatible; DistillateSearchBot/1.0; +https://github.com/embbit/Kotlin)"
)
CHAPTER_RE = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)")
SEGMENT_SECONDS = 90
MIN_LONG_VIDEO_SECONDS = 120


@dataclass(frozen=True)
class YouTubeVideo:
    video_id: str
    title: str
    published_unixtime: int
    published_iso: str
    description: str


def _fetch(url: str, *, timeout: float = 60.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _parse_duration_seconds(iso_duration: str | None) -> int | None:
    if not iso_duration:
        return None
    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        iso_duration,
    )
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _video_duration_seconds(video_id: str) -> int | None:
    url = (
        "https://www.youtube.com/oembed"
        f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
    )
    try:
        data = json.loads(_fetch(url).decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
    # oembed does not expose duration; use watch page marker
    try:
        html = _fetch(f"https://www.youtube.com/watch?v={video_id}").decode(
            "utf-8", errors="replace"
        )
    except (urllib.error.URLError, TimeoutError):
        return None
    match = re.search(r'"lengthSeconds":"(\d+)"', html)
    if match:
        return int(match.group(1))
    return None


def videos_from_rss(rss_url: str = YOUTUBE_RSS_URL) -> list[YouTubeVideo]:
    root = ET.fromstring(_fetch(rss_url))
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    videos: list[YouTubeVideo] = []
    for entry in root.findall("atom:entry", ns):
        video_id = entry.find("yt:videoId", ns)
        title = entry.find("atom:title", ns)
        published = entry.find("atom:published", ns)
        desc = entry.find("media:group/media:description", ns)
        if video_id is None or title is None or published is None:
            continue
        pub_text = published.text or ""
        pub_unix = int(time.mktime(time.strptime(pub_text[:19], "%Y-%m-%dT%H:%M:%S")))
        videos.append(
            YouTubeVideo(
                video_id=video_id.text or "",
                title=unescape(title.text or ""),
                published_unixtime=pub_unix,
                published_iso=pub_text[:10],
                description=unescape(desc.text or "") if desc is not None else "",
            )
        )
    return videos


def list_channel_video_ids(channel_url: str = YOUTUBE_CHANNEL_URL) -> list[str]:
    html = _fetch(f"{channel_url}/videos").decode("utf-8", errors="replace")
    return sorted(set(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)))


def _seconds_from_timestamp(ts: str) -> int:
    parts = [int(x) for x in ts.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def _chapters_from_description(description: str) -> list[tuple[int, str, str]]:
    chapters: list[tuple[int, str, str]] = []
    for ts, title in CHAPTER_RE.findall(description):
        start = _seconds_from_timestamp(ts)
        chapters.append((start, title.strip(), ts))
    return chapters


def _transcript_segments(video_id: str) -> list[tuple[int, str]]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return []

    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id, languages=["ru", "ru-RU", "en"])
    except Exception:
        return []

    snippets = transcript.snippets if hasattr(transcript, "snippets") else transcript
    segments: list[tuple[int, str]] = []
    for item in snippets:
        if hasattr(item, "start"):
            start = int(item.start)
            text = item.text
        else:
            start = int(item["start"])
            text = item["text"]
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            segments.append((start, text))
    return segments


def _chunks_from_transcript(
    video: YouTubeVideo,
    segments: list[tuple[int, str]],
) -> list[tuple[int, str, str]]:
    if not segments:
        return []

    chunks: list[tuple[int, str, str]] = []
    current_start = segments[0][0]
    current_parts: list[str] = []
    current_len = 0

    for start, text in segments:
        if current_parts and current_len + len(text) > 900:
            body = " ".join(current_parts).strip()
            chunks.append((current_start, body, _format_timestamp(current_start)))
            current_start = start
            current_parts = [text]
            current_len = len(text)
        else:
            if not current_parts:
                current_start = start
            current_parts.append(text)
            current_len += len(text) + 1

    if current_parts:
        body = " ".join(current_parts).strip()
        chunks.append((current_start, body, _format_timestamp(current_start)))
    return chunks


def _format_timestamp(seconds: int) -> str:
    minutes, sec = divmod(max(0, seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes}:{sec:02d}"


def _chunks_from_description(video: YouTubeVideo) -> list[tuple[int, str, str]]:
    chapters = _chapters_from_description(video.description)
    if not chapters:
        intro = video.description.strip()
        if len(intro) > 80:
            return [(0, intro[:2000], "0:00")]
        return []

    chunks: list[tuple[int, str, str]] = []
    desc_lines = video.description.splitlines()
    for index, (start, title, ts) in enumerate(chapters):
        end = chapters[index + 1][0] if index + 1 < len(chapters) else None
        body_parts = [title]
        for line in desc_lines:
            if line.strip().startswith(ts):
                continue
            if any(line.strip().startswith(other_ts) for other_ts, _ in CHAPTER_RE.findall(line)):
                continue
        text = f"{video.title}\n\n{title}"
        chunks.append((start, text, ts))
    return chunks


def build_video_chunks(video: YouTubeVideo) -> list[tuple[int, str, str]]:
    segments = _transcript_segments(video.video_id)
    if segments:
        return _chunks_from_transcript(video, segments)
    return _chunks_from_description(video)


def sync_youtube_channel(
    conn: sqlite3.Connection,
    *,
    include_shorts: bool = False,
) -> dict[str, int]:
    ensure_source(
        conn,
        chat_id=YOUTUBE_CHAT_ID,
        name="Distillate Club",
        source_type="youtube",
        label="youtube",
        username="DistillateClub",
    )

    rss_videos = {v.video_id: v for v in videos_from_rss()}
    video_ids = list_channel_video_ids()
    if not video_ids:
        video_ids = list(rss_videos)

    indexed_videos = 0
    indexed_chunks = 0
    skipped = 0
    skipped_shorts = 0
    errors = 0

    for video_id in video_ids:
        video = rss_videos.get(video_id)
        if video is None:
            try:
                html = _fetch(f"https://www.youtube.com/watch?v={video_id}").decode(
                    "utf-8", errors="replace"
                )
                title_match = re.search(r'"title":"([^"]{5,200})"', html)
                title = unescape(title_match.group(1)) if title_match else video_id
            except (urllib.error.URLError, TimeoutError):
                errors += 1
                continue
            now = int(time.time())
            video = YouTubeVideo(
                video_id=video_id,
                title=title,
                published_unixtime=now,
                published_iso=time.strftime("%Y-%m-%d", time.gmtime(now)),
                description="",
            )

        duration = _video_duration_seconds(video_id)
        if duration is not None and duration < MIN_LONG_VIDEO_SECONDS and not include_shorts:
            skipped_shorts += 1
            continue

        raw_chunks = build_video_chunks(video)
        if not raw_chunks:
            errors += 1
            continue

        doc_hash = content_hash(
            video.title + "\n" + video.description + "\n".join(c[1] for c in raw_chunks)
        )
        if document_unchanged(conn, YOUTUBE_CHAT_ID, video.video_id, doc_hash):
            skipped += 1
            continue

        doc_chunks: list[DocumentChunk] = []
        for index, (start_sec, body, ts_label) in enumerate(raw_chunks):
            url = f"https://www.youtube.com/watch?v={video.video_id}&t={max(0, start_sec)}s"
            text = f"{video.title} ({ts_label})\n\n{body}"
            doc_chunks.append(
                DocumentChunk(
                    message_id=chunk_message_id(video.video_id, index),
                    external_id=video.video_id,
                    title=video.title,
                    text=text,
                    url=url,
                    date_unixtime=video.published_unixtime,
                    date_iso=video.published_iso,
                    content_hash=doc_hash,
                )
            )

        indexed_chunks += upsert_chunks(conn, YOUTUBE_CHAT_ID, doc_chunks)
        indexed_videos += 1
        print(
            f"  [youtube] {video.title[:55]} — {len(doc_chunks)} chunks",
            flush=True,
        )

    set_meta(conn, META_YOUTUBE_VIDEO_COUNT, str(len(video_ids)))
    return {
        "videos_total": len(video_ids),
        "videos_indexed": indexed_videos,
        "chunks_indexed": indexed_chunks,
        "skipped": skipped,
        "skipped_shorts": skipped_shorts,
        "errors": errors,
    }
