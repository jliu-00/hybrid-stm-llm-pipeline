import requests
import xml.etree.ElementTree as ET
import os
import json
import time
import random
import re
from datetime import datetime

# ================= Static Configuration Area =================
ROBOTS_TXT_URL = "https://www.bbc.com/robots.txt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_INDEX_FILE = os.path.join(SCRIPT_DIR, "BBC_chinese_index_2023_2024.json")

# Global crawling time range (2023-01-01 to 2024-11-24)
GLOBAL_START = datetime.strptime("2023-01-01", "%Y-%m-%d")
GLOBAL_END = datetime.strptime("2024-11-24", "%Y-%m-%d")

# Filter out obviously irrelevant language sitemaps to improve scan efficiency
NON_CHINESE_LANGS = [
    '/afrique/', '/arabic/', '/bengali/', '/burmese/', '/gahuza/', '/hausa/', 
    '/hindi/', '/indonesia/', '/mundo/', '/pashto/', '/persian/', '/portuguese/', 
    '/russian/', '/swahili/', '/tajik/', '/turkce/', '/ukrainian/', '/urdu/', 
    '/uzbek/', '/vietnamese/', '/sport/'
]
# =============================================================

def get_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': 'application/xml, text/xml, */*; q=0.01',
        'Connection': 'keep-alive'
    }

def fetch_text(url):
    """Request the target URL and return the text content."""
    try:
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[-] Request failed: {url} | Error: {e}")
        return ""

def discover_root_sitemaps():
    """Accurately parse robots.txt to extract all declared Sitemap nodes."""
    print("[*] Parsing robots.txt for root Sitemap indices...")
    raw_text = fetch_text(ROBOTS_TXT_URL)
    sitemaps = []
    if raw_text:
        sitemaps = re.findall(r'^Sitemap:\s*(https?://\S+)', raw_text, re.IGNORECASE | re.MULTILINE)
    
    # Exclude explicitly foreign language sitemaps to save network resources
    filtered_sitemaps = [sm for sm in sitemaps if not any(lang in sm for lang in NON_CHINESE_LANGS)]
    return filtered_sitemaps

def strip_xml_namespaces(xml_string):
    """Remove XML namespaces to eliminate path complexity during ElementTree parsing."""
    return re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)

def normalize_bbc_chinese_url(loc):
    """
    Format traditional/simplified links based on factual BBC routing rules:
    1. Replace traditional links containing /trad with /simp.
    2. For the new React architecture (containing /articles/), forcibly append /simp if no variant is specified.
    3. Keep legacy structures (containing /simp/[ID]) unchanged to avoid 404 errors.
    """
    if '/trad' in loc:
        return loc.replace('/trad', '/simp')
    
    if '/articles/' in loc and not loc.endswith(('/simp', '/trad')):
        return loc.rstrip('/') + '/simp'
        
    return loc

def process_sitemap(url, url_database, visited_sitemaps):
    """Recursively parse the Sitemap DOM tree."""
    if url in visited_sitemaps:
        return
    visited_sitemaps.add(url)
    
    xml_text = fetch_text(url)
    if not xml_text:
        return

    try:
        xml_text = strip_xml_namespaces(xml_text)
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"[-] XML parsing failed: {url} | Error: {e}")
        return

    # 1. Process Sitemap index nodes (nested Sitemaps)
    if root.tag == 'sitemapindex':
        for sitemap in root.findall('sitemap'):
            loc_elem = sitemap.find('loc')
            if loc_elem is not None and loc_elem.text:
                child_url = loc_elem.text
                # Skip irrelevant foreign language sub-indices
                if not any(lang in child_url for lang in NON_CHINESE_LANGS):
                    process_sitemap(child_url, url_database, visited_sitemaps)
                    time.sleep(0.5)

    # 2. Process standard URL lists
    elif root.tag == 'urlset':
        print(f"  [>] Extracting article nodes from: {url}")
        for url_node in root.findall('url'):
            loc_elem = url_node.find('loc')
            
            if loc_elem is not None and loc_elem.text:
                loc = loc_elem.text
                
                # Capture only BBC Chinese network data
                if '/zhongwen/' in loc:
                    lastmod_elem = url_node.find('lastmod')
                    if lastmod_elem is not None and lastmod_elem.text:
                        lastmod_str = lastmod_elem.text[:10] # Extract YYYY-MM-DD format
                        try:
                            lastmod_date = datetime.strptime(lastmod_str, "%Y-%m-%d")
                            
                            # Filter based on target timeframe (Engineering trade-off)
                            if GLOBAL_START <= lastmod_date <= GLOBAL_END:
                                # Normalize simplified/traditional routing
                                normalized_loc = normalize_bbc_chinese_url(loc)
                                
                                # Store in dictionary. Utilizes dict properties to auto-overwrite/deduplicate.
                                url_database[normalized_loc] = lastmod_str
                        except ValueError:
                            pass

def main():
    print("=== BBC Chinese Sitemap Full Extraction & Filter Tool ===")
    print(f"Target Timeframe: {GLOBAL_START.strftime('%Y-%m-%d')} to {GLOBAL_END.strftime('%Y-%m-%d')}")
    
    url_database = {}
    visited_sitemaps = set()
    
    root_sitemaps = discover_root_sitemaps()
    if not root_sitemaps:
        print("[-] Failed to extract the Sitemap list from robots.txt.")
        return
        
    print(f"[*] Found {len(root_sitemaps)} associated root Sitemaps. Initiating recursive DOM tree parsing...")
    
    for sm in root_sitemaps:
        process_sitemap(sm, url_database, visited_sitemaps)
            
    print(f"\n[+] Sitemap tree traversal complete. Captured {len(url_database)} unique Chinese article links.")
    
    # Structure and output to JSON, sorted chronologically descending
    sorted_urls = sorted(url_database.items(), key=lambda x: x[1], reverse=True)
    output_data = [{"url": loc, "date": date} for loc, date in sorted_urls]
    
    try:
        with open(LOCAL_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"[+] Index data conclusively persisted to: {LOCAL_INDEX_FILE}")
    except Exception as e:
        print(f"[-] File write failed: {e}")

if __name__ == "__main__":
    main()