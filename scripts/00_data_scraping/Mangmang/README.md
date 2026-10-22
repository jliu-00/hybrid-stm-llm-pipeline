# Mang Mang Scraper

Python data extraction pipeline to collect articles from the Mang Mang archive.

The [media name mapping](../../../MEDIA_NAMES.md) lists the official display name and the historical identifiers used in files and code.

## Core Architecture

The pipeline accesses article listings through a multi-strategy discovery mechanism involving Sitemap XML parsing, JSON API pagination, and direct HTML scraping. It utilizes `newspaper3k` with fallback DOM parsing for comprehensive text and metadata extraction.

## Technical Highlights

* **Multi-Strategy Link Discovery:** Attempts to fetch article links using the site's Sitemap first, falls back to JSON API pagination endpoints, and ultimately defaults to basic HTML parsing if prior methods fail.
* **Date Parsing:** In addition to standard OpenGraph metadata extraction, it parses JSON-LD structured data and specific HTML `<time>` tags to ensure accurate publication dates.
* **Stateful Resumption:** Designed to resume operations  to prevent redundant data fetching.
* **Rate Limiting Protocols:** Implements randomized sleep intervals to throttle concurrent request rates and prevent server overload.
* **Data Integrity & Versioning:** Automatically generates timestamped backups of the CSV file prior to execution and enforces reverse chronological sorting upon dataset updates.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4 newspaper3k lxml_html_clean
```

## Setup & Configuration

1. Open `Mangmang.py` in a text editor.
2. Configure the target date range via the `TARGET_START_STR` and `TARGET_END_STR` variables.
3. Execute the script:
   ```bash
   python3 Mangmang.py
   ```

## Output Artifacts

* `Mangmang_2023_2025.csv`: The primary dataset containing collected articles and metadata.
* `Mangmang_2023_2025_backup_[timestamp].csv`: Auto-generated incremental backups.

## Limitations & Risks

1. **JavaScript-Rendered Content:** Articles heavily reliant on dynamic client-side rendering (CSR) might not be fully parsed by standard synchronous requests, although DOM fallbacks capture main content blocks.
2. **Rate Limiting:** High request rates could result in IP throttling or server-side blocks.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*
