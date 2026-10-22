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
BASE_URL_PAGE_1 = "https://www.thenewslens.com/category/china/"
BASE_URL_PAGE_N = "https://www.thenewslens.com/category/china/page{}"

# State archive file for resumable scraping
STATE_FILE = "scraper_state_TNL.json"
# Fixed output filename
SINGLE_OUTPUT_FILE = "TNL_2023_2025.csv"

# Split 2023-2025 into 6 half-year (6 months) intervals.
# Since news is ordered from newest to oldest, to match the pagination logic, we scrape the most recent interval first.
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

# Fixed field content
MEDIA_NAME = "The News Lens"
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
    """Parse content of a single article"""
    soup = fetch_html(url)
    if not soup:
        return None
    
    # 1. Extract publish date (usually in meta tag: property="article:published_time")
    date_meta = soup.find('meta', property='article:published_time')
    news_date_str = ""
    dt_obj = None
    if date_meta and date_meta.get('content'):
        # Format is usually: 2026-03-15T10:00:00+08:00
        raw_date = date_meta['content']
        news_date_str = raw_date.split('T')[0] # Get YYYY-MM-DD
        try:
            dt_obj = datetime.strptime(news_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    # 2. Extract news title
    title_tag = soup.find('h1', class_='article-title')
    if not title_tag:
        title_tag = soup.find('title')
    news_title = title_tag.text.strip() if title_tag else "No Title"
    
    # Clean up potential website suffix in title
    news_title = news_title.replace("- TNL The News Lens 關鍵評論網", "")

    # 3. Extract news content
    # The News Lens content is generally in a specific container, like a div with class article-content
    content_div = soup.find('div', class_='article-content')
    if not content_div:
        # Alternative plan: try to find main tag or article tag
        content_div = soup.find('article')
        
    news_content = ""
    if content_div:
        # Extract all paragraph <p> tags
        paragraphs = content_div.find_all('p')
        # Filter out empty paragraphs, concatenate text
        news_content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    
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
        # Read existing data
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            
        # Sort by 'News Date' descending (newest to oldest)
        data.sort(key=lambda x: x['News Date'], reverse=True)
        
        # Overwrite with sorted data
        with open(filepath, mode='w', encoding='utf-8-sig', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(data)
        print("[+] Global data rearranged in reverse chronological order!")
    except Exception as e:
        print(f"[-] Error occurred while sorting CSV file: {e}")

def main():
    # --- 1. Initialize resumable scraping state ---
    current_chunk_idx = 0
    current_page = 6  # Default starts from page 6
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_chunk_idx = state.get("next_chunk_idx", 0)
                saved_page = state.get("last_page", 2)
                current_page = max(1, saved_page - 5) 
            print(f"[*] Archive state found! Will start from chunk {current_chunk_idx+1}, starting page adjusted to: Page {current_page}.")
        except Exception as e:
            print(f"[-] Failed to read archive: {e}, will start from the beginning.")

    if current_chunk_idx >= len(CHUNKS):
        print("\n[*] All 6 phases (36 months total) from 2023 to 2025 have been processed")
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
    empty_page_count = 0  # Track consecutive empty pages
    invalid_page_count = 0

    while not reached_older_month:
        if current_page == 1:
            list_url = BASE_URL_PAGE_1
        else:
            list_url = BASE_URL_PAGE_N.format(current_page)
            
        print(f"\n[+] Scanning page {current_page}: {list_url}")
        
        soup = fetch_html(list_url)
        if not soup:
            print("[-] Failed to fetch list page, exiting loop.")
            break
            
        article_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if '/article/' in href and href not in seen_urls:
                if not re.search(r'/article/\d+$', href):
                    continue
                article_links.append(href)
                seen_urls.add(href)
                
        if not article_links:
            print("[-] No new article links found on current page.")
            empty_page_count += 1
            if empty_page_count >= 5:
                print("[-] No data for 5 consecutive pages, might have reached the bottom of the website, forcing exit.")
                break
            current_page += 1
            continue
            
        empty_page_count = 0
        newer_count = 0
        target_count = 0
        older_count = 0
        valid_articles_checked = 0
            
        for link in article_links:
            time.sleep(random.uniform(1.0, 2.0))
            
            article_data = parse_article(link)
            if not article_data or not article_data['dt_obj']:
                continue
                
            dt = article_data['dt_obj']
            valid_articles_checked += 1
            
            if dt > target_end:
                # Later than target end time of current chunk (e.g. target is 2024H2, encountered 2025/2026 articles)
                newer_count += 1
                
            elif target_start <= dt <= target_end:
                # Hit time range of current chunk
                print(f"  [Collected] {dt.strftime('%Y-%m-%d')} | {article_data['title'][:30]}...")
                target_count += 1
                chunk_data.append({
                    'Media Name': MEDIA_NAME,
                    'News Title': article_data['title'],
                    'News Date': article_data['date_str'],
                    'News Content': article_data['content'],
                    'News Link': article_data['url'],  # Newly added link field
                    'Media Region': MEDIA_REGION,
                    'Funding Source': FUNDING_SOURCE
                })
                
            elif dt < target_start:
                # Earlier than start time of current chunk (e.g. encountered 2024H1 articles)
                print(f"  [Ignored] {dt.strftime('%Y-%m-%d')} (earlier than target range) | {article_data['title'][:20]}...")
                older_count += 1
                
        # Page-level comprehensive judgement
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
        # Removed chunk_data.reverse(), keeping the original newest-to-oldest reverse order from webpage
        
        print(f"\n[*] Scraping finished. Collected {len(chunk_data)} articles in this chunk.")
        print(f"[*] Appending to {SINGLE_OUTPUT_FILE} ...")
        
        # Check if file exists and is empty to decide whether to write headers
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
            
            # --- Rearrange the whole document in reverse chronological order after each append ---
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
        print(f"[+] Progress saved. Next run will process the next 6-month content.")
    except Exception as e:
        print(f"[-] Failed to save archive: {e}")

if __name__ == "__main__":
    main()