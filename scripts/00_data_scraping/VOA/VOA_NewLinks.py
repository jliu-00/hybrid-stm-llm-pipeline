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
BASE_DOMAIN = "https://www.voachinese.com"
BASE_URL_CATEGORY = "https://www.voachinese.com/z/1757?p={0}"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "voa_boundary_state.json")
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "VOA_NewLinks.csv")

GLOBAL_START = datetime(2023, 1, 1)
GLOBAL_END = datetime(2025, 12, 31, 23, 59, 59)

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
    ]
    return {'User-Agent': random.choice(user_agents)}

def fetch_html_and_text(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser'), response.text
    except requests.RequestException:
        return None, ""

def load_existing_urls(filepath):
    existing_urls = set()
    if os.path.exists(filepath):
        try:
            with open(filepath, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'News Link' in row:
                        existing_urls.add(row['News Link'])
        except Exception:
            pass
    return existing_urls

def parse_article(url):
    config = Config()
    config.request_timeout = 15
    config.fetch_images = False

    soup, raw_html = fetch_html_and_text(url)
    if not raw_html:
        return None

    try:
        article = Article(url, config=config)
        article.set_html(raw_html)
        article.parse()
    except Exception:
        return None

    dt_obj = article.publish_date
    if not dt_obj and soup:
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

    news_date_str = dt_obj.strftime("%Y-%m-%d") if dt_obj else ""
    news_title = article.title.replace(" - 美国之音", "").strip() if article.title else "No Title"
    news_content = article.text.strip()
    
    return {
        'url': url, 'title': news_title, 'date_str': news_date_str, 
        'dt_obj': dt_obj, 'content': news_content
    }

def backup_existing_csv(filepath):
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(filepath)
        backup_filepath = f"{base}_backup_{timestamp}{ext}"
        try:
            shutil.copy2(filepath, backup_filepath)
        except Exception:
            pass

def save_state(current_page, oldest_date_str):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({"current_page": current_page, "oldest_date": oldest_date_str}, f)
    except Exception:
        pass

def flush_to_csv(data_list):
    if not data_list:
        return
    file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
    write_header = not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0
    try:
        with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            if write_header:
                writer.writeheader()
            writer.writerows(data_list)
    except IOError:
        pass

def main():
    print("=== VOA Phase 1: NewLinks Scraper ===")
    backup_existing_csv(SINGLE_OUTPUT_FILE)
    global_seen_urls = load_existing_urls(SINGLE_OUTPUT_FILE)

    current_page = 1
    oldest_date_obj = None

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_page = state.get("current_page", 1)
                oldest_date_str = state.get("oldest_date")
                if oldest_date_str:
                    oldest_date_obj = datetime.strptime(oldest_date_str, "%Y-%m-%d")
            print(f"[*] Resuming from Page: {current_page}. Current oldest date: {oldest_date_str}")
        except Exception:
            pass

    while current_page <= 100:
        list_url = BASE_URL_CATEGORY.format(current_page)
        print(f"\n[+] Scanning Category Page {current_page}/100: {list_url}")
        
        soup, raw_text = fetch_html_and_text(list_url)
        if not raw_text:
            print("  [-] Reached physical category archive boundary (404/Empty).")
            break
            
        page_target_urls = []
        if soup:
            main_area = soup.find('div', id='content') or soup.find('div', id='main-content') or soup.find('ul', id='ordinaryItems') or soup
            for a_tag in main_area.find_all('a', href=True):
                href = a_tag['href']
                if '/a/' in href and '/video/' not in href:
                    full_url = urljoin(BASE_DOMAIN, href)
                    if full_url.startswith("https://www.voachinese.com/a/") and full_url not in page_target_urls:
                        page_target_urls.append(full_url)
        
        if not page_target_urls:
            print("  [-] No valid links found on page.")
            break

        page_data = []
        for link in page_target_urls:
            if link in global_seen_urls:
                continue
                
            time.sleep(random.uniform(1.5, 3.0))
            article_data = parse_article(link)
            
            if not article_data or not article_data['dt_obj']:
                continue
                
            dt = article_data['dt_obj']
            
            if dt <= GLOBAL_END:
                print(f"  [Collected] {dt.strftime('%Y-%m-%d')} | {article_data['title'][:30]}...")
                global_seen_urls.add(link)
                page_data.append({
                    'Media Name': MEDIA_NAME, 'News Title': article_data['title'],
                    'News Date': article_data['date_str'], 'News Content': article_data['content'],
                    'News Link': article_data['url'], 'Media Region': MEDIA_REGION,
                    'Funding Source': FUNDING_SOURCE
                })
                
                # Update oldest date tracker
                if oldest_date_obj is None or dt < oldest_date_obj:
                    oldest_date_obj = dt
        
        flush_to_csv(page_data)
        current_page += 1
        
        oldest_date_str = oldest_date_obj.strftime("%Y-%m-%d") if oldest_date_obj else ""
        save_state(current_page, oldest_date_str)

    print("\n[*] Phase 1 Complete. Maximum accessible category pages scanned.")
    if oldest_date_obj:
        print(f"[*] The oldest date successfully scraped is: {oldest_date_obj.strftime('%Y-%m-%d')}")
        print("[*] Please proceed to run VOA_Sitemap.py to prepare the OldLinks index.")

if __name__ == "__main__":
    main()
