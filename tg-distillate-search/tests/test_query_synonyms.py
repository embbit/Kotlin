"""Tests for query synonym expansion."""

from __future__ import annotations

import unittest

from tg_search.query_synonyms import (
    expand_word_groups,
    fts_query_from_groups,
    synonym_lemmas,
    text_matches_synonym_word,
    title_topic_boost,
)
from tg_search.lemmatize import lemmatize_word


class TestQuerySynonyms(unittest.TestCase):
    def test_enzyme_ferment_group(self) -> None:
        self.assertIn("фермент", synonym_lemmas("энзим"))
        self.assertIn("энзим", synonym_lemmas("фермент"))

    def test_fts_or_query(self) -> None:
        groups = expand_word_groups(["энзим"])
        q = fts_query_from_groups(groups)
        self.assertIn("OR", q)
        self.assertIn("энзим", q)
        self.assertIn("фермент", q)

    def test_text_match_across_synonyms(self) -> None:
        self.assertTrue(
            text_matches_synonym_word(
                "Поговорим о ферментах и брожении",
                "энзимы",
                lemmatize_word=lemmatize_word,
            )
        )

    def test_title_boost(self) -> None:
        boost = title_topic_boost(
            "Поговорим о ферментах",
            ["энзимы"],
            lemmatize_word=lemmatize_word,
        )
        self.assertGreater(boost, 1.3)


if __name__ == "__main__":
    unittest.main()
