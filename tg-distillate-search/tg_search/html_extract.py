"""Extract readable text from HTML pages (Tilda / generic)."""

from __future__ import annotations

import re
from html import unescape

from bs4 import BeautifulSoup

STRIP_TAGS = ("script", "style", "nav", "footer", "header", "noscript")
MIN_LINE_LEN = 40
CHUNK_TARGET = 1200


def clean_page_title(raw: str) -> str:
    title = unescape(raw or "").strip()
    title = re.sub(r"\s*[-|–—]\s*HERTZ.*$", "", title, flags=re.I)
    title = re.sub(r"^Статья:\s*", "", title, flags=re.I)
    return title.strip() or "Статья"


def extract_page_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = clean_page_title(title_tag.get_text(strip=True) if title_tag else "")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    lines: list[str] = []
    seen: set[str] = set()
    for line in soup.get_text("\n", strip=True).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < MIN_LINE_LEN:
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)

    body = "\n\n".join(lines).strip()
    return title, body


def chunk_text(body: str, *, target: int = CHUNK_TARGET) -> list[str]:
    if not body:
        return []
    if len(body) <= target:
        return [body]

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current and current_len + len(para) + 2 > target:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para) + 2

    if current:
        chunks.append("\n\n".join(current))
    return chunks
