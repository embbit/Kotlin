"""Russian stop words for search queries."""

from __future__ import annotations

import re
from typing import Callable

WORD_RE = re.compile(r"[\w\u0400-\u04FF]+", re.UNICODE)

RU_STOPWORDS = frozenset(
    """
    и в во не ни что это как так но а или либо
    с со к ко у о об обо от до из за на над под при для про без через
    по мне ты он она мы вы они
    мой твой свой наш ваш их этот тот такой какой который
    уже ещё еще
    """.split()
)


def query_tokens(raw: str) -> list[str]:
    return WORD_RE.findall(raw)


def content_words(raw: str, lemmatize_word: Callable[[str], str]) -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    for word in query_tokens(raw):
        lw = word.lower()
        if lw in RU_STOPWORDS or len(lw) < 2:
            continue
        lemma = lemmatize_word(word).lower()
        if lemma in RU_STOPWORDS or lemma in seen:
            continue
        seen.add(lemma)
        words.append(lemma)
    return words
