import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from datetime import datetime
import os
import shutil
from urllib.parse import urljoin
from newspaper import Article, Config

# ================= Configuration Area =================
BASE_DOMAIN = "https://read.mangmang.run"
ARCHIVE_URL = "https://read.mangmang.run/archive"

# Ensure files are saved in the exact same directory as the script regardless of terminal location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Fixed output filename
SINGLE_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "Mangmang_2023_2025.csv")


TARGET_START_STR = "2023-01-01"
TARGET_END_STR = "2025-12-31"
TARGET_START = datetime.strptime(TARGET_START_STR, "%Y-%m-%d")
TARGET_END = datetime.strptime(TARGET_END_STR, "%Y-%m-%d")

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
MEDIA_NAME = "Mangmang"
MEDIA_REGION = "Europe"
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
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': BASE_DOMAIN
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

def parse_fallback_date(soup):
    """Date extraction for various meta/time tags and JSON-LD"""
    import json
    # 1. Check JSON-LD
    for script in soup.find_all('script', type='application/ld+json'):
        if script.string:
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and 'datePublished' in item:
                        return datetime.strptime(item['datePublished'][:10], "%Y-%m-%d")
            except:
                pass
    
    # 2. Check time tags
    for time_tag in soup.find_all('time'):
        if time_tag.get('datetime'):
            try:
                return datetime.strptime(time_tag['datetime'][:10], "%Y-%m-%d")
            except:
                pass
                
    # 3. Check Meta tags
    meta_tags = [
        soup.find('meta', property='article:published_time'),
        soup.find('meta', property='og:article:published_time'),
        soup.find('meta', attrs={'name': 'date'})
    ]
    for meta in meta_tags:
        if meta and meta.get('content'):
            try:
                return datetime.strptime(meta['content'][:10], "%Y-%m-%d")
            except:
                pass
    return None

def parse_article(url):
    """Parse content and metadata of a single article using Newspaper3k with DOM fallback."""
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
        # Fallback: Manually parse HTML for OpenGraph article metadata, JSON-LD, and Time tags
        soup = BeautifulSoup(article.html, 'html.parser')
        dt_obj = parse_fallback_date(soup)

    if not dt_obj:
        print(f"  [-] Failed to extract date for {url}, skipping.")
        return None

    # Strip timezone info to allow comparison with naive datetimes
    dt_obj = dt_obj.replace(tzinfo=None)
    news_date_str = dt_obj.strftime("%Y-%m-%d")

    # 2. Extract news title and clean up site suffix
    news_title = article.title if article.title else "No Title"
    news_title = news_title.replace(" - Mangmang", "").replace(" | 莽莽", "").strip()

    # 3. Extract news content
    news_content = article.text.strip()
    
    
    if "This site requires JavaScript" in news_content or len(news_content) < 50:
        soup = BeautifulSoup(article.html, 'html.parser')
        
        # Remove noscript tags to avoid interference
        for noscript in soup.find_all('noscript'):
            noscript.decompose()
            
        # Locate common article content containers (e.g., .gh-content for Ghost)
        content_container = soup.select_one('.gh-content, .post-content, .entry-content, .article-content, article')
        
        if content_container:
            # Extract contents of paragraphs, headers, and lists
            elements = content_container.find_all(['p', 'h2', 'h3', 'h4', 'li', 'blockquote'])
            news_content = '\n\n'.join([el.get_text(strip=True) for el in elements if el.get_text(strip=True)])
        else:
            # Fallback: Remove irrelevant scripts, styles, and navigation, then extract text from the entire page
            for hidden in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                hidden.decompose()
            if soup.body:
                news_content = soup.body.get_text(separator='\n', strip=True)

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

