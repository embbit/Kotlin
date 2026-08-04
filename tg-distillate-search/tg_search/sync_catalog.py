"""Sync hrtz.store catalog products into the search database."""

from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.error
import urllib.request
from html import unescape

from tg_search.external_sources import (
    HRTZ_BASE_URL,
    HRTZ_CATALOG_CHAT_ID,
    HRTZ_CATALOG_PAGE_URL,
    HRTZ_CATALOG_RECID,
    META_HRTZ_CATALOG_COUNT,
    chunk_message_id,
)
from tg_search.html_extract import extract_page_text
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
TILDA_STORE_API = "https://store.tildaapi.com/api/getproductslist/"
STORE_PART_RE = re.compile(
    rf"storepartnav%5B{re.escape(HRTZ_CATALOG_RECID)}%5D=([0-9]+)"
)
META_DESC_RE = re.compile(
    r'<meta\s+name="description"\s+content="([^"]*)"',
    re.IGNORECASE,
)


def _fetch(url: str, *, timeout: float = 60.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _fetch_json(url: str, *, timeout: float = 60.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def catalog_part_uids(catalog_html: str | None = None) -> list[str]:
    html = catalog_html if catalog_html is not None else _fetch(HRTZ_CATALOG_PAGE_URL)
    return sorted(set(STORE_PART_RE.findall(html)))


def _products_for_part(recid: str, part_uid: str, *, page_size: int = 100) -> list[dict]:
    products: list[dict] = []
    slice_num = 1
    while True:
        url = (
            f"{TILDA_STORE_API}?getoptions=true&getparts=true"
            f"&recid={recid}&size={page_size}&slice={slice_num}&storepartuid={part_uid}"
        )
        payload = _fetch_json(url)
        batch = payload.get("products") or []
        products.extend(batch)
        total = int(payload.get("total") or 0)
        if not batch or slice_num * page_size >= total:
            break
        slice_num += 1
    return products


def fetch_catalog_products(
    *,
    recid: str = HRTZ_CATALOG_RECID,
    catalog_html: str | None = None,
) -> list[dict]:
    by_uid: dict[int, dict] = {}
    for part_uid in catalog_part_uids(catalog_html):
        for product in _products_for_part(recid, part_uid):
            by_uid[int(product["uid"])] = product
    return list(by_uid.values())


def _format_price(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return raw.strip()
    if value.is_integer():
        return f"{int(value)} ₽"
    return f"{value:.2f}".rstrip("0").rstrip(".") + " ₽"


def _meta_description(html: str) -> str:
    match = META_DESC_RE.search(html)
    if not match:
        return ""
    return unescape(match.group(1)).strip()


def _product_body(product: dict, *, page_html: str | None = None) -> str:
    lines = [unescape(str(product.get("title") or "Товар")).strip()]
    sku = str(product.get("sku") or "").strip()
    if sku:
        lines.append(f"Артикул: {sku}")
    price = _format_price(str(product.get("price") or "").strip())
    if price:
        lines.append(f"Цена: {price}")
    mark = str(product.get("mark") or "").strip()
    if mark:
        lines.append(f"Наличие: {mark}")

    for field in ("descr", "text"):
        value = unescape(str(product.get(field) or "")).strip()
        if value:
            lines.append(value)

    if page_html:
        _title, body = extract_page_text(page_html)
        if body:
            lines.append(body)
        meta = _meta_description(page_html)
        if meta and meta not in lines[-1]:
            lines.insert(1, meta)

    url = str(product.get("url") or HRTZ_CATALOG_PAGE_URL).strip()
    lines.append(f"Заказать в каталоге hrtz.store: {url}")
    return "\n\n".join(line for line in lines if line)


def sync_hrtz_catalog(
    conn: sqlite3.Connection,
    *,
    recid: str = HRTZ_CATALOG_RECID,
    fetch_pages: bool = True,
) -> dict[str, int]:
    ensure_source(
        conn,
        chat_id=HRTZ_CATALOG_CHAT_ID,
        name="HERTZ — каталог",
        source_type="web",
        label="каталог",
        username="hrtz.store",
    )

    catalog_html = _fetch(HRTZ_CATALOG_PAGE_URL)
    products = fetch_catalog_products(recid=recid, catalog_html=catalog_html)
    indexed_products = 0
    indexed_chunks = 0
    skipped = 0
    errors = 0

    for product in products:
        uid = int(product["uid"])
        url = str(product.get("url") or f"{HRTZ_BASE_URL}/product/{uid}").strip()
        title = unescape(str(product.get("title") or "Товар")).strip()
        page_html: str | None = None
        if fetch_pages and not str(product.get("text") or "").strip():
            try:
                page_html = _fetch(url)
            except (urllib.error.URLError, TimeoutError):
                page_html = None

        body = _product_body(product, page_html=page_html)
        if not body:
            errors += 1
            continue

        doc_hash = content_hash(title + "\n" + body)
        external_id = f"product:{uid}"
        if document_unchanged(conn, HRTZ_CATALOG_CHAT_ID, external_id, doc_hash):
            skipped += 1
            continue

        doc_chunks = [
            DocumentChunk(
                message_id=chunk_message_id(external_id, 0),
                external_id=external_id,
                title=title,
                text=f"{title}\n\n{body}",
                url=url,
                date_unixtime=int(time.time()),
                date_iso=time.strftime("%Y-%m-%d", time.gmtime()),
                content_hash=doc_hash,
            )
        ]
        indexed_chunks += upsert_chunks(conn, HRTZ_CATALOG_CHAT_ID, doc_chunks)
        indexed_products += 1
        print(f"  [каталог] {title[:60]}", flush=True)

    set_meta(conn, META_HRTZ_CATALOG_COUNT, str(len(products)))
    return {
        "products_total": len(products),
        "products_indexed": indexed_products,
        "chunks_indexed": indexed_chunks,
        "skipped": skipped,
        "errors": errors,
        "active_external_ids": active_catalog_external_ids(products),
    }


def remove_stale_catalog_products(conn: sqlite3.Connection, active_ids: set[str]) -> int:
    rows = conn.execute(
        "SELECT DISTINCT from_id FROM messages WHERE chat_id = ? AND from_id IS NOT NULL",
        (HRTZ_CATALOG_CHAT_ID,),
    ).fetchall()
    removed = 0
    for row in rows:
        external_id = str(row["from_id"])
        if external_id not in active_ids:
            delete_external_documents(conn, HRTZ_CATALOG_CHAT_ID, external_id)
            removed += 1
    return removed


def active_catalog_external_ids(products: list[dict]) -> set[str]:
    return {f"product:{int(product['uid'])}" for product in products}
