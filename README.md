# Search Engine Tool Coursework

This project implements a small search engine for `https://quotes.toscrape.com/` as required by the coursework brief. It crawls the quote listing pages, builds an inverted index with word frequencies and positions, saves the index to disk, and supports command-line search operations.

## Project Structure

```text
repository-name/
src/
  crawler.py
  indexer.py
  search.py
  main.py
tests/
  test_crawler.py
  test_indexer.py
  test_search.py
data/
  index.json
requirements.txt
README.md
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the shell:

```bash
python main.py
```

Run the coursework commands directly:

```bash
python main.py build
python main.py load
python main.py print nonsense
python main.py find good friends
```

Optional custom index path:

```bash
python main.py --index-file data/custom-index.json build
```

## Search Behaviour

- Crawls only the quote listing pagination pages from the target website.
- Enforces a 6-second politeness window between successive HTTP requests.
- Normalises words to lowercase so search is case-insensitive.
- `find` uses AND semantics, so every returned page must contain all query words.
- Results are sorted by the sum of matched term frequencies in descending order.

## Testing

```bash
pytest --cov=src --cov-report=term-missing
```

## Dependencies

- `requests`
- `beautifulsoup4`
- `pytest`
- `pytest-cov`
