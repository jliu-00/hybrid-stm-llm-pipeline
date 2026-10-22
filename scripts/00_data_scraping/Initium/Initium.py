import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
from datetime import datetime
import os
import json
import shutil
from urllib.parse import urljoin
from newspaper import Article, Config

# ================= Configuration Area =================
BASE_DOMAIN = "https://theinitium.com"
BASE_URL_PAGE_1 = "https://theinitium.com/tag/mainland-zh-hans/"
BASE_URL_PAGE_N = "https://theinitium.com/tag/mainland-zh-hans/page/{}/"

# Paste your valid Cookie string within the quotes below
PREMIUM_COOKIE = "Paste your long Cookie string here"

# State archive file for resumable scraping
STATE_FILE = "scraper_state_Initium.json"
# Output filename
SINGLE_OUTPUT_FILE = "Initium_2023_2025.csv"

# Split 2023-2025 into 3-month (quarterly) intervals.
# First chunk is strictly isolated to December 2025 for testing purposes.
CHUNKS = [
    {"start": "2025-12-01", "end": "2025-12-31", "label": "2025_12_Test"},
    {"start": "2025-09-01", "end": "2025-11-30", "label": "2025_Sep_Nov"},
    {"start": "2025-06-01", "end": "2025-08-31", "label": "2025_Jun_Aug"},
    {"start": "2025-03-01", "end": "2025-05-31", "label": "2025_Mar_May"},
    {"start": "2024-12-01", "end": "2025-02-28", "label": "2024_Dec_2025_Feb"},
    {"start": "2024-09-01", "end": "2024-11-30", "label": "2024_Sep_Nov"},
    {"start": "2024-06-01", "end": "2024-08-31", "label": "2024_Jun_Aug"},
    {"start": "2024-03-01", "end": "2024-05-31", "label": "2024_Mar_May"},
    {"start": "2023-12-01", "end": "2024-02-29", "label": "2023_Dec_2024_Feb"},
    {"start": "2023-09-01", "end": "2023-11-30", "label": "2023_Sep_Nov"},
    {"start": "2023-06-01", "end": "2023-08-31", "label": "2023_Jun_Aug"},
    {"start": "2023-03-01", "end": "2023-05-31", "label": "2023_Mar_May"},
    {"start": "2023-01-01", "end": "2023-02-28", "label": "2023_Jan_Feb"}
]

CSV_HEADERS = [
    'Media Name', 'News Title', 'News Date', 'News Content', 'News Link', 'Media Region', 'Funding Source'
]

MEDIA_NAME = "The Initium"
MEDIA_REGION = "Singapore"
FUNDING_SOURCE = "Independent Media"
# ====================================================

# Ensure files are saved in the script's execution directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, STATE_FILE)
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, SINGLE_OUTPUT_FILE)


