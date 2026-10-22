import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
from datetime import datetime
import os
import json

# ================= Configuration Area =================
# DW pagination URL format
BASE_URL_PAGE_N = "https://www.dw.com/zh/%E4%B8%AD%E5%9B%BD/t-40349312/page-{}"

# State file for resuming interrupted scraping
STATE_FILE = "dw_scraper_state.json"
# Fixed output filename
SINGLE_OUTPUT_FILE = "DW_2023_2025.csv"

# Split 2023-2025 into 6 half-year (6 months) chunks.
# Since news is ordered newest to oldest, we scrape the most recent chunk first.
CHUNKS = [
    {"start": "2025-07-01", "end": "2025-12-31", "label": "2025_H2"},
    {"start": "2025-01-01", "end": "2025-06-30", "label": "2025_H1"},
    {"start": "2024-07-01", "end": "2024-12-31", "label": "2024_H2"},
    {"start": "2024-01-01", "end": "2024-06-30", "label": "2024_H1"},
    {"start": "2023-07-01", "end": "2023-12-31", "label": "2023_H2"},
    {"start": "2023-01-01", "end": "2023-06-30", "label": "2023_H1"},
]

# CSV column headers (English)
CSV_HEADERS = [
    'Media Name', 
    'News Title', 
    'News Date', 
    'News Content', 
    'News Link',
    'Media Region', 
    'Funding Source'
]

# Fixed field content (Modified for DW)
MEDIA_NAME = "Deutsche Welle (DW)"
MEDIA_REGION = "Germany"
FUNDING_SOURCE = "Foreign Government" 
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
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,de;q=0.7',
    }

def fetch_html(url):
    """Request webpage and return BeautifulSoup object"""
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"[-] Failed to request page: {url} | Error: {e}")
        return None

