from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
from typing import Sequence

from src.crawler import CrawlerError, QuoteCrawler
from src.indexer import SearchIndex, build_index, load_index, save_index
from src.search import SearchEngine

DEFAULT_INDEX_PATH = Path("data/index.json")


class SearchToolApp:
    def __init__(self, index_path: Path = DEFAULT_INDEX_PATH) -> None:
        self.index_path = index_path
        self.search_index: SearchIndex | None = None

    def build(self) -> str:
        crawler = QuoteCrawler()
        pages = crawler.crawl()
        self.search_index = build_index(pages)
        saved_to = save_index(self.search_index, self.index_path)
        return f"Built index with {len(pages)} pages and saved it to {saved_to}"

    def load(self) -> str:
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        self.search_index = load_index(self.index_path)
        page_count = self.search_index.metadata.get("page_count", len(self.search_index.pages))
        return f"Loaded index from {self.index_path} ({page_count} pages)"

    def print_word(self, word: str) -> str:
        engine = SearchEngine(self._require_index())
        postings = engine.print_word(word)
        if not postings:
            return f"No postings found for '{word}'."
        return json.dumps(postings, indent=2, sort_keys=True)

    def find(self, query: str) -> str:
        engine = SearchEngine(self._require_index())
        results = engine.find(query)
        if not query.strip():
            return "Empty query. Please provide one or more search terms."
        if not results:
            return f"No pages matched '{query}'."

        lines = []
        for result in results:
            lines.append(
                f"{result.url} | {result.title} | total_frequency={result.total_frequency} | matched_terms={result.matched_terms}"
            )
        return "\n".join(lines)

    def run_shell(self) -> int:
        print("Search tool shell. Commands: build, load, print <word>, find <query>, help, exit")

        while True:
            try:
                raw_command = input("> ").strip()
            except EOFError:
                print()
                return 0

            if not raw_command:
                continue

            if raw_command.lower() in {"exit", "quit"}:
                return 0

            try:
                output = self.execute(raw_command)
            except Exception as exc:  # pragma: no cover - exercised via direct commands
                output = f"Error: {exc}"

            if output:
                print(output)

    def execute(self, command_line: str) -> str:
        parts = shlex.split(command_line)
        if not parts:
            return ""

        command = parts[0].lower()
        arguments = parts[1:]

        if command == "help":
            return "Commands: build, load, print <word>, find <query>, help, exit"
        if command == "build":
            return self.build()
        if command == "load":
            return self.load()
        if command == "print":
            if len(arguments) != 1:
                raise ValueError("Usage: print <word>")
            return self.print_word(arguments[0])
        if command == "find":
            if not arguments:
                return "Empty query. Please provide one or more search terms."
            return self.find(" ".join(arguments))

        raise ValueError(f"Unknown command: {command}")

    def _require_index(self) -> SearchIndex:
        if self.search_index is None:
            self.search_index = load_index(self.index_path)
        return self.search_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Coursework search engine tool")
    parser.add_argument(
        "--index-file",
        default=str(DEFAULT_INDEX_PATH),
        help="Path to the compiled index file",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("build", help="Crawl the website and build the index")
    subparsers.add_parser("load", help="Load an existing index file")

    print_parser = subparsers.add_parser("print", help="Print the postings for a word")
    print_parser.add_argument("word")

    find_parser = subparsers.add_parser("find", help="Find pages matching an AND query")
    find_parser.add_argument("terms", nargs=argparse.REMAINDER)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    app = SearchToolApp(index_path=Path(args.index_file))
    if args.command is None:
        return app.run_shell()

    try:
        if args.command == "build":
            print(app.build())
        elif args.command == "load":
            print(app.load())
        elif args.command == "print":
            print(app.print_word(args.word))
        elif args.command == "find":
            print(app.find(" ".join(args.terms)))
        else:
            parser.error(f"Unsupported command: {args.command}")
    except (CrawlerError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    return 0