def get_headers():
    """Generate request headers."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
    ]
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
        'Referer': 'https://theinitium.com/'
    }
    # Inject Cookie into headers
    if PREMIUM_COOKIE and "Paste_Your_Cookie_Here" not in PREMIUM_COOKIE:
        headers['Cookie'] = PREMIUM_COOKIE
    return headers

def extract_date_from_url(url):
    """Extract publish date from the article URL."""
    match = re.search(r'/(\d{8})-', url)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            pass
    return None

def parse_article(url):
    """Parse article content using Newspaper3k with request headers."""
    config = Config()
    headers = get_headers()
    config.browser_user_agent = headers['User-Agent']
    config.headers = headers 
    config.request_timeout = 20

    try:
        article = Article(url, config=config)
        article.download()
        
        if article.download_state == 0:
            print(f"  [-] Failed to download article: {url}")
            return None
            
        article.parse()
    except Exception as e:
        print(f"  [-] Error parsing {url}: {e}")
        return None

    dt_obj = article.publish_date
    if not dt_obj:
        dt_obj = extract_date_from_url(url)
        
    news_date_str = dt_obj.strftime("%Y-%m-%d") if dt_obj else ""
    news_title = article.title.replace("｜端传媒 Initium Media", "").strip() if article.title else "No Title"
    
    # Extract the full article text
    news_content = article.text.strip()
    
    return {
        'url': url,
        'title': news_title,
        'date_str': news_date_str,
        'dt_obj': dt_obj,
        'content': news_content
    }

def sort_csv_reverse_chronologically(filepath):
    """Sort the CSV file by date in descending order."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        data.sort(key=lambda x: x['News Date'], reverse=True)
        with open(filepath, mode='w', encoding='utf-8-sig', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(data)
        print("[+] CSV data successfully sorted in reverse chronological order.")
    except Exception as e:
        pass

def backup_existing_csv(filepath):
    """Create a backup of the existing CSV file before writing new data."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(filepath)
        backup_filepath = f"{base}_backup_{timestamp}{ext}"
        try:
            shutil.copy2(filepath, backup_filepath)
            print(f"[*] Backup created: {backup_filepath}")
        except Exception:
            pass

def main():
    if "Paste_Your_Cookie_Here" in PREMIUM_COOKIE:
        print("[-] Error: Please configure your PREMIUM_COOKIE at the top of the script.")
        return

    # Backup existing data file before modifying it
    backup_existing_csv(SINGLE_OUTPUT_FILE)

    current_chunk_idx = 0
    
    # Set the starting page here. Change this number to start from a different page.
    current_page = 2
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_chunk_idx = state.get("next_chunk_idx", 0)
                saved_page = state.get("last_page", 2)
                current_page = max(1, saved_page - 5) 
            print(f"[*] State file found. Resuming from chunk {current_chunk_idx+1}, page {current_page}.")
        except Exception:
            pass

    if current_chunk_idx >= len(CHUNKS):
        print("\n[*] All defined chunks have been scraped.")
        return

    current_chunk = CHUNKS[current_chunk_idx]
    target_start = datetime.strptime(current_chunk["start"], "%Y-%m-%d")
    target_end = datetime.strptime(current_chunk["end"], "%Y-%m-%d")
    
    print(f"\n[*] === Scraping chunk {current_chunk_idx + 1}/{len(CHUNKS)} : {current_chunk['label']} ===")
    
    reached_older_month = False
    chunk_data = []
    seen_urls = set()
    empty_page_count = 0  
    invalid_page_count = 0

    while not reached_older_month:
        url = BASE_URL_PAGE_N.format(current_page) if current_page > 1 else BASE_URL_PAGE_1
        print(f"\n[+] Scanning page {current_page}...")
        
        # Add delay between pagination requests
        if current_page > 1:
            page_delay = random.uniform(5.0, 10.0)
            print(f"  [Wait] Delaying {page_delay:.1f}s before loading the next page...")
            time.sleep(page_delay)

        MAX_RETRIES = 3
        retry_count = 0
        success = False

        while retry_count < MAX_RETRIES and not success:
            try:
                response = requests.get(url, headers=get_headers(), timeout=20)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                raw_text = response.text
                success = True
                
            except requests.RequestException as e:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    wait_time = 60 * retry_count
                    print(f"  [-] Request error: {e}. Retrying {retry_count}/{MAX_RETRIES} in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  [-] Failed to fetch page {current_page} after {MAX_RETRIES} attempts. Skipping to save progress.")
                    reached_older_month = True
                    break

        if not success:
            break 
            
        paths = re.findall(r'["\'](/\d{8}-[a-zA-Z0-9\-]+/?)["\']', raw_text)
        urls = re.findall(r'["\'](https://theinitium.com/\d{8}-[a-zA-Z0-9\-]+/?)["\']', raw_text)
            
        all_raw_links = set(paths + urls)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if re.search(r'^/?\d{8}-', href) and not href.endswith('#comments'):
                all_raw_links.add(href)
                
        article_links = []
        for raw_link in all_raw_links:
            clean_link = raw_link.replace('\\/', '/').split('?')[0].split('#')[0]
            full_url = urljoin(BASE_DOMAIN, clean_link)
            if full_url not in seen_urls:
                article_links.append(full_url)
                seen_urls.add(full_url)
                
        if not article_links:
            empty_page_count += 1
            if empty_page_count >= 3:
                break
            current_page += 1
            continue
            
        empty_page_count = 0
        newer_count = 0
        target_count = 0
        older_count = 0
        valid_articles_checked = 0
            
        for link in article_links:
            url_dt = extract_date_from_url(link)
            if url_dt:
                if url_dt > target_end:
                    newer_count += 1
                    continue
                elif url_dt < target_start:
                    older_count += 1
                    continue

            # Request delay for individual articles
            delay = random.uniform(20.0, 40.0)
            print(f"  [Wait] Delaying {delay:.1f}s before fetching article...")
            time.sleep(delay)
            
            article_data = parse_article(link)
            if not article_data or not article_data['dt_obj']:
                continue
                
            dt = article_data['dt_obj']
            valid_articles_checked += 1
            
            if dt > target_end:
                newer_count += 1
            elif target_start <= dt <= target_end:
                content_preview = article_data['content'][:30].replace("\n", "")
                content_length = len(article_data['content'])
                print(f"  [Collected] {dt.strftime('%Y-%m-%d')} | Length: {content_length} chars | {content_preview}...")
                
                target_count += 1
                chunk_data.append({
                    'Media Name': MEDIA_NAME,
                    'News Title': article_data['title'],
                    'News Date': article_data['date_str'],
                    'News Content': article_data['content'],
                    'News Link': article_data['url'],
                    'Media Region': MEDIA_REGION,
                    'Funding Source': FUNDING_SOURCE
                })
            elif dt < target_start:
                older_count += 1
                
        total_valid = newer_count + target_count + older_count
        if total_valid > 0:
            invalid_page_count = 0
            if older_count > 0 and target_count == 0:
                print(f"\n[*] Reached articles older than the target timeframe. Chunk processing complete.")
                reached_older_month = True
                break
        else:
            invalid_page_count += 1
            print(f"  [-] No valid dates could be extracted on page {current_page}.")
            if invalid_page_count >= 3:
                print("  [-] 3 consecutive pages with no valid dates. Forcing exit.")
                break
                
        current_page += 1

    if chunk_data:
        file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
        write_header = not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0
        try:
            with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                if write_header:
                    writer.writeheader()
                writer.writerows(chunk_data)
            print("[+] Data appended to CSV successfully.")
            sort_csv_reverse_chronologically(SINGLE_OUTPUT_FILE)
        except IOError as e:
            print(f"[-] IO Error during file writing: {e}")
            
    new_state = {"next_chunk_idx": current_chunk_idx + 1, "last_page": current_page}
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(new_state, f)
    except Exception as e:
        print(f"[-] Error saving state file: {e}")

if __name__ == "__main__":
    main()