"""Tests for external source sync."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tg_search.document_links import hit_link
from tg_search.external_sources import HRTZ_CHAT_ID, YOUTUBE_CHAT_ID
from tg_search.db import connect, rebuild_fts
from tg_search.html_extract import chunk_text, extract_page_text
from tg_search.import_json import import_export
from tg_search.search import search
from tg_search.sync_web import article_urls_from_sitemap, sync_hrtz_articles
from tg_search.sync_youtube import (
    _chapters_from_description,
    _seconds_from_timestamp,
    build_video_chunks,
)
from tg_search.sync_youtube import YouTubeVideo

CHAT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://hrtz.store/page123.html</loc></url>
  <url><loc>https://hrtz.store/catalog</loc></url>
</urlset>"""

ARTICLE_HTML = """
<html><head><title>Статья: подготовка новых бочек</title></head>
<body><main>
<p>Нюансы работы с новыми бочками при первом использовании дубовой ёмкости.</p>
<p>Промывка паром и контроль влажности перед первой заливкой дистиллята.</p>
</main></body></html>
"""


class TestHtmlExtract(unittest.TestCase):
    def test_extract_and_chunk(self) -> None:
        title, body = extract_page_text(ARTICLE_HTML)
        self.assertEqual(title, "подготовка новых бочек")
        self.assertIn("нюансы работы", body.lower())
        chunks = chunk_text(body, target=80)
        self.assertGreaterEqual(len(chunks), 1)


class TestYouTubeChapters(unittest.TestCase):
    def test_parse_chapters(self) -> None:
        desc = "00:00 Intro\n09:06 Как готовить бочку\n15:20 Доля ангелов"
        chapters = _chapters_from_description(desc)
        self.assertEqual(len(chapters), 3)
        self.assertEqual(_seconds_from_timestamp("09:06"), 546)

    def test_build_chunks_from_description(self) -> None:
        video = YouTubeVideo(
            video_id="abc12345678",
            title="Дубовая бочка",
            published_unixtime=1_650_000_000,
            published_iso="2023-05-18",
            description="00:00 Start\n09:06 Как готовить бочку",
        )
        chunks = build_video_chunks(video)
        self.assertGreaterEqual(len(chunks), 1)


class TestExternalSync(unittest.TestCase):
    def test_sitemap_filters_article_pages(self) -> None:
        with patch("tg_search.sync_web._fetch", return_value=SITEMAP):
            urls = article_urls_from_sitemap()
        self.assertEqual(urls, ["https://hrtz.store/page123.html"])

    def test_sync_web_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            import_export(CHAT_FIXTURE, db, username="distillate_club_chat")

            with patch("tg_search.sync_web._fetch") as fetch:
                fetch.side_effect = [SITEMAP, ARTICLE_HTML]
                conn = connect(db)
                try:
                    stats = sync_hrtz_articles(conn)
                    rebuild_fts(conn)
                    conn.commit()
                finally:
                    conn.close()

            conn = connect(db)
            row = conn.execute(
                "SELECT m.*, s.username, s.label AS source_label "
                "FROM messages m JOIN sources s ON s.chat_id = m.chat_id "
                "WHERE m.chat_id = ? LIMIT 1",
                (HRTZ_CHAT_ID,),
            ).fetchone()
            conn.close()

            self.assertEqual(stats["articles_indexed"], 1)
            self.assertIsNotNone(row)
            self.assertTrue(str(row["url"]).startswith("https://hrtz.store/"))
            self.assertEqual(hit_link(row), row["url"])

            hits = search(db, "новыми бочками", limit=5)
            self.assertTrue(any("бочк" in h.text.lower() for h in hits))


if __name__ == "__main__":
    unittest.main()
