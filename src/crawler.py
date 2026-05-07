from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class CrawlerError(RuntimeError):
    """Raised when the crawler cannot retrieve or parse a page."""


@dataclass(slots=True)
class PageContent:
    url: str
    title: str
    text: str


class QuoteCrawler:
    """Crawl quote listing pages while respecting the coursework politeness rule."""

    def __init__(
        self,
        base_url: str = "https://quotes.toscrape.com/",
        politeness_window: float = 6.0,
        session: requests.Session | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url
        self.politeness_window = politeness_window
        self.session = session or requests.Session()
        self.sleeper = sleeper
        self.clock = clock
        self.timeout = timeout
        self.last_request_time: float | None = None
        self.session.headers.setdefault(
            "User-Agent",
            "Web2CourseworkSearchTool/1.0 (+https://quotes.toscrape.com/)",
        )

    def crawl(self) -> list[PageContent]:
        pages: list[PageContent] = []
        next_url = self.base_url
        visited: set[str] = set()

        while next_url:
            if next_url in visited:
                break

            visited.add(next_url)
            response = self._get(next_url)
            page, next_url = self._parse_page(response.text, response.url)
            pages.append(page)

        return pages

    def _get(self, url: str) -> requests.Response:
        self._wait_for_politeness()

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CrawlerError(f"Failed to fetch {url}: {exc}") from exc

        self.last_request_time = self.clock()
        return response

    def _wait_for_politeness(self) -> None:
        if self.last_request_time is None:
            return

        elapsed = self.clock() - self.last_request_time
        remaining = self.politeness_window - elapsed
        if remaining > 0:
            self.sleeper(remaining)

    def _parse_page(self, html: str, page_url: str) -> tuple[PageContent, str | None]:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else page_url
        quote_blocks = soup.select("div.quote")

        if not quote_blocks:
            raise CrawlerError(f"No quote blocks found in {page_url}")

        fragments: list[str] = []
        for block in quote_blocks:
            quote_text = block.select_one("span.text")
            author = block.select_one("small.author")
            tags = [tag.get_text(strip=True) for tag in block.select("div.tags a.tag")]

            if quote_text:
                fragments.append(quote_text.get_text(" ", strip=True))
            if author:
                fragments.append(author.get_text(" ", strip=True))
            if tags:
                fragments.append(" ".join(tags))

        next_link = soup.select_one("li.next a[href]")
        next_url = urljoin(page_url, next_link["href"]) if next_link else None
        page_text = "\n".join(fragments)

        return PageContent(url=page_url, title=title, text=page_text), next_url
