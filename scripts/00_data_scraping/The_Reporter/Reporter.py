import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from datetime import datetime
import os
import json
import shutil
from urllib.parse import urljoin
from newspaper import Article, Config

# ================= Configuration Area =================
BASE_DOMAIN = "https://www.twreporter.org"
BASE_URL_PAGE_1 = "https://www.twreporter.org/tag/5768ed08406be01000c69076?page=1"
BASE_URL_PAGE_N = "https://www.twreporter.org/tag/5768ed08406be01000c69076?page={}"

# Ensure files are saved in the exact same directory as the script regardless of terminal location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# State archive file for resumable scraping
STATE_FILE = os.path.join(SCRIPT_DIR, "scraper_state_TWReporter.json")
# Fixed output filename
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "TWReporter_2023_2025.csv")

# Split 2023-2025 into 6 half-year intervals.
# Executed in reverse chronological order.
CHUNKS = [
    {"start": "2025-07-01", "end": "2025-12-31", "label": "2025_H2"},
    {"start": "2025-01-01", "end": "2025-06-30", "label": "2025_H1"},
    {"start": "2024-07-01", "end": "2024-12-31", "label": "2024_H2"},
    {"start": "2024-01-01", "end": "2024-06-30", "label": "2024_H1"},
    {"start": "2023-07-01", "end": "2023-12-31", "label": "2023_H2"},
    {"start": "2023-01-01", "end": "2023-06-30", "label": "2023_H1"},
]

# CSV column headers (all English)
CSV_HEADERS = [
    'Media Name', 
    'News Title', 
    'News Date', 
    'News Content', 
    'News Link',  
    'Media Region', 
    'Funding Source'
]

# Fixed field content according to specification
MEDIA_NAME = "The Reporter"
MEDIA_REGION = "Taiwan"
FUNDING_SOURCE = "Independent Media" 
# ============================================

def get_headers():
    """Generate random User-Agent to manage request behavior"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.twreporter.org/'
    }

def fetch_html_and_text(url):
    """Request webpage and return BeautifulSoup object and raw text payload"""
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser'), response.text
    except requests.RequestException as e:
        print(f"[-] Failed to request page: {url} | Error: {e}")
        return None, ""

def parse_article(url):
    """Parse content and metadata of a single TWReporter article using Newspaper3k with DOM fallback."""
    config = Config()
    headers = get_headers()
    config.browser_user_agent = headers['User-Agent']
    config.request_timeout = 15

    try:
        article = Article(url, config=config)
        article.download()
        
        # Verify download state before parsing
        if article.download_state == 0:  
            print(f"  [-] Failed to download article via Newspaper3k: {url}")
            return None
            
        article.parse()
    except Exception as e:
        print(f"  [-] Newspaper3k encountered an error parsing {url}: {e}")
        return None

    # 1. Extract publish date
    dt_obj = article.publish_date
    if not dt_obj:
        # Fallback: Manually parse HTML for OpenGraph article metadata used by The Reporter
        soup = BeautifulSoup(article.html, 'html.parser')
        meta_pub = soup.find('meta', property='article:published_time')
        if meta_pub and meta_pub.get('content'):
            try:
                # Meta content format is usually ISO 8601 (e.g., 2024-05-23T04:00:00Z)
                dt_str = meta_pub['content'][:10]
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")
            except ValueError:
                pass

    if not dt_obj:
        print(f"  [-] Failed to extract date for {url}, skipping.")
        return None

    # Strip timezone info to allow comparison with naive datetimes
    dt_obj = dt_obj.replace(tzinfo=None)

    news_date_str = dt_obj.strftime("%Y-%m-%d")

    # 2. Extract news title and clean up site suffix
    news_title = article.title if article.title else "No Title"
    news_title = news_title.replace(" - 報導者 The Reporter", "").strip()

    # 3. Extract news content
    news_content = article.text.strip()
    
    return {
        'url': url,
        'title': news_title,
        'date_str': news_date_str,
        'dt_obj': dt_obj,
        'content': news_content
    }

def sort_csv_reverse_chronologically(filepath):
    """Read existing CSV file, sort by news date in reverse chronological order, and rewrite"""
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
        print("[+] Global data rearranged in reverse chronological order!")
    except Exception as e:
        print(f"[-] Error occurred while sorting CSV file: {e}")

def backup_existing_csv(filepath):
    """Backup the existing CSV file before running to avoid data corruption"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(filepath)
        backup_filepath = f"{base}_backup_{timestamp}{ext}"
        try:
            shutil.copy2(filepath, backup_filepath)
            print(f"[+] Backup created: {backup_filepath}")
        except Exception as e:
            print(f"[-] Backup failed: {e}")
    else:
        print("[*] Target CSV file not created yet, skipping backup.")

