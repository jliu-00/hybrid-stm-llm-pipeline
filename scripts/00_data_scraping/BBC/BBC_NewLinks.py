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
BASE_DOMAIN = "https://www.bbc.com"
# BBC topics page pagination structure
BASE_URL_PAGE_N = "https://www.bbc.com/zhongwen/topics/ckr7mn6r003t/simp?page={}"

# Ensure files are saved in the exact same directory as the script regardless of terminal location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# State archive file for resumable scraping
STATE_FILE = os.path.join(SCRIPT_DIR, "scraper_state_BBC.json")
# Fixed output filename
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "BBC_NewLinks.csv")

# Split 2024-2025 into intervals.
# First chunk is isolated to December 2025 for testing purposes.
# The remainder covers the rest of the 2024-2025 timeline in reverse chronological order.
CHUNKS = [
    {"start": "2025-12-01", "end": "2025-12-31", "label": "2025_12_Test"},
    {"start": "2025-07-01", "end": "2025-11-30", "label": "2025_H2_Remainder"},
    {"start": "2025-01-01", "end": "2025-06-30", "label": "2025_H1"},
    {"start": "2024-07-01", "end": "2024-12-31", "label": "2024_H2"}
]

# CSV column headers
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
MEDIA_NAME = "BBC"
MEDIA_REGION = "UK"
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
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.bbc.com/zhongwen/simp'
    }

def fetch_html_and_text(url):
    """Request webpage and return both BeautifulSoup object and raw text payload."""
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser'), response.text
    except requests.RequestException as e:
        print(f"[-] Failed to request page: {url} | Error: {e}")
        return None, ""

def parse_article(url):
    """Parse content of a single BBC article."""
    config = Config()
    config.request_timeout = 15
    # Disable Newspaper's default image fetching to speed up process and reduce request footprint
    config.fetch_images = False

    # 1. Fetch the raw HTML 
    soup, raw_html = fetch_html_and_text(url)
    if not raw_html:
        return None

    # 2. Feed the fetched HTML directly to Newspaper3k
    try:
        article = Article(url, config=config)
        article.set_html(raw_html)
        article.parse()
    except Exception as e:
        print(f"  [-] Newspaper3k encountered an error parsing {url}: {e}")
        return None

    # 3. Extract publish date
    dt_obj = article.publish_date
    
    # Fallback: check specific meta and time tags if Newspaper3k fails to identify the date
    if not dt_obj and soup:
        # Method A: OpenGraph / Article Meta
        meta_date = soup.find('meta', property='article:published_time') or soup.find('meta', attrs={'name': 'article:published_time'})
        if meta_date and meta_date.get('content'):
            try:
                date_str = meta_date['content'][:10]
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Method B: HTML5 Time Tag
        if not dt_obj:
            time_tag = soup.find('time')
            if time_tag and time_tag.get('datetime'):
                try:
                    date_str = time_tag['datetime'][:10]
                    dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    pass

    news_date_str = dt_obj.strftime("%Y-%m-%d") if dt_obj else ""

    # 4. Extract news title
    news_title = article.title if article.title else "No Title"
    news_title = news_title.replace(" - BBC News 中文", "").strip()

    # 5. Extract news content
    news_content = article.text.strip()
    
    # 6. Clean up the extracted content
    # Remove the title from the beginning of the content if Newspaper3k incorrectly included it
    if news_title != "No Title" and news_content.startswith(news_title):
        news_content = news_content[len(news_title):].strip()
    elif article.title and news_content.startswith(article.title.strip()):
        news_content = news_content[len(article.title.strip()):].strip()
        
    # Remove metadata lines anywhere in the content using regex multiline mode
    # Remove lines that only contain a Chinese date
    news_content = re.sub(r'(?m)^\s*\d{4}年\s*\d{1,2}月\s*\d{1,2}日\s*$', '', news_content)
    # Remove reading time indicators
    news_content = re.sub(r'(?m)^\s*阅读时间[:：]?\s*\d+\s*分钟\s*$', '', news_content)
    # Remove BBC image captions and image source text
    news_content = re.sub(r'(?m)^\s*图像来源[，,:：].*$', '', news_content)
    news_content = re.sub(r'(?m)^\s*图像加注文字[，,:：].*$', '', news_content)
    # Remove author and role information lines
    news_content = re.sub(r'(?m)^\s*Author,.*$', '', news_content)
    
    # Clean up excessive empty lines left behind by the regex removals
    news_content = re.sub(r'\n{3,}', '\n\n', news_content).strip()
    
    return {
        'url': url,
        'title': news_title,
        'date_str': news_date_str,
        'dt_obj': dt_obj,
        'content': news_content
    }

def sort_csv_reverse_chronologically(filepath):
    """Read existing CSV file, sort by news date in reverse chronological order, and rewrite."""
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
    """Backup the existing CSV file before running."""
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
    # Default to page 8
    current_page = 8  
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_chunk_idx = state.get("next_chunk_idx", 0)
                saved_page = state.get("last_page", 9)
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
        list_url = BASE_URL_PAGE_N.format(current_page)
            
        print(f"\n[+] Scanning page {current_page}: {list_url}")
        
        soup, raw_text = fetch_html_and_text(list_url)
        if not raw_text:
            print("[-] Failed to fetch list page, exiting loop.")
            break
            
        article_links = []
        
        # Method 1: Extract links directly from raw text payload
        payload_pattern = r'/zhongwen/articles/[a-zA-Z0-9]+'
        payload_links = re.findall(payload_pattern, raw_text)
        
        for link_path in payload_links:
            full_url = f"{BASE_DOMAIN}{link_path}/simp"
            if full_url not in seen_urls and full_url.startswith("https://www.bbc.com/zhongwen/articles/"):
                article_links.append(full_url)
                seen_urls.add(full_url)
        
        # Method 2: Standard DOM parser mapping for traditional HTML links
        if soup:
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                if '/zhongwen/articles/' in href:
                    match = re.search(r'(/zhongwen/articles/[a-zA-Z0-9]+)', href)
                    if match:
                        full_url = f"{BASE_DOMAIN}{match.group(1)}/simp"
                        if full_url not in seen_urls and full_url.startswith("https://www.bbc.com/zhongwen/articles/"):
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
            time.sleep(random.uniform(1.5, 3.0)) 
            
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