def main():
    # --- 0. Backup existing data ---
    backup_existing_csv(SINGLE_OUTPUT_FILE)

    print(f"\n[*] === Started scraping Mangmang Archive ===")
    print(f"[*] Target time range: {TARGET_START_STR} to {TARGET_END_STR}")
    
    article_links = []
    seen_urls = set()
    
    # --- 1. Fetch Links (Handling Infinite Scroll) ---
    print("\n[+] Attempting to fetch all links via Sitemap (handles infinite scroll)...")
    sitemap_url = urljoin(BASE_DOMAIN, "/sitemap.xml")
    sitemap_soup, _ = fetch_html_and_text(sitemap_url)
    
    if sitemap_soup:
        for loc in sitemap_soup.find_all('loc'):
            url = loc.text.strip()
            skip_keywords = ['/archive', '/about', '/contact', '/podcast', '/tag/']
            if BASE_DOMAIN in url and not any(kw in url for kw in skip_keywords):
                path = url.replace(BASE_DOMAIN, "")
                if len(path) > 3 and url not in seen_urls:
                    article_links.append(url)
                    seen_urls.add(url)
        print(f"[+] Found {len(article_links)} potential links from Sitemap.")
        
    # Fallback 1: Substack/Ghost style JSON API pagination
    if len(article_links) < 20:
        print("[*] Sitemap returned few links. Attempting API pagination...")
        offset = 0
        while True:
            api_url = f"{BASE_DOMAIN}/api/v1/archive?sort=new&search=&offset={offset}&limit=50"
            try:
                import json
                resp = requests.get(api_url, headers=get_headers(), timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if not data: 
                        break
                    new_links = 0
                    for post in data:
                        url = post.get('canonical_url') or post.get('url')
                        if url and url not in seen_urls:
                            article_links.append(url)
                            seen_urls.add(url)
                            new_links += 1
                    print(f"  [>] Fetched API offset {offset}, found {new_links} new links")
                    if new_links == 0:
                        break
                    offset += 50
                    time.sleep(1)
                else:
                    break
            except:
                break
                
    # Fallback 2: Basic HTML parsing (only gets first page)
    if len(article_links) < 20:
        print(f"[*] API failed. Fetching archive list directly from HTML: {ARCHIVE_URL}")
        soup, raw_text = fetch_html_and_text(ARCHIVE_URL)
        if soup:
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                skip_keywords = ['/archive', '/about', '/contact', '/podcast', '/tag/', 'mailto:', 'javascript:']
                if any(kw in href for kw in skip_keywords):
                    continue
                full_url = urljoin(BASE_DOMAIN, href).split('?')[0].split('#')[0]
                if BASE_DOMAIN in full_url and full_url not in seen_urls:
                    path = full_url.replace(BASE_DOMAIN, "")
                    if len(path) > 3:
                        article_links.append(full_url)
                        seen_urls.add(full_url)

    if not article_links:
        print("[-] No valid article links found via any method.")
        return
        
    print(f"\n[+] Total {len(article_links)} unique article links compiled. Starting verification...\n")
    
    # --- 2. Iterate, Parse and Filter by Date ---
    chunk_data = []
        
    for idx, link in enumerate(article_links):
        # Adding a small randomized delay to respect the server
        time.sleep(random.uniform(1.0, 2.0)) 
        
        article_data = parse_article(link)
        if not article_data or not article_data['dt_obj']:
            continue
            
        dt = article_data['dt_obj']
        
        if TARGET_START <= dt <= TARGET_END:
            print(f"  [Collected] {dt.strftime('%Y-%m-%d')} | {article_data['title'][:30]}...")
            chunk_data.append({
                'Media Name': MEDIA_NAME,
                'News Title': article_data['title'],
                'News Date': article_data['date_str'],
                'News Content': article_data['content'],
                'News Link': article_data['url'],
                'Media Region': MEDIA_REGION,
                'Funding Source': FUNDING_SOURCE
            })
        else:
            print(f"  [Ignored] {dt.strftime('%Y-%m-%d')} (outside target) | {article_data['title'][:20]}...")

    # --- 3. Data saving ---
    if chunk_data:
        print(f"\n[*] Scraping finished. Collected {len(chunk_data)} articles within the time range.")
        print(f"[*] Saving to {SINGLE_OUTPUT_FILE} ...")
        
        file_exists = os.path.exists(SINGLE_OUTPUT_FILE)
        write_header = not file_exists or os.path.getsize(SINGLE_OUTPUT_FILE) == 0
        
        try:
            with open(SINGLE_OUTPUT_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                if write_header:
                    writer.writeheader()
                writer.writerows(chunk_data)
            print("[+] CSV document saved/appended")
            
            # Sort the final CSV in reverse chronological order
            sort_csv_reverse_chronologically(SINGLE_OUTPUT_FILE)
            
        except IOError as e:
            print(f"[-] Error occurred while saving CSV: {e}")
    else:
        print(f"\n[*] Scraping finished. No articles found between {TARGET_START_STR} and {TARGET_END_STR}.")

if __name__ == "__main__":
    main()