def main():
    # --- 0. Backup existing data ---
    backup_existing_csv(SINGLE_OUTPUT_FILE)

    # --- 1. Initialize resumable scraping state ---
    current_chunk_idx = 0
    current_page = 1  
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_chunk_idx = state.get("next_chunk_idx", 0)
                saved_page = state.get("last_page", 4)
                current_page = max(1, saved_page - 5) 
            print(f"[*] Archive state found! Will start from chunk {current_chunk_idx+1}, starting page adjusted to: Page {current_page}.")
        except Exception as e:
            print(f"[-] Failed to read archive: {e}, will start from the default setting.")

    if current_chunk_idx >= len(CHUNKS):
        print("\n[*] All phases have been processed")
        return

    # --- 2. Get target chunk for current run ---
    current_chunk = CHUNKS[current_chunk_idx]
    target_start = datetime.strptime(current_chunk["start"], "%Y-%m-%d")
    target_end = datetime.strptime(current_chunk["end"], "%Y-%m-%d")
    
    print(f"\n[*] === Scraping chunk {current_chunk_idx + 1}/{len(CHUNKS)} : {current_chunk['label']} ===")
    print(f"[*] Target time range: {current_chunk['start']} to {current_chunk['end']}")
    
    reached_older_month = False
    chunk_data = []
    seen_urls = set()
    empty_page_count = 0  
    invalid_page_count = 0

    while not reached_older_month:
        if current_page == 1:
            list_url = BASE_URL_PAGE_1
        else:
            list_url = BASE_URL_PAGE_N.format(current_page)
            
        print(f"\n[+] Scanning page {current_page}: {list_url}")
        
        soup, raw_text = fetch_html_and_text(list_url)
        if not raw_text:
            print("[-] Failed to fetch list page, exiting loop.")
            break
            
        article_links = []
        
        # Standard DOM parser mapping for TWReporter architecture
        if soup:
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # The Reporter articles use '/a/' (article) or '/i/' (interactive) paths
                if href.startswith('/a/') or href.startswith('/i/'):
                    full_url = urljoin(BASE_DOMAIN, href).split('?')[0].split('#')[0]
                    if full_url not in seen_urls:
                        article_links.append(full_url)
                        seen_urls.add(full_url)
                
        if not article_links:
            print("[-] No valid article links found on current page.")
            empty_page_count += 1
            if empty_page_count >= 5:
                print("[-] No data for 5 consecutive pages. Assumed bottom of the index, forcing exit.")
                break
            current_page += 1
            continue
            
        empty_page_count = 0
        newer_count = 0
        target_count = 0
        older_count = 0
        valid_articles_checked = 0
            
        for link in article_links:
            # TWReporter URLs lack dates. Data must be requested and verified from the DOM.
            time.sleep(random.uniform(1.0, 2.5)) 
            
            article_data = parse_article(link)
            if not article_data or not article_data['dt_obj']:
                continue
                
            dt = article_data['dt_obj']
            valid_articles_checked += 1
            
            if dt > target_end:
                newer_count += 1
            elif target_start <= dt <= target_end:
                print(f"  [Collected] {dt.strftime('%Y-%m-%d')} | {article_data['title'][:30]}...")
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
                print(f"  [Ignored] {dt.strftime('%Y-%m-%d')} (earlier than target range) | {article_data['title'][:20]}...")
                older_count += 1
                
        if valid_articles_checked > 0:
            invalid_page_count = 0
            if older_count > 0 and target_count == 0:
                print(f"\n[*] All articles on page {current_page} are earlier than {current_chunk['start']} (or pinned newer), current chunk scraping finished!")
                reached_older_month = True
                break
            elif newer_count > 0 and target_count == 0 and older_count == 0:
                print("  [>] All articles on this page are newer, keep flipping to find...")
        else:
            invalid_page_count += 1
            print(f"  [-] No valid dates could be extracted on page {current_page}.")
            if invalid_page_count >= 3:
                print("  [-] 3 consecutive pages with no valid dates. Forcing exit.")
                break
                
        current_page += 1

    # --- 3. Data saving and state update ---
    if chunk_data:
        print(f"\n[*] Scraping finished. Collected {len(chunk_data)} articles in this chunk.")
        print(f"[*] Appending to {SINGLE_OUTPUT_FILE} ...")
        
        file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
        write_header = not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0
        
        try:
            with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                if write_header:
                    writer.writeheader()
                writer.writerows(chunk_data)
            print("[+] CSV document saved/appended")
            
            sort_csv_reverse_chronologically(SINGLE_OUTPUT_FILE)
            
        except IOError as e:
            print(f"[-] Error occurred while saving CSV: {e}")
            
    # Save state for next run
    new_state = {
        "next_chunk_idx": current_chunk_idx + 1,
        "last_page": current_page
    }
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(new_state, f)
        print(f"[+] Progress archived! Next run will execute the next time interval defined in CHUNKS.")
    except Exception as e:
        print(f"[-] Failed to save archive: {e}")

if __name__ == "__main__":
    main()