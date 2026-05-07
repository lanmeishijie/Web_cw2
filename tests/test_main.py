from __future__ import annotations

from src.crawler import PageContent
from src.main import SearchToolApp, main


class FakeCrawler:
    def crawl(self) -> list[PageContent]:
        return [
            PageContent(
                url="https://quotes.toscrape.com/",
                title="Home",
                text="Good friends good books",
            ),
            PageContent(
                url="https://quotes.toscrape.com/page/2/",
                title="Page 2",
                text="Good friends stay close",
            ),
        ]


def test_app_build_load_print_and_find(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("src.main.QuoteCrawler", FakeCrawler)
    app = SearchToolApp(index_path=tmp_path / "index.json")

    build_output = app.build()
    load_output = app.load()
    print_output = app.print_word("good")
    find_output = app.find("good friends")

    assert "Built index with 2 pages" in build_output
    assert "Loaded index from" in load_output
    assert '"frequency": 2' in print_output
    assert "https://quotes.toscrape.com/" in find_output
    assert "matched_terms={'good': 2, 'friends': 1}" in find_output


def test_execute_handles_help_and_empty_find(tmp_path) -> None:
    app = SearchToolApp(index_path=tmp_path / "index.json")

    assert "Commands:" in app.execute("help")
    assert app.execute("find") == "Empty query. Please provide one or more search terms."


def test_main_returns_zero_for_direct_find(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr("src.main.DEFAULT_INDEX_PATH", tmp_path / "index.json")
    monkeypatch.setattr("src.main.QuoteCrawler", FakeCrawler)

    assert main(["--index-file", str(tmp_path / "index.json"), "build"]) == 0
    assert main(["--index-file", str(tmp_path / "index.json"), "find", "good", "friends"]) == 0

    output = capsys.readouterr().out
    assert "Built index with 2 pages" in output
    assert "https://quotes.toscrape.com/page/2/" in output
