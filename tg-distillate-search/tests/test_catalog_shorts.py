"""Tests for hrtz.store catalog sync and YouTube Shorts listing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tg_search.db import connect, get_meta, rebuild_fts
from tg_search.external_sources import HRTZ_CATALOG_CHAT_ID
from tg_search.search import search_page
from tg_search.sync_catalog import (
    _product_body,
    catalog_part_uids,
    sync_hrtz_catalog,
)
from tg_search.sync_youtube import list_all_channel_video_ids, list_channel_short_ids

CATALOG_HTML = """
<html><body>
<script>storepartnav%5B1102118231%5D=111</script>
<script>storepartnav%5B1102118231%5D=222</script>
</body></html>
"""

PRODUCTS_PAYLOAD = {
    "total": 1,
    "products": [
        {
            "uid": 9001,
            "title": "EN-03 Энзим для крахмала",
            "sku": "EN-03",
            "price": "1500",
            "mark": "В наличии",
            "descr": "Фермент для сахарного сырья.",
            "text": "",
            "url": "https://hrtz.store/product/9001-en03",
        }
    ],
}


class TestCatalogSync(unittest.TestCase):
    def test_catalog_part_uids(self) -> None:
        uids = catalog_part_uids(CATALOG_HTML)
        self.assertEqual(uids, ["111", "222"])

    def test_product_body_includes_order_link(self) -> None:
        body = _product_body(PRODUCTS_PAYLOAD["products"][0])
        self.assertIn("EN-03", body)
        self.assertIn("Заказать в каталоге hrtz.store:", body)
        self.assertIn("https://hrtz.store/product/9001-en03", body)

    def test_sync_catalog_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            conn = connect(db)

            def fetch_side_effect(url: str, *, timeout: float = 60.0) -> str:
                if "catalog" in url:
                    return CATALOG_HTML
                if "9001-en03" in url:
                    return (
                        '<html><head><meta name="description" '
                        'content="Энзим EN-03 для крахмала"></head><body></body></html>'
                    )
                raise AssertionError(f"unexpected fetch: {url}")

            def fetch_json_side_effect(url: str, *, timeout: float = 60.0) -> dict:
                self.assertIn("storepartuid=", url)
                return PRODUCTS_PAYLOAD

            with patch("tg_search.sync_catalog._fetch", side_effect=fetch_side_effect):
                with patch(
                    "tg_search.sync_catalog._fetch_json",
                    side_effect=fetch_json_side_effect,
                ):
                    stats = sync_hrtz_catalog(conn, fetch_pages=True)
                    rebuild_fts(conn)
                    conn.commit()

            self.assertEqual(stats["products_indexed"], 1)
            self.assertEqual(get_meta(conn, "hrtz_catalog_count"), "1")

            row = conn.execute(
                """
                SELECT m.*, s.label AS source_label
                FROM messages m
                JOIN sources s ON s.chat_id = m.chat_id
                WHERE m.chat_id = ?
                """,
                (HRTZ_CATALOG_CHAT_ID,),
            ).fetchone()
            conn.close()

            self.assertIsNotNone(row)
            self.assertEqual(row["source_label"], "каталог")
            self.assertIn("EN-03", row["text"])

            page = search_page(db, "заказать энзимы", limit=5)
            self.assertTrue(page.hits)
            self.assertEqual(page.hits[0].source_label, "каталог")


class TestYouTubeShorts(unittest.TestCase):
    def test_list_channel_short_ids(self) -> None:
        html = b'{"videoId":"abc11111111","videoId":"def22222222"}'
        with patch("tg_search.sync_youtube._fetch", return_value=html):
            ids = list_channel_short_ids()
        self.assertEqual(ids, ["abc11111111", "def22222222"])

    def test_list_all_includes_shorts(self) -> None:
        with patch(
            "tg_search.sync_youtube.list_channel_video_ids",
            return_value=["vid11111111"],
        ), patch(
            "tg_search.sync_youtube.list_channel_short_ids",
            return_value=["sho11111111"],
        ), patch(
            "tg_search.sync_youtube.videos_from_rss",
            return_value=[],
        ):
            ids = list_all_channel_video_ids()
        self.assertEqual(ids, ["sho11111111", "vid11111111"])


if __name__ == "__main__":
    unittest.main()
