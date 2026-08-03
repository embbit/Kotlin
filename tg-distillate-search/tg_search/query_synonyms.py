"""Query synonym groups for FTS and text matching."""

from __future__ import annotations

import re

from tg_search.fuzzy import text_matches_query_word

WORD_RE = re.compile(r"[\w\u0400-\u04FF]+", re.UNICODE)

# Canonical lemma roots with shared meaning in distilling context.
SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"энзим", "фермент"}),
)


def canonical_synonym_root(lemma: str) -> str:
    lemma = lemma.lower()
    if lemma.startswith("энзим"):
        return "энзим"
    if lemma.startswith("фермент"):
        return "фермент"
    return lemma


def synonym_lemmas(lemma: str) -> frozenset[str]:
    root = canonical_synonym_root(lemma.lower())
    for group in SYNONYM_GROUPS:
        if root in group:
            return group
    return frozenset({lemma.lower()})


def expand_word_groups(words: list[str]) -> list[list[str]]:
    """One OR-group per query word (synonyms included)."""
    groups: list[list[str]] = []
    seen_groups: set[tuple[str, ...]] = set()
    for word in words:
        group = tuple(sorted(synonym_lemmas(word.lower())))
        if group in seen_groups:
            continue
        seen_groups.add(group)
        groups.append(list(group))
    return groups


def fts_word_group(alternatives: list[str], *, prefix: bool = False) -> str:
    if not alternatives:
        return ""
    if len(alternatives) == 1:
        word = alternatives[0]
        if prefix and len(word) >= 3:
            return f"{word}*"
        return f'"{word}"'
    parts = []
    for word in alternatives:
        if prefix and len(word) >= 3:
            parts.append(f"{word}*")
        else:
            parts.append(f'"{word}"')
    return "(" + " OR ".join(parts) + ")"


def fts_query_from_groups(groups: list[list[str]], *, prefix: bool = False) -> str:
    if not groups:
        return ""
    return " ".join(fts_word_group(group, prefix=prefix) for group in groups)


def text_matches_synonym_word(text: str, word: str, *, lemmatize_word) -> bool:
    query_group = synonym_lemmas(lemmatize_word(word).lower())
    for token in WORD_RE.findall(text):
        if synonym_lemmas(lemmatize_word(token).lower()) & query_group:
            return True
    for alt in query_group:
        if text_matches_query_word(text, alt, lemmatize_word=lemmatize_word):
            return True
    return False


def title_topic_boost(
    from_name: str | None,
    words: list[str],
    *,
    lemmatize_word,
) -> float:
    title = (from_name or "").lower()
    if not title or not words:
        return 1.0
    for word in words:
        for alt in synonym_lemmas(lemmatize_word(word).lower()):
            if alt in title:
                return 1.4
    return 1.0