def parse_article(url):
    """Parse single article content"""
    soup = fetch_html(url)
    if not soup:
        return None
    
    # 1. Extract publication date
    # DW usually contains date in meta property="article:published_time" or name="date"
    date_meta = soup.find('meta', property='article:published_time') or \
                soup.find('meta', attrs={'name': 'date'})
    
    news_date_str = ""
    dt_obj = None
    if date_meta and date_meta.get('content'):
        raw_date = date_meta['content']
        news_date_str = raw_date.split('T')[0] # Extract YYYY-MM-DD
        try:
            dt_obj = datetime.strptime(news_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    # 2. Extract news title
    # DW titles are usually in h1 tags
    title_tag = soup.find('h1')
    if not title_tag:
        title_tag = soup.find('title')
    
    news_title = title_tag.text.strip() if title_tag else "No Title"
    
    # Clean up website suffix from title
    news_title = news_title.replace(" | DW", "").replace(" - DW", "")

    # 3. Extract news content
    # DW content is generally inside div with class containing 'rich-text' or directly in article tag
    content_div = soup.find('div', class_='rich-text')
    if not content_div:
        content_div = soup.find('article')
    if not content_div:
        content_div = soup.find('main') # Final fallback
        
    news_content = ""
    if content_div:
        # Extract all paragraphs <p>
        paragraphs = content_div.find_all('p')
        # Filter empty paragraphs and join text
        news_content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    
    return {
        'url': url,
        'title': news_title,
        'date_str': news_date_str,
        'dt_obj': dt_obj,
        'content': news_content
    }

def sort_csv_descending(filepath):
    """Read existing CSV, sort by News Date descending (newest first), and rewrite"""
    if not os.path.exists(filepath):
        return
    
    try:
        # Read existing data
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            
        # Sort by 'News Date' descending
        data.sort(key=lambda x: x['News Date'], reverse=True)
        
        # Overwrite sorted data
        with open(filepath, mode='w', encoding='utf-8-sig', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(data)
        print("[+] Global data sorted in descending chronological order!")
    except Exception as e:
        print(f"[-] Error occurred while sorting CSV file: {e}")

def main():
    # --- 1. Initialize resume state ---
    current_chunk_idx = 0
    current_page = 7  # DW list page starts from 7
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_chunk_idx = state.get("next_chunk_idx", 0)
                saved_page = state.get("last_page", 1)
                current_page = max(1, saved_page - 5) 
            print(f"[*] Save state found! Starting from chunk {current_chunk_idx+1}, adjusting start page to: Page {current_page}.")
        except Exception as e:
            print(f"[-] Failed to read save state: {e}, starting from the beginning.")

    if current_chunk_idx >= len(CHUNKS):
        print("\n[*]All 6 stages (36 months) from 2023 to 2024 have been crawled.")
        return

    # --- 2. Get target chunk for current run ---
    current_chunk = CHUNKS[current_chunk_idx]
    target_start = datetime.strptime(current_chunk["start"], "%Y-%m-%d")
    target_end = datetime.strptime(current_chunk["end"], "%Y-%m-%d")
    
    print(f"\n[*] === Crawling chunk {current_chunk_idx + 1}/{len(CHUNKS)} : {current_chunk['label']} ===")
    print(f"[*] Target time range: {current_chunk['start']} to {current_chunk['end']}")
    
    reached_older_month = False
    chunk_data = []
    seen_urls = set()
    empty_page_count = 0  # Prevent infinite loop on consecutive empty pages
    invalid_page_count = 0

    while not reached_older_month:
        # DW list direct pagination
        list_url = BASE_URL_PAGE_N.format(current_page)
            
        print(f"\n[+] Scanning page {current_page}: {list_url}")
        
        soup = fetch_html(list_url)
        if not soup:
            print("[-] Failed to retrieve list page, exiting loop.")
            break
            
        article_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # DW article links usually contain /a- and digits (e.g., /zh/xxx/a-123456)
            if '/a-' in href and re.search(r'/a-\d+', href):
                # Concatenate full domain if relative link
                full_url = href if href.startswith('http') else 'https://www.dw.com' + href
                if full_url not in seen_urls:
                    article_links.append(full_url)
                    seen_urls.add(full_url)
                
        if not article_links:
            print("[-] No new article links found on current page.")
            empty_page_count += 1
            if empty_page_count >= 5:
                print("[-] 5 consecutive empty pages, possibly reached bottom of site, forcing exit.")
                break
            current_page += 1
            continue
            
        empty_page_count = 0
        newer_count = 0
        target_count = 0
        older_count = 0
        valid_articles_checked = 0
            
        for link in article_links:
            # Add slight delay to manage request rate (random 1~2.5 seconds)
            time.sleep(random.uniform(1.0, 2.5))
            
            article_data = parse_article(link)
            if not article_data or not article_data['dt_obj']:
                continue
                
            dt = article_data['dt_obj']
            valid_articles_checked += 1
            
            if dt > target_end:
                # Later than target end time of current chunk
                newer_count += 1
                
            elif target_start <= dt <= target_end:
                # Matches target time range of current chunk
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
                # Earlier than target start time of current chunk
                print(f"  [Ignored] {dt.strftime('%Y-%m-%d')} (Older than target range) | {article_data['title'][:20]}...")
                older_count += 1
                
        # Comprehensive page-level judgment
        if valid_articles_checked > 0:
            invalid_page_count = 0
            if older_count > 0 and target_count == 0:
                print(f"\n[*] All articles on page {current_page} are older than {current_chunk['start']} (or pinned newer), chunk crawl complete!")
                reached_older_month = True
                break
            elif newer_count > 0 and target_count == 0 and older_count == 0:
                print("  [>] All articles on this page are newer, continuing to next page...")
        else:
            invalid_page_count += 1
            print(f"  [-] No valid dates could be extracted on page {current_page}.")
            if invalid_page_count >= 3:
                print("  [-] 3 consecutive pages with no valid dates. Forcing exit.")
                break
                
        current_page += 1

    # --- 3. Data saving and state update ---
    if chunk_data:
        
        
        print(f"\n[*] Crawl complete. Collected {len(chunk_data)} articles in this chunk.")
        print(f"[*] Appending to {SINGLE_OUTPUT_FILE} ...")
        
        # Check if file exists and is not empty to determine if header is needed
        file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
        write_header = not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0
        
        try:
            # Use 'a' (append) mode to write data
            with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                if write_header:
                    writer.writeheader()
                writer.writerows(chunk_data)
            print("[+] CSV document saved/appended")
            
            # --- After each append, re-sort entire document descending ---
            sort_csv_descending(SINGLE_OUTPUT_FILE)
            
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
        print(f"[+] Progress saved! Next run will continue to the next 6-month chunk.")
    except Exception as e:
        print(f"[-] Failed to save progress state: {e}")

if __name__ == "__main__":
    main()