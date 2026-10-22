# BBC News Chinese Scraper

Python data extraction pipeline to collect news articles from the BBC News Chinese site.

The [media name mapping](../../../MEDIA_NAMES.md) lists the official display name and the historical identifiers used in files and code.

## Core Architecture

The pipeline utilizes the `newspaper3k` library and `BeautifulSoup4` for structural text extraction and article metadata parsing. It implements a hybrid routing strategy, handling both sitemap parsing and direct HTML pagination to discover article URLs effectively.

## Scraping Strategy

Due to URL structural modifications on the target website and a maximum limit of 40 pages on the topic pagination index, a multi-phase scraping approach is employed:

* **Post-Nov 24, 2024:** Articles published after November 24, 2024 (the earliest accessible date via pagination as of April 2026) are scraped directly using the topic pagination endpoint.
* **Pre-Nov 24, 2024:** Historical links are extracted via the Sitemap. Traditional Chinese URLs are actively filtered to prevent dataset duplication with Simplified Chinese versions.
  * **Oct 28 - Nov 24, 2024:** Articles in this window are filtered utilizing the Next.js Topic ID.
  * **Pre-Oct 28, 2024:** Prior to the site's URL restructuring, links are filtered by matching the `"chinese-news-"` pattern (the standard URL format for China-related topics at the time).

*Note: Hardcoded date intervals in the script should be manually verified and adjusted based on the earliest accessible news date available through topic pagination at the actual time of execution.*

## Technical Highlights

* **Modular Architecture:** Segregated into dedicated scripts for handling new links, historical links, sitemap processing, and data aggregation.
* **Preemptive Data Cleaning:** Implements regex-based content cleaning to remove metadata lines, reading time indicators, and image captions prior to storage. This removes website-specific structural boilerplates that `newspaper3k` frequently misidentifies as body text.
* **Stateful Resumption:** Execution progress is strictly logged to a local `scraper_state_BBC.json` file. If interrupted, subsequent runs resume from the logged breakpoint.
* **Rate Limiting Protocols:** Enforces randomized sleep intervals (e.g., 1.5 to 3.0 seconds) between network requests to simulate organic browsing behavior and prevent IP throttling.
* **Data Integrity & Versioning:** Automatically generates timestamped backups of the CSV file before initiating new network requests. Appended datasets are automatically sorted in reverse chronological order.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4 newspaper3k lxml_html_clean
```

## Setup & Execution

Execute the pipeline sequentially:

```bash
python3 BBC_NewLinks.py
python3 BBC_Sitemap.py
python3 BBC_OldLinks.py
python3 BBC_Merge.py
```

## Output Artifacts

* `BBC_NewLinks.csv` / `BBC_OldLinks.csv`: Intermediate datasets.
* `BBC_2023_2025.csv`: Final merged and sorted dataset.
* `BBC_chinese_index_2023_2024.json`: Filtered sitemap URL index.
* `scraper_state_BBC.json` / `content_scraper_state.json`: State tracking files.
* `*_backup_[timestamp].csv`: Auto-generated incremental backups.

## Limitations & Risks

1. **Rate Limiting and Blocking:** High data retrieval rates can trigger backend risk control systems. Built-in delays are essential to mitigate this.
2. **DOM Volatility:** Structural changes to the target website's layout may require updates to the parsing logic.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*
