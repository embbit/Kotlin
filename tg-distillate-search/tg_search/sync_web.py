"""Sync hrtz.store knowledge-base articles into the search database."""

from __future__ import annotations

import re
import sqlite3
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from tg_search.external_sources import (
    HRTZ_ARTICLE_PATH_RE,
    HRTZ_BASE_URL,
    HRTZ_CHAT_ID,
    HRTZ_SITEMAP_URL,
    META_HRTZ_ARTICLE_COUNT,
    chunk_message_id,
)
from tg_search.html_extract import chunk_text, extract_page_text
from tg_search.sync_common import (
    DocumentChunk,
    content_hash,
    delete_external_documents,
    document_unchanged,
    ensure_source,
    upsert_chunks,
)
from tg_search.db import set_meta

USER_AGENT = (
    "Mozilla/5.0 (compatible; DistillateSearchBot/1.0; +https://github.com/embbit/Kotlin)"
)
ARTICLE_PATH_PATTERN = re.compile(HRTZ_ARTICLE_PATH_RE)


def _fetch(url: str, *, timeout: float = 60.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def article_urls_from_sitemap(sitemap_url: str = HRTZ_SITEMAP_URL) -> list[str]:
    xml_text = _fetch(sitemap_url)
    root = ET.fromstring(xml_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: list[str] = []
    for loc in root.findall(".//sm:loc", ns):
        if loc.text and ARTICLE_PATH_PATTERN.search(loc.text):
            urls.append(loc.text.strip())
    return sorted(set(urls))


def sync_hrtz_articles(
    conn: sqlite3.Connection,
    *,
    sitemap_url: str = HRTZ_SITEMAP_URL,
    base_url: str = HRTZ_BASE_URL,
) -> dict[str, int]:
    ensure_source(
        conn,
        chat_id=HRTZ_CHAT_ID,
        name="HERTZ — база знаний",
        source_type="web",
        label="сайт",
        username="hrtz.store",
    )

    urls = article_urls_from_sitemap(sitemap_url)
    indexed_articles = 0
    indexed_chunks = 0
    skipped = 0
    errors = 0

    for url in urls:
        try:
            html = _fetch(url)
            title, body = extract_page_text(html)
            if not body:
                errors += 1
                continue

            doc_hash = content_hash(title + "\n" + body)
            if document_unchanged(conn, HRTZ_CHAT_ID, url, doc_hash):
                skipped += 1
                continue

            chunks = chunk_text(body)
            now = int(time.time())
            date_iso = time.strftime("%Y-%m-%d", time.gmtime(now))
            doc_chunks: list[DocumentChunk] = []
            for index, chunk in enumerate(chunks):
                chunk_url = url if len(chunks) == 1 else f"{url}#chunk-{index + 1}"
                prefix = f"{title}\n\n" if index == 0 else f"{title} (продолжение)\n\n"
                text = prefix + chunk
                doc_chunks.append(
                    DocumentChunk(
                        message_id=chunk_message_id(url, index),
                        external_id=url,
                        title=title,
                        text=text,
                        url=chunk_url,
                        date_unixtime=now,
                        date_iso=date_iso,
                        content_hash=doc_hash,
                    )
                )

            indexed_chunks += upsert_chunks(conn, HRTZ_CHAT_ID, doc_chunks)
            indexed_articles += 1
            print(f"  [сайт] {title[:60]} — {len(doc_chunks)} chunks", flush=True)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            errors += 1
            print(f"  [сайт] skip {url}: {exc}", flush=True)

    set_meta(conn, META_HRTZ_ARTICLE_COUNT, str(indexed_articles + skipped))
    return {
        "articles_total": len(urls),
        "articles_indexed": indexed_articles,
        "chunks_indexed": indexed_chunks,
        "skipped": skipped,
        "errors": errors,
    }


def remove_stale_hrtz_urls(conn: sqlite3.Connection, active_urls: set[str]) -> int:
    rows = conn.execute(
        "SELECT DISTINCT from_id FROM messages WHERE chat_id = ? AND from_id IS NOT NULL",
        (HRTZ_CHAT_ID,),
    ).fetchall()
    removed = 0
    for row in rows:
        url = str(row["from_id"])
        if url not in active_urls:
            delete_external_documents(conn, HRTZ_CHAT_ID, url)
            removed += 1
    return removed
