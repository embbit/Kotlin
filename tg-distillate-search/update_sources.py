#!/usr/bin/env python3
"""Sync external sources (hrtz.store + catalog + YouTube) — for cron or manual runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tg_search.db import connect
from tg_search.sync_catalog import (
    remove_stale_catalog_products,
    sync_hrtz_catalog,
)
from tg_search.sync_common import finalize_sync
from tg_search.sync_web import article_urls_from_sitemap, remove_stale_hrtz_urls, sync_hrtz_articles
from tg_search.sync_youtube import sync_youtube_channel
from tg_search.vector_index import build_vectors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Update hrtz.store articles, catalog products and "
            "@DistillateClub YouTube in the search index"
        )
    )
    parser.add_argument(
        "-d",
        "--db",
        type=Path,
        default=Path("distillate.db"),
        help="SQLite database path",
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Sync only hrtz.store articles",
    )
    parser.add_argument(
        "--youtube-only",
        action="store_true",
        help="Sync only YouTube channel",
    )
    parser.add_argument(
        "--no-youtube-shorts",
        action="store_true",
        help="Skip YouTube Shorts (<2 min)",
    )
    parser.add_argument(
        "--skip-vectors",
        action="store_true",
        help="Do not embed new/changed chunks (FTS only)",
    )
    args = parser.parse_args()

    if not args.db.is_file():
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        return 1

    conn = connect(args.db)
    try:
        print(f"Updating external sources in {args.db} …", flush=True)

        web_stats = {"articles_indexed": 0, "chunks_indexed": 0}
        catalog_stats = {"products_indexed": 0, "chunks_indexed": 0}
        yt_stats = {"videos_indexed": 0, "chunks_indexed": 0}

        if not args.youtube_only:
            print("→ hrtz.store articles", flush=True)
            web_stats = sync_hrtz_articles(conn)
            active = set(article_urls_from_sitemap())
            removed = remove_stale_hrtz_urls(conn, active)
            if removed:
                print(f"  removed stale articles: {removed}", flush=True)

            print("→ hrtz.store catalog", flush=True)
            catalog_stats = sync_hrtz_catalog(conn)
            active_products = catalog_stats.get("active_external_ids") or set()
            removed_catalog = remove_stale_catalog_products(conn, active_products)
            if removed_catalog:
                print(f"  removed stale catalog products: {removed_catalog}", flush=True)

        if not args.web_only:
            print("→ YouTube @DistillateClub", flush=True)
            yt_stats = sync_youtube_channel(
                conn, include_shorts=not args.no_youtube_shorts
            )

        finalize_sync(conn)
    finally:
        conn.close()

    if not args.skip_vectors:
        print("→ embedding new/changed chunks …", flush=True)
        vector_stats = build_vectors(args.db)
        print(
            f"  vectors: +{vector_stats.get('built', 0):,}, "
            f"total {vector_stats.get('total_vectors', 0):,}",
            flush=True,
        )

    print(
        "Done.\n"
        f"  site: {web_stats.get('articles_indexed', 0)} articles, "
        f"{web_stats.get('chunks_indexed', 0)} chunks\n"
        f"  catalog: {catalog_stats.get('products_indexed', 0)} products, "
        f"{catalog_stats.get('chunks_indexed', 0)} chunks\n"
        f"  youtube: {yt_stats.get('videos_indexed', 0)} videos, "
        f"{yt_stats.get('chunks_indexed', 0)} chunks",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
