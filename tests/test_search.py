from __future__ import annotations

import pytest

from src.indexer import SearchIndex, PageRecord
from src.search import SearchEngine


def build_search_engine() -> SearchEngine:
    search_index = SearchIndex(
        metadata={"page_count": 2},
        pages={
            "https://quotes.toscrape.com/": PageRecord(title="Home", word_count=4),
            "https://quotes.toscrape.com/page/2/": PageRecord(
                title="Page 2", word_count=5
            ),
        },
        index={
            "good": {
                "https://quotes.toscrape.com/": {"frequency": 2, "positions": [1, 3]},
                "https://quotes.toscrape.com/page/2/": {"frequency": 1, "positions": [2]},
            },
            "friends": {
                "https://quotes.toscrape.com/": {"frequency": 1, "positions": [2]},
                "https://quotes.toscrape.com/page/2/": {"frequency": 3, "positions": [1, 4, 5]},
            },
        },
    )
    return SearchEngine(search_index)


def test_print_word_returns_postings() -> None:
    engine = build_search_engine()

    postings = engine.print_word("good")

    assert postings["https://quotes.toscrape.com/"]["frequency"] == 2


def test_print_word_rejects_multi_word_input() -> None:
    engine = build_search_engine()

    with pytest.raises(ValueError):
        engine.print_word("good friends")


def test_find_uses_and_semantics_and_sorts_by_total_frequency() -> None:
    engine = build_search_engine()

    results = engine.find("good friends")

    assert [result.url for result in results] == [
        "https://quotes.toscrape.com/page/2/",
        "https://quotes.toscrape.com/",
    ]
    assert results[0].total_frequency == 4
    assert results[1].matched_terms == {"good": 2, "friends": 1}


def test_find_returns_empty_list_for_empty_or_missing_queries() -> None:
    engine = build_search_engine()

    assert engine.find("") == []
    assert engine.find("missing") == []
