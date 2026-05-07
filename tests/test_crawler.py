from __future__ import annotations

from dataclasses import dataclass

from src.crawler import QuoteCrawler


@dataclass
class FakeResponse:
    text: str
    url: str
    status_code: int = 200

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, responses: dict[str, FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[str] = []
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.calls.append(url)
        return self.responses[url]


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


def test_crawler_follows_next_page_and_extracts_quote_text() -> None:
    html_page_1 = """
    <html>
      <head><title>Page 1</title></head>
      <body>
        <div class="quote">
          <span class="text">"Be yourself."</span>
          <small class="author">Oscar Wilde</small>
          <div class="tags"><a class="tag">life</a><a class="tag">humor</a></div>
        </div>
        <li class="next"><a href="/page/2/">Next</a></li>
      </body>
    </html>
    """
    html_page_2 = """
    <html>
      <head><title>Page 2</title></head>
      <body>
        <div class="quote">
          <span class="text">"Read more books."</span>
          <small class="author">Jane Austen</small>
          <div class="tags"><a class="tag">books</a></div>
        </div>
      </body>
    </html>
    """
    session = FakeSession(
        {
            "https://quotes.toscrape.com/": FakeResponse(
                text=html_page_1, url="https://quotes.toscrape.com/"
            ),
            "https://quotes.toscrape.com/page/2/": FakeResponse(
                text=html_page_2, url="https://quotes.toscrape.com/page/2/"
            ),
        }
    )
    clock = FakeClock()
    crawler = QuoteCrawler(
        session=session,
        sleeper=clock.sleep,
        clock=clock.now,
        politeness_window=6.0,
    )

    pages = crawler.crawl()

    assert [page.title for page in pages] == ["Page 1", "Page 2"]
    assert "Oscar Wilde" in pages[0].text
    assert "books" in pages[1].text
    assert session.calls == [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
    ]
    assert clock.value == 6.0
