"""Fuzzy and prefix matching for slang / typos."""

from __future__ import annotations

import math
import re

WORD_RE = re.compile(r"[\w\u0400-\u04FF]+", re.UNICODE)

SHORT_PREFIX_MIN = 3
SHORT_PREFIX_TRY = (5, 4, 3)
MIN_SUBSTRING_LEN = 3
PROXIMITY_WINDOW_BASE = 50
PROXIMITY_WINDOW_PER_WORD = 20
PROXIMITY_WINDOW_MAX = 160


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
    if q == t:
        return True
    if len(t) >= MIN_SUBSTRING_LEN and t in q:
        return True
    if len(q) >= MIN_SUBSTRING_LEN and q in t:
        return True

    common = shared_prefix_len(q, t)
    if common >= SHORT_PREFIX_MIN and len(q) >= 5 and len(t) >= 4:
        return True

    max_len = max(len(q), len(t))
    if max_len < 5:
        return False
    max_edits = 2 if max_len > 8 else 1
    return levenshtein(q, t) <= max_edits


def _token_matches_word(
    token: str,
    word: str,
    *,
    lemmatize_word,
    allow_fuzzy: bool,
) -> bool:
    tl = token.lower()
    if len(tl) < 2:
        return False
    w = word.lower()
    if tl == w:
        return True
    query_lemma = lemmatize_word(word).lower()
    if lemmatize_word(token).lower() == query_lemma:
        return True
    if allow_fuzzy and len(tl) >= MIN_SUBSTRING_LEN and fuzzy_token_match(word, token):
        return True
    return False


def text_matches_query_word(
    text: str,
    word: str,
    *,
    lemmatize_word,
    allow_fuzzy: bool = True,
) -> bool:
    lower = text.lower()
    w = word.lower()
    if w in lower:
        return True

    query_lemma = lemmatize_word(word).lower()
    if len(query_lemma) >= MIN_SUBSTRING_LEN and query_lemma in lower:
        return True

    for token in WORD_RE.findall(text):
        if _token_matches_word(
            token, word, lemmatize_word=lemmatize_word, allow_fuzzy=allow_fuzzy
        ):
            return True
    return False


def count_content_matches(
    text: str,
    words: list[str],
    *,
    lemmatize_word,
    allow_fuzzy: bool = True,
) -> int:
    return sum(
        1
        for word in words
        if text_matches_query_word(
            text, word, lemmatize_word=lemmatize_word, allow_fuzzy=allow_fuzzy
        )
    )


def _token_spans(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group()) for m in WORD_RE.finditer(text)]


def proximity_window_chars(word_count: int) -> int:
    if word_count <= 1:
        return PROXIMITY_WINDOW_MAX
    return min(
        PROXIMITY_WINDOW_MAX,
        PROXIMITY_WINDOW_BASE + PROXIMITY_WINDOW_PER_WORD * word_count,
    )


def proximity_match_ratio(
    text: str,
    words: list[str],
    *,
    lemmatize_word,
    window: int | None = None,
) -> float:
    """Share of query words co-occurring inside the tightest character window."""
    if not words:
        return 1.0
    if len(words) == 1:
        return 1.0 if text_matches_query_word(text, words[0], lemmatize_word=lemmatize_word) else 0.0

    window = window or proximity_window_chars(len(words))
    allow_fuzzy = len(words) <= 2
    tagged: list[tuple[int, int, int]] = []
    for wi, word in enumerate(words):
        for start, end, token in _token_spans(text):
            if _token_matches_word(
                token, word, lemmatize_word=lemmatize_word, allow_fuzzy=allow_fuzzy
            ):
                tagged.append((start, end, wi))

    if not tagged:
        return 0.0

    tagged.sort()
    best = 0
    for i, (start, _end, _wi) in enumerate(tagged):
        words_in_window: set[int] = set()
        for pos_start, pos_end, wi in tagged[i:]:
            if pos_start - start > window:
                break
            words_in_window.add(wi)
        best = max(best, len(words_in_window))

    return best / len(words)


def multi_word_match_threshold(word_count: int) -> int:
    if word_count <= 2:
        return word_count
    if word_count == 3:
        return 2
    return max(3, math.ceil(word_count * 0.75))


def min_proximity_ratio(word_count: int) -> float:
    if word_count <= 2:
        return 0.0
    if word_count == 3:
        return 0.67
    return 0.6


def text_matches_multi_word(
    text: str,
    words: list[str],
    *,
    lemmatize_word,
) -> bool:
    if not words:
        return True
    if len(words) == 1:
        return text_matches_query_word(text, words[0], lemmatize_word=lemmatize_word)
    allow_fuzzy = len(words) <= 2
    matches = count_content_matches(
        text, words, lemmatize_word=lemmatize_word, allow_fuzzy=allow_fuzzy
    )
    needed = multi_word_match_threshold(len(words))
    if matches < needed:
        return False
    if len(words) >= 3:
        return proximity_match_ratio(text, words, lemmatize_word=lemmatize_word) >= min_proximity_ratio(
            len(words)
        )
    return True


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
