"""Fuzzy and prefix matching for slang / typos."""

from __future__ import annotations

import re

WORD_RE = re.compile(r"[\w\u0400-\u04FF]+", re.UNICODE)

SHORT_PREFIX_MIN = 3
SHORT_PREFIX_TRY = (5, 4, 3)


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def shared_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def fuzzy_token_match(query: str, token: str) -> bool:
    q, t = query.lower(), token.lower()
    if not q or not t:
        return False
    if q == t or q in t or t in q:
        return True

    common = shared_prefix_len(q, t)
    if common >= SHORT_PREFIX_MIN and len(q) >= 5 and len(t) >= 4:
        return True

    max_len = max(len(q), len(t))
    if max_len < 5:
        return False
    max_edits = 2 if max_len > 8 else 1
    return levenshtein(q, t) <= max_edits


def text_matches_query_word(text: str, word: str, *, lemmatize_word) -> bool:
    lower = text.lower()
    w = word.lower()
    if w in lower:
        return True

    query_lemma = lemmatize_word(word).lower()
    if query_lemma in lower:
        return True

    for token in WORD_RE.findall(text):
        tl = token.lower()
        if lemmatize_word(token).lower() == query_lemma:
            return True
        if fuzzy_token_match(word, token):
            return True
    return False


def best_match_needle(text: str, word: str) -> str | None:
    lower = text.lower()
    w = word.lower()
    if w in lower:
        return w

    best: str | None = None
    best_len = 0
    for token in WORD_RE.findall(text):
        tl = token.lower()
        if fuzzy_token_match(word, token) and len(tl) > best_len:
            best = tl
            best_len = len(tl)
    return best


def short_prefixes(word: str, *, lemmatize_word) -> list[str]:
    base = lemmatize_word(word) if len(word) > 2 else word
    bases = {word.lower(), base.lower()}
    prefixes: list[str] = []
    seen: set[str] = set()
    for b in bases:
        for plen in SHORT_PREFIX_TRY:
            if plen >= SHORT_PREFIX_MIN and plen < len(b):
                p = b[:plen]
                if p not in seen:
                    seen.add(p)
                    prefixes.append(p)
    return prefixes
