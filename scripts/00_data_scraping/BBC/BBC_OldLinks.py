import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
from datetime import datetime
import os
import json
from newspaper import Article, Config

# ================= Configuration Area =================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Input: Local index file
LOCAL_INDEX_FILE = os.path.join(SCRIPT_DIR, "BBC_chinese_index_2023_2024.json")

# Output: Final CSV data and resumable scraping state file
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "BBC_OldLinks.csv")
STATE_FILE = os.path.join(SCRIPT_DIR, "content_scraper_state.json")

# Time range chunks for scraping
CHUNKS = [
    {"start": "2024-11-01", "end": "2024-11-24", "label": "2024_11_Test"},
    {"start": "2024-07-01", "end": "2024-10-31", "label": "2024_H2_Remainder"},
    {"start": "2024-01-01", "end": "2024-06-30", "label": "2024_H1"},
    {"start": "2023-07-01", "end": "2023-12-31", "label": "2023_H2"},
    {"start": "2023-01-01", "end": "2023-06-30", "label": "2023_H1"},
]

CSV_HEADERS = [
    'Media Name', 'News Title', 'News Date', 'News Content', 
    'News Link', 'Media Region', 'Funding Source'
]

MEDIA_NAME = "BBC"
MEDIA_REGION = "UK"
FUNDING_SOURCE = "Foreign Government" 

# Global unique topic ID for the China topic
CHINA_TOPIC_ID = "ckr7mn6r003t"
# ============================================

def get_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive'
    }

