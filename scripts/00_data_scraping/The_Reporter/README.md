# The Reporter Scraper

Python data extraction pipeline to collect articles related to specific topics or tags from The Reporter (TWReporter).

## Core Architecture

The pipeline crawls pagination endpoints to locate article and interactive content URLs. It leverages the `newspaper3k` library for structural text extraction and relies on OpenGraph meta tags for accurate publication date parsing.

## Technical Highlights

* **Time-Chunked Processing:** The overall timeline is divided into semi-annual blocks and scraped in reverse chronological order to  cover specific time ranges.
* **Stateful Resumption:** Persists the current chunk and page index to a `scraper_state_TWReporter.json` file. If interrupted, execution resumes from the exact breakpoint, utilizing a minor offset to capture intermediate updates.
* **Rate Limiting Protocols:** Employs randomized sleep intervals (1.0 to 2.5 seconds) to manage request volume and prevent server degradation.
* **Data Integrity & Versioning:** Automatically backs up the existing dataset before network requests and enforces reverse chronological sorting upon dataset updates.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4 newspaper3k lxml_html_clean
```

## Setup & Configuration

1. Ensure the target tag URL and date ranges are pre-configured within `Reporter.py`.
2. Execute the script:
   ```bash
   python3 Reporter.py
   ```

## Output Artifacts

* `TWReporter_2023_2025.csv`: The primary dataset containing the extracted content.
* `scraper_state_TWReporter.json`: State tracking file for resumable scraping.
* `TWReporter_2023_2025_backup_[timestamp].csv`: Auto-generated incremental backups.

## Limitations & Risks

1. **Interactive Content:** Special interactive articles or multimedia-heavy pages may lack clean semantic text, resulting in poor parsing by standard NLP libraries.
2. **Data Omission:** Network timeouts or structural edge cases may lead to skipped articles.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*
