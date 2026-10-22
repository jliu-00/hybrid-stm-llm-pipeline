import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from datetime import datetime
import os
import json
import concurrent.futures
from newspaper import Article, Config

# ================= Configuration Area =================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_INDEX_FILE = os.path.join(SCRIPT_DIR, "VOA_index_old.json")
STATE_FILE = os.path.join(SCRIPT_DIR, "voa_oldlinks_state.json")
BOUNDARY_STATE_FILE = os.path.join(SCRIPT_DIR, "voa_boundary_state.json")
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "VOA_OldLinks.csv")

GLOBAL_START = datetime(2023, 1, 1)
MAX_WORKERS = 15 # Number of concurrent threads, recommended 10-20. Too high may risk IP blocking.

CSV_HEADERS = [
    'Media Name', 'News Title', 'News Date', 'News Content', 
    'News Link', 'Media Region', 'Funding Source'
]

MEDIA_NAME = "VOA"
MEDIA_REGION = "USA"
FUNDING_SOURCE = "Foreign Government" 
# ============================================

def get_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ]
    return {'User-Agent': random.choice(user_agents)}

def validate_and_parse(url, cutoff_date):
    """
    1. Fetches HTML.
    2. Checks for `<meta name="keywords" content="中国">`.
    3. If valid, parses the article with Newspaper3k.
    4. Validates publish date is within bounds.
    """
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        raw_html = response.text
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException:
        return None, "Request Failed"

    # Strenge Validierung: Muss das Meta-Schlagwort '中国' (China) im Meta-Keywords-Tag enthalten
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    is_china_topic = False
    if meta_keywords and meta_keywords.get('content'):
        if "中国" in meta_keywords['content']:
            is_china_topic = True
            
    if not is_china_topic:
        return None, "Not China Topic"

    # Parsing
    config = Config()
    config.request_timeout = 15
    config.fetch_images = False
    
    try:
        article = Article(url, config=config)
        article.set_html(raw_html)
        article.parse()
    except Exception:
        return None, "Parse Failed"

    # Date Extraction
    dt_obj = article.publish_date
    if not dt_obj:
        meta_date = soup.find('meta', attrs={'name': 'pubdate'}) or \
                    soup.find('meta', property='article:published_time') or \
                    soup.find('meta', attrs={'name': 'article:published_time'})
        if meta_date and meta_date.get('content'):
            try:
                date_str = meta_date['content'][:10]
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass

    if dt_obj and dt_obj.tzinfo is not None:
        dt_obj = dt_obj.replace(tzinfo=None)

    if not dt_obj:
        return None, "Missing Date"
        
    # Date Bounds Validation
    if not (GLOBAL_START <= dt_obj <= cutoff_date):
        return None, "Out of Target Date Range"

    news_date_str = dt_obj.strftime("%Y-%m-%d")
    news_title = article.title.replace(" - 美国之音", "").strip() if article.title else "No Title"
    news_content = article.text.strip()
    
    return {
        'url': url, 'title': news_title, 'date_str': news_date_str, 'content': news_content
    }, "Success"

def process_url_worker(url, cutoff_date):
    """Worker function for threading"""
    # Add a micro-delay to prevent sudden bursts of concurrent requests from being blocked by the server
    time.sleep(random.uniform(0.1, 0.5))
    article_data, status = validate_and_parse(url, cutoff_date)
    return url, article_data, status

def save_state(processed_urls):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({"processed_urls": list(processed_urls)}, f)
    except Exception:
        pass

def main():
    print("=== VOA Phase 3: OldLinks Content Scraper (Multi-threaded) ===")
    
    # Load cutoff date
    cutoff_date = datetime.now()
    if os.path.exists(BOUNDARY_STATE_FILE):
        try:
            with open(BOUNDARY_STATE_FILE, 'r') as f:
                state = json.load(f)
                oldest_date_str = state.get("oldest_date")
                if oldest_date_str:
                    cutoff_date = datetime.strptime(oldest_date_str, "%Y-%m-%d")
        except Exception:
            pass
    print(f"[*] Target Timeline: {GLOBAL_START.strftime('%Y-%m-%d')} to {cutoff_date.strftime('%Y-%m-%d')} (Cutoff)")

    # Load local index
    if not os.path.exists(LOCAL_INDEX_FILE):
        print(f"[-] Index not found at {LOCAL_INDEX_FILE}. Please run VOA_Sitemap.py first.")
        return
        
    with open(LOCAL_INDEX_FILE, 'r', encoding='utf-8') as f:
        all_indexed_articles = json.load(f)
        
    # Load resume state
    processed_links = set()
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)
                processed_links = set(state_data.get("processed_urls", []))
            print(f"[*] Resuming from state. Processed so far: {len(processed_links)}")
        except Exception:
            pass

    # Filter links that need to be processed
    urls_to_process = [entry['url'] for entry in all_indexed_articles if entry['url'] not in processed_links]
    print(f"[*] Remaining links to process: {len(urls_to_process)}")
    print(f"[*] Initializing ThreadPool with {MAX_WORKERS} workers...")

    file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
    
    with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0:
            writer.writeheader()

        saved_count = 0
        processed_in_this_run = 0
        
        # Start multi-threading
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(process_url_worker, url, cutoff_date): url for url in urls_to_process}
            
            try:
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result_url, article_data, status = future.result()
                        processed_links.add(url)
                        processed_in_this_run += 1
                        
                        if article_data:
                            print(f"  [Saved] {article_data['date_str']} | {article_data['title'][:30]}...")
                            writer.writerow({
                                'Media Name': MEDIA_NAME, 'News Title': article_data['title'],
                                'News Date': article_data['date_str'], 'News Content': article_data['content'],
                                'News Link': article_data['url'], 'Media Region': MEDIA_REGION,
                                'Funding Source': FUNDING_SOURCE
                            })
                            saved_count += 1
                            
                        else:
                            if status == "Not China Topic":
                                print(f"  [Ignored] Tag Mismatch (Not China Topic): {url}")
                            else:
                                print(f"  [Ignored] {status}: {url}")
                        
                        # Periodic disk flush (save state every 50 processed URLs to handle high threaded speed)
                        if processed_in_this_run % 50 == 0:
                            f.flush()
                            save_state(processed_links)
                            
                    except Exception as exc:
                        print(f"[-] {url} generated an exception: {exc}")
                        # Do not add to processed_links on fatal error so it can be retried on next run
                        
            except KeyboardInterrupt:
                print("\n[!] Interrupted by user. Cancelling pending tasks and saving state... Please wait.")
                for future in future_to_url:
                    future.cancel()
                save_state(processed_links)
                return

    # Final complete state flush
    save_state(processed_links)
    print(f"\n[*] OldLinks Scrape Complete. Saved {saved_count} valid China articles in this session.")
    print("[*] Please run VOA_Merge.py to finalize the dataset.")

if __name__ == "__main__":
    main()
