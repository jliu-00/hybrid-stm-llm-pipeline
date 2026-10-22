# Initium Media Scraper

Python data extraction pipeline to retrieve news articles from specified channels (defaulting to the mainland China channel `mainland-zh-hans`) on Initium Media.

The [media name mapping](../../../MEDIA_NAMES.md) lists the official display name and the historical identifiers used in files and code.

## Core Architecture

This script is engineered to access full-text articles that are typically restricted by server-side paywalls. By injecting a valid premium subscription session token (Cookie) into the HTTP headers, the script retrieves the complete server-side payload and utilizes `newspaper3k` for structural text extraction.

## Technical Highlights

* **Authenticated Payload Retrieval:** Utilizes premium authentication cookies to bypass public preview truncations and retrieve full article content.
* **Dynamic Error Handling:** Implements exponential backoff and retry mechanisms (up to 3 attempts) to gracefully handle network packet loss, temporary timeouts, or HTTP 429 status codes.
* **Stateful Resumption:** The script logs the current time chunk index and pagination state to `scraper_state_Initium.json` in real-time. Execution automatically resumes from the exact breakpoint if interrupted.
* **Rate Limiting Protocols:** To mitigate the risk of account suspension, the script injects extended randomized sleep intervals during pagination requests (5-10 seconds) and individual article fetching (20-40 seconds).
* **Data Integrity & Versioning:** Automatically generates a timestamped backup of the existing CSV file before initiating new network requests. The final dataset is consistently sorted in reverse chronological order.

## Prerequisites

Python 3.7+ is required.

```bash
pip install requests beautifulsoup4 newspaper3k lxml_html_clean
```

## Setup & Configuration

### 1. Extract Session Cookie

To access full text, you must provide a valid premium session Cookie:

1. Access Initium Media via a desktop browser and log into your premium account.
2. Open **Developer Tools** (`F12` or Right-click -> Inspect).
3. Navigate to the **Network** tab and refresh the page (`F5`).
4. Select the primary document request (usually `theinitium.com`).
5. Scroll down to the **Request Headers** section.
6. Locate the `cookie:` field and copy the entire string.

### 2. Configure and Run

1. Open `Initium.py` in a text editor.
2. Locate the `PREMIUM_COOKIE` constant near line 20.
3. Paste your copied string within the quotation marks:
   ```python
   PREMIUM_COOKIE = "Paste your long Cookie string here"
   ```
4. Execute the script:
   ```bash
   python3 Initium.py
   ```

## Output Artifacts

* `Initium_2023_2025.csv`: The primary dataset containing the extracted content.
* `scraper_state_Initium.json`: Progress tracking state file.
* `Initium_2023_2025_backup_[timestamp].csv`: Auto-generated incremental backup files.

## Limitations & Risks

1. **Account Suspension Risk:** This script utilizes personal premium credentials. Artificially shortening the `time.sleep()` parameters significantly increases the risk of detection. High data retrieval rates can trigger backend risk control systems (e.g., Ghost CMS access logs, Cloudflare traffic monitoring), potentially leading to subscription suspension.
2. **Cookie Expiration:** Browser session cookies have a limited lifespan. If the script begins returning very short content lengths (public previews), the Cookie has expired and must be refreshed via the browser.
3. **Data Omission:** Physical network fluctuations or irregular HTML structures may cause occasional parsing failures for specific entries.

*Disclaimer: This tool is intended for academic and research purposes. Users must ensure compliance with the target website's Terms of Service and `robots.txt`.*