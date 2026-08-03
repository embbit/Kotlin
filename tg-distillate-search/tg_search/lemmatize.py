"""Russian lemmatization for FTS indexing and queries."""

from __future__ import annotations

import re
from functools import lru_cache

WORD_RE = re.compile(r"[\w\u0400-\u04FF]+", re.UNICODE)


@lru_cache(maxsize=1)
def _analyzer():
    import pymorphy3

    return pymorphy3.MorphAnalyzer()


def lemmatize_word(word: str) -> str:
    word = word.strip().lower()
    if not word:
        return word
    parsed = _analyzer().parse(word)
    if not parsed:
        return word
    return parsed[0].normal_form


def lemmatize_text(text: str) -> str:
    parts: list[str] = []
    last = 0
    for match in WORD_RE.finditer(text):
        parts.append(text[last : match.start()])
        parts.append(lemmatize_word(match.group(0)))
        last = match.end()
    parts.append(text[last:])
    return "".join(parts)