def fetch_html_and_text(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser'), response.text
    except requests.RequestException:
        # Exceptions are handled by checking the return value in the parsing phase
        return None, ""

def validate_url_pre_flight(url):
    """
    Preliminary screening based on URL structural features before initiating a network request.
    Returns: (should_download, auto_pass_topic_check)
    """
    if '/articles/' in url:
        # Optimo architecture requires downloading to check internal JSON-LD
        return True, False
    else:
        # Legacy architecture allows topic determination via URL strings
        if 'chinese-news-' in url:
            # Explicitly classified as a China topic
            return True, True
        else:
            # Block URLs belonging to other categories
            return False, False

def check_topic_in_html(soup):
    """Check if the structured data in the HTML source code contains the target topic."""
    if not soup:
        return False, None
        
    # Parse Next.js core page properties to match internal topic IDs
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    if next_data_script and next_data_script.string:
        try:
            next_data = json.loads(next_data_script.string)
            page_props = next_data.get('props', {}).get('pageProps', {})
            
            def find_topic(data):
                if isinstance(data, dict):
                    if data.get('topicId') == CHINA_TOPIC_ID:
                        return True, "Next.js Topic ID"
                    if CHINA_TOPIC_ID in str(data.get('sameAs', '')):
                        return True, "Next.js Schema ID"
                        
                    for key, value in data.items():
                        if key.lower() in ['navigation', 'footer', 'header', 'nav', 'footers']:
                            continue
                        found, method = find_topic(value)
                        if found: return found, method
                        
                elif isinstance(data, list):
                    for item in data:
                        found, method = find_topic(item)
                        if found: return found, method
                        
                return False, None
                
            found, method = find_topic(page_props)
            if found:
                return True, method
        except Exception:
            pass
                
    return False, None

def parse_article(url, auto_pass_topic, fallback_date_str):
    """Extract article content."""
    config = Config()
    config.request_timeout = 15
    config.fetch_images = False

    soup, raw_html = fetch_html_and_text(url)
    if not raw_html: 
        return None

    # Topic validation
    match_method = "URL Pattern (chinese-news)"
    is_target_topic = auto_pass_topic
    
    if not auto_pass_topic:
        is_target_topic, match_method = check_topic_in_html(soup)
        
    if not is_target_topic:
        return {'is_target_topic': False}

    # Content extraction
    try:
        article = Article(url, config=config)
        article.set_html(raw_html)
        article.parse()
    except Exception:
        return None

    # Extract publish date
    dt_obj = article.publish_date
    if not dt_obj and soup:
        meta_date = soup.find('meta', property='article:published_time') or soup.find('meta', attrs={'name': 'article:published_time'})
        if meta_date and meta_date.get('content'):
            try: dt_obj = datetime.strptime(meta_date['content'][:10], "%Y-%m-%d")
            except ValueError: pass

    news_date_str = dt_obj.strftime("%Y-%m-%d") if dt_obj else fallback_date_str
    news_title = article.title.replace(" - BBC News 中文", "").strip() if article.title else "No Title"
    news_content = article.text.strip()
    
    # Text cleaning
    if news_title != "No Title" and news_content.startswith(news_title):
        news_content = news_content[len(news_title):].strip()
    elif article.title and news_content.startswith(article.title.strip()):
        news_content = news_content[len(article.title.strip()):].strip()
        
    news_content = re.sub(r'(?m)^\s*\d{4}年\s*\d{1,2}月\s*\d{1,2}日\s*$', '', news_content)
    news_content = re.sub(r'(?m)^\s*阅读时间[:：]?\s*\d+\s*分钟\s*$', '', news_content)
    news_content = re.sub(r'(?m)^\s*图像来源[，,:：].*$', '', news_content)
    news_content = re.sub(r'(?m)^\s*图像加注文字[，,:：].*$', '', news_content)
    news_content = re.sub(r'(?m)^\s*Author,.*$', '', news_content)
    
    news_content = re.sub(r'\n{3,}', '\n\n', news_content).strip()
    
    return {
        'url': url,
        'title': news_title,
        'date_str': news_date_str,
        'content': news_content,
        'is_target_topic': True,
        'match_method': match_method
    }

def save_state(processed_urls, current_chunk_idx):
    """Save processed links and chunk index for resumable scraping."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({
                "processed_urls": list(processed_urls),
                "chunk_idx": current_chunk_idx
            }, f)
    except Exception:
        pass

def main():
    print("=== Phase 2: BBC Content Scraper Initiated ===")
    
    # 1. Load resumable state
    processed_links = set()
    current_chunk_idx = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)
                if isinstance(state_data, list):
                    processed_links = set(state_data)
                elif isinstance(state_data, dict):
                    processed_links = set(state_data.get("processed_urls", []))
                    current_chunk_idx = state_data.get("chunk_idx", 0)
            print(f"[*] Resuming from saved state. Chunk index: {current_chunk_idx}, Links processed: {len(processed_links)}.")
        except Exception:
            pass

    if current_chunk_idx >= len(CHUNKS):
        print("\n[*] All chunks have been processed")
        return

    current_chunk = CHUNKS[current_chunk_idx]
    target_start = datetime.strptime(current_chunk['start'], "%Y-%m-%d")
    target_end = datetime.strptime(current_chunk['end'], "%Y-%m-%d")

    print(f"\n[*] === Scraping chunk {current_chunk_idx + 1}/{len(CHUNKS)} : {current_chunk['label']} ===")
    print(f"[*] Target time range: {current_chunk['start']} to {current_chunk['end']}")

    # 2. Check and load local index
    if not os.path.exists(LOCAL_INDEX_FILE):
        print(f"[-] Local index not found at {LOCAL_INDEX_FILE}. Please run Phase 1 script first.")
        return
        
    with open(LOCAL_INDEX_FILE, 'r', encoding='utf-8') as f:
        all_indexed_articles = json.load(f)
        
    # 3. Filter tasks for current run based on the time range
    target_entries = []
    for item in all_indexed_articles:
        try:
            item_dt = datetime.strptime(item['date'], "%Y-%m-%d")
            if target_start <= item_dt <= target_end:
                target_entries.append(item)
        except ValueError:
            pass
            
    print(f"[*] Found {len(target_entries)} entries in the local index for {current_chunk['start']} to {current_chunk['end']}.")
    
    if not target_entries:
        print("[-] No entries match the target time range. Updating state to next chunk.")
        save_state(processed_links, current_chunk_idx + 1)
        return

    # 4. Start scraping and validation
    saved_count = 0
    current_run_processed = 0
    
    file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
    with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0:
            writer.writeheader()
            
        for entry in target_entries:
            url = entry['url']
            fallback_date = entry['date']
            
            if url in processed_links:
                continue
                
            current_run_processed += 1
            
            # Step A: Apply pre-flight URL rule validation
            should_download, auto_pass_topic = validate_url_pre_flight(url)
            is_new_format = '/articles/' in url
            
            if not should_download:
                processed_links.add(url)
                save_state(processed_links, current_chunk_idx)
                print(f"  [Excluded - URL Pattern] Not a China news link: {url}")
                continue
            
            # Step B: Initiate request and parse content
            time.sleep(random.uniform(1.0, 2.5))
            article_data = parse_article(url, auto_pass_topic, fallback_date)
            
            processed_links.add(url)
            save_state(processed_links, current_chunk_idx)
            
            if not article_data:
                print(f"  [Excluded - Page Invalid] Cannot access or parse page: {url}")
                continue
                
            if not article_data.get('is_target_topic', False):
                print(f"  [Excluded - Tag Mismatch] No relevant China topic structured metadata detected: {url}")
                continue
            
            # Step C: Save data
            match_str = f"{article_data['match_method']}"
            print(f"  [Saved] {article_data['date_str']} | [Rule: {match_str}] | {article_data['title'][:25]}...")
                
            writer.writerow({
                'Media Name': MEDIA_NAME,
                'News Title': article_data['title'],
                'News Date': article_data['date_str'],
                'News Content': article_data['content'],
                'News Link': article_data['url'],
                'Media Region': MEDIA_REGION,
                'Funding Source': FUNDING_SOURCE
            })
            saved_count += 1

    print(f"\n[*] Chunk {current_chunk['label']} Complete. Processed {current_run_processed} links this session, Saved {saved_count} valid articles.")
    
    # Update state to the next chunk
    save_state(processed_links, current_chunk_idx + 1)
    print(f"[+] Progress archived! Next run will execute the next time interval.")

if __name__ == "__main__":
    main()