from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from src.crawler import PageContent

WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


@dataclass(slots=True)
class PageRecord:
    title: str
    word_count: int


@dataclass(slots=True)
class SearchIndex:
    metadata: dict[str, Any]
    pages: dict[str, PageRecord]
    index: dict[str, dict[str, dict[str, list[int] | int]]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata,
            "pages": {url: asdict(page) for url, page in self.pages.items()},
            "index": self.index,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SearchIndex":
        pages = {
            url: PageRecord(**page_payload)
            for url, page_payload in payload.get("pages", {}).items()
        }
        return cls(
            metadata=payload.get("metadata", {}),
            pages=pages,
            index=payload.get("index", {}),
        )


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in WORD_PATTERN.finditer(text)]


def build_index(pages: list[PageContent]) -> SearchIndex:
    inverted_index: dict[str, dict[str, dict[str, list[int] | int]]] = {}
    page_records: dict[str, PageRecord] = {}

    for page in pages:
        tokens = tokenize(page.text)
        page_records[page.url] = PageRecord(title=page.title, word_count=len(tokens))

        for position, token in enumerate(tokens, start=1):
            postings = inverted_index.setdefault(token, {})
            posting = postings.setdefault(page.url, {"frequency": 0, "positions": []})
            posting["frequency"] += 1
            posting["positions"].append(position)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "word_count": len(inverted_index),
    }
    return SearchIndex(metadata=metadata, pages=page_records, index=inverted_index)


def save_index(search_index: SearchIndex, destination: str | Path) -> Path:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(
        json.dumps(search_index.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return destination_path


def load_index(source: str | Path) -> SearchIndex:
    source_path = Path(source)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    return SearchIndex.from_dict(payload)
