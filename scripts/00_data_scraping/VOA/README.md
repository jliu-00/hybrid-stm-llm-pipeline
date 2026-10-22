# VOA Scraper

Python data extraction pipeline to collect news articles from the VOA Chinese site, specifically targeting the "China" category.

## Core Architecture

The extraction process is modularized into a 4-stage pipeline. It utilizes `newspaper3k` and `BeautifulSoup4` for text extraction and DOM parsing, integrating direct pagination scraping with sitemap traversal to bypass server-side pagination limits.

## Scraping Strategy

The target server generally imposes a hard limit of 100 pages on category pagination archives. To retrieve historical data predating this threshold without relying on imprecise search engine queries, the pipeline executes the following phases:

### Phase 1: Pagination Scraper (`VOA_NewLinks.py`)
* Extracts the most recent articles accessible via category pagination (up to page 100).
* Persists the oldest successfully scraped date to a local state file (`voa_boundary_state.json`), establishing the boundary for the sitemap phase.

### Phase 2: Sitemap Indexer (`VOA_Sitemap.py`)
* Fetches and decompresses `sitemap.xml` and nested `.xml.gz` archives to build a comprehensive URL index.
* Filters URLs based on the `lastmod` attribute, retaining entries modified between the target start date and the boundary date recorded in Phase 1.
* Serializes the filtered URLs to `VOA_index_old.json`.

### Phase 3: Historical Content Scraper (`VOA_OldLinks.py`)
* **Challenge:** Sitemap URLs lack category metadata.
* **Resolution:** Implements strict metadata filtering by parsing the HTML source and verifying the presence of the `"中国"` keyword within the `<meta name="keywords">` tag.
* Parses and saves valid articles to `VOA_OldLinks.csv`.

### Phase 4: Data Merging (`VOA_Merge.py`)
* Aggregates datasets from Phase 1 and Phase 3.
* Enforces global deduplication based on article URLs.
* Sorts the final dataset in reverse chronological order, outputting to `VOA_2023_2025.csv`.

## Technical Highlights

* **Dual-Engine Routing:** Circumvents server-side pagination limits by  transitioning from direct pagination scraping to exhaustive sitemap extraction.
* **High-Concurrency Fan-Out/Fan-In:** Employs `concurrent.futures.ThreadPoolExecutor` for network I/O bound tasks while funneling disk writes to a sequential, lock-free main thread to prevent data corruption.
* **Real-Time Memory Flushing:** Flushes parsed data directly to the local CSV after each processed page/article to prevent memory exhaustion and data loss.
* **Stateful Resumption & Fault Tolerance:**  logs progress to local JSON state files, allowing execution to resume exactly from the last saved checkpoint in the event of network failure.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4 newspaper3k lxml_html_clean
```

## Setup & Execution

Execute the pipeline sequentially:

```bash
python3 VOA_NewLinks.py
python3 VOA_Sitemap.py
python3 VOA_OldLinks.py
python3 VOA_Merge.py
```

## Output Artifacts

* `VOA_NewLinks.csv` / `VOA_OldLinks.csv`: Intermediate datasets.
* `VOA_2023_2025.csv`: Final merged and sorted dataset.
* `VOA_index_old.json`: Filtered sitemap URL index.
* `*.json`: State files for progress tracking.

## Limitations & Risks

1. **Meta Tag Constraints:** Articles tagged under related keywords (e.g., "美中关系") without explicitly including the target keyword may be excluded.
2. **Sitemap `lastmod` Volatility:** Recently updated older articles might fall outside the historical `lastmod` filter window.
3. **Rate Limiting:** High-frequency requests may trigger anti-scraping mechanisms. Built-in sleep intervals mitigate this risk but increase execution time.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*
