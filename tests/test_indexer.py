from __future__ import annotations

from src.crawler import PageContent
from src.indexer import build_index, load_index, save_index, tokenize


def test_tokenize_is_case_insensitive_and_keeps_apostrophes() -> None:
    assert tokenize("Good friends don't disappear.") == [
        "good",
        "friends",
        "don't",
        "disappear",
    ]


def test_build_index_tracks_frequency_and_positions() -> None:
    pages = [
        PageContent(
            url="https://quotes.toscrape.com/",
            title="Home",
            text="Good friends good books",
        )
    ]

    search_index = build_index(pages)

    assert search_index.metadata["page_count"] == 1
    assert search_index.pages["https://quotes.toscrape.com/"].word_count == 4
    assert search_index.index["good"]["https://quotes.toscrape.com/"]["frequency"] == 2
    assert search_index.index["good"]["https://quotes.toscrape.com/"]["positions"] == [1, 3]


def test_save_and_load_round_trip(tmp_path) -> None:
    pages = [
        PageContent(
            url="https://quotes.toscrape.com/",
            title="Home",
            text="Books and friends",
        )
    ]
    destination = tmp_path / "index.json"

    saved_path = save_index(build_index(pages), destination)
    loaded = load_index(saved_path)

    assert saved_path.exists()
    assert loaded.pages["https://quotes.toscrape.com/"].title == "Home"
    assert loaded.index["friends"]["https://quotes.toscrape.com/"]["positions"] == [3]
