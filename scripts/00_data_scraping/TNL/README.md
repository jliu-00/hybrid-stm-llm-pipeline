# The News Lens Scraper

Python data extraction pipeline to collect news articles from the China category of The News Lens (TNL).

## Core Architecture

The pipeline traverses pagination endpoints to discover article links and utilizes `BeautifulSoup4` to extract structural text and publication metadata directly from the HTML DOM.

## Technical Highlights

* **Targeted Extraction:** Focuses specifically on the `/category/china/` section, extracting content by explicitly identifying the main semantic article container blocks.
* **Time-Chunked Execution:** Partitions the target timeline (e.g., 2023-2025) into half-year intervals, processing them iteratively in reverse chronological order.
* **Stateful Resumption:** Progress is logged to a local `scraper_state_TNL.json` file in real-time, allowing execution to resume automatically from the current time chunk and page following any interruptions.
* **Rate Limiting Protocols:** Injects randomized sleep intervals between article requests to simulate human reading velocity and prevent server overload.
* **Data Integrity & Versioning:** Reorganizes the entire dataset in reverse chronological order (newest to oldest) after each update.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4
```

## Setup & Configuration

1. Open `TNL.py` in a text editor to verify the predefined date chunks and base URLs. No additional authentication or cookies are required.
2. Execute the script:
   ```bash
   python3 TNL.py
   ```

## Output Artifacts

* `TNL_2023_2025.csv`: The primary dataset containing the extracted content.
* `scraper_state_TNL.json`: Progress tracking file. Do not manually edit unless resetting progress.

## Limitations & Risks

1. **DOM Volatility:** If the website updates its HTML class names or DOM structure, the extraction logic will fail and require manual selector updates.
2. **Rate Limiting:** Scraping without appropriate delays may trigger upstream anti-scraping mechanisms.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*
