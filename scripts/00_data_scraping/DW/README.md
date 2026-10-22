# Deutsche Welle (DW) Scraper

Python data extraction pipeline to collect news articles from the China section of Deutsche Welle (DW).

## Core Architecture

The pipeline accesses pagination index URLs to discover article links, subsequently utilizing `BeautifulSoup4` to parse standard HTML blocks and extract article content and metadata.

## Technical Highlights

* **Time-Chunked Processing:** Segments the 2023-2025 timeline into 6-month chunks, processing them  from the newest content to the oldest.
* **Stateful Resumption:** Maintains a `dw_scraper_state.json` file to  track progress. Upon resumption, it automatically rewinds several pages to ensure no new or interspersed articles are missed.
* **Rate Limiting Protocols:** Injects randomized delays between individual article fetches to respect server resources and handle anti-scraping mechanisms.
* **Data Integrity & Versioning:** Enforces descending chronological sorting automatically after data is appended.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4
```

## Setup & Configuration

1. Open `DW.py` to view the predefined URLs and chronological chunks.
2. Execute the script:
   ```bash
   python3 DW.py
   ```

## Output Artifacts

* `DW_2023_2025.csv`: The primary dataset.
* `dw_scraper_state.json`: The state tracking file used for session resumption.

## Limitations & Risks

1. **DOM Volatility:** The extraction logic relies heavily on specific HTML classes. Upstream updates to the site's layout will necessitate code adjustments.
2. **Rate Limiting:** Continuous, high-volume requests without adequate delays may lead to temporary IP bans.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*
