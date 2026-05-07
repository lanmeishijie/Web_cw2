from __future__ import annotations

from dataclasses import dataclass

from src.indexer import SearchIndex, tokenize


@dataclass(slots=True)
class SearchResult:
    url: str
    title: str
    total_frequency: int
    matched_terms: dict[str, int]


class SearchEngine:
    def __init__(self, search_index: SearchIndex) -> None:
        self.search_index = search_index

    def print_word(self, word: str) -> dict[str, dict[str, list[int] | int]]:
        tokens = tokenize(word)
        if len(tokens) != 1:
            raise ValueError("print expects exactly one searchable word")
        return self.search_index.index.get(tokens[0], {})

    def find(self, query: str) -> list[SearchResult]:
        terms = tokenize(query)
        if not terms:
            return []

        postings_by_term = [self.search_index.index.get(term, {}) for term in terms]
        if any(not postings for postings in postings_by_term):
            return []

        page_urls = set(postings_by_term[0])
        for postings in postings_by_term[1:]:
            page_urls &= set(postings)

        results: list[SearchResult] = []
        for url in page_urls:
            matched_terms = {
                term: int(self.search_index.index[term][url]["frequency"]) for term in terms
            }
            page = self.search_index.pages[url]
            results.append(
                SearchResult(
                    url=url,
                    title=page.title,
                    total_frequency=sum(matched_terms.values()),
                    matched_terms=matched_terms,
                )
            )

        results.sort(key=lambda result: (-result.total_frequency, result.url))
        return results
