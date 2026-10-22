import requests
import xml.etree.ElementTree as ET
import os
import json
import time
import random
import re
import gzip
from io import BytesIO
from datetime import datetime, timedelta

# ================= Configuration Area =================
SITEMAP_INDEX_URL = "https://www.voachinese.com/sitemap.xml"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_INDEX_FILE = os.path.join(SCRIPT_DIR, "VOA_index_old.json")
STATE_FILE = os.path.join(SCRIPT_DIR, "voa_boundary_state.json")

GLOBAL_START = datetime.strptime("2023-01-01", "%Y-%m-%d")
# ======================================================

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

def fetch_sitemap_content(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        
        if url.endswith('.gz'):
            # Decompress gzip content
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                return f.read().decode('utf-8')
        else:
            return response.text
    except Exception as e:
        print(f"[-] Request failed: {url} | Error: {e}")
        return ""

def strip_xml_namespaces(xml_string):
    return re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)

def main():
    print("=== VOA Sitemap Indexer ===")
    
    # 1. Load the Cutoff Date from Phase 1
    cutoff_date = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                oldest_date_str = state.get("oldest_date")
                if oldest_date_str:
                    cutoff_date = datetime.strptime(oldest_date_str, "%Y-%m-%d")
        except Exception:
            pass
            
    if not cutoff_date:
        print("[-] Could not find 'oldest_date' in voa_boundary_state.json.")
        print("[-] Please run VOA_NewLinks.py first, or we will default to extracting up to today.")
        cutoff_date = datetime.now()
        
    # We add a 30-day buffer to the cutoff date to account for 'lastmod' being later than publish_date
    safe_end_date = cutoff_date + timedelta(days=30)
    print(f"[*] Target Range: {GLOBAL_START.strftime('%Y-%m-%d')} to {safe_end_date.strftime('%Y-%m-%d')} (Cutoff + Buffer)")

    # 2. Fetch Root Sitemap Index
    print(f"[*] Fetching root sitemap: {SITEMAP_INDEX_URL}")
    root_xml = fetch_sitemap_content(SITEMAP_INDEX_URL)
    if not root_xml:
        return
        
    root_xml = strip_xml_namespaces(root_xml)
    try:
        root = ET.fromstring(root_xml)
    except ET.ParseError:
        print("[-] Failed to parse root sitemap XML.")
        return

    sitemaps_to_process = []
    if root.tag == 'sitemapindex':
        for sitemap in root.findall('sitemap'):
            loc_elem = sitemap.find('loc')
            if loc_elem is not None and loc_elem.text:
                url = loc_elem.text
                if 'sitemap_412_' in url: # VOA specific pattern for content sitemaps
                    # Optimization: Some sitemap index items have lastmod
                    lastmod_elem = sitemap.find('lastmod')
                    if lastmod_elem is not None and lastmod_elem.text:
                        lm_dt = datetime.strptime(lastmod_elem.text[:10], "%Y-%m-%d")
                        # Skip sitemaps entirely outside our range if possible
                        if lm_dt < GLOBAL_START:
                            continue
                    sitemaps_to_process.append(url)
    
    print(f"[*] Found {len(sitemaps_to_process)} sub-sitemaps to traverse.")
    
    # 3. Traverse and Extract
    url_database = {}
    
    for sm_url in sitemaps_to_process:
        print(f"  [>] Processing: {sm_url}")
        xml_text = fetch_sitemap_content(sm_url)
        if not xml_text:
            continue
            
        try:
            xml_text = strip_xml_namespaces(xml_text)
            sm_root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue
            
        if sm_root.tag == 'urlset':
            for url_node in sm_root.findall('url'):
                loc_elem = url_node.find('loc')
                if loc_elem is not None and loc_elem.text:
                    loc = loc_elem.text
                    if '/a/' in loc:
                        lastmod_elem = url_node.find('lastmod')
                        if lastmod_elem is not None and lastmod_elem.text:
                            lastmod_str = lastmod_elem.text[:10]
                            try:
                                lastmod_date = datetime.strptime(lastmod_str, "%Y-%m-%d")
                                if GLOBAL_START <= lastmod_date <= safe_end_date:
                                    url_database[loc] = lastmod_str
                            except ValueError:
                                pass
                                
        time.sleep(1.0) # Polite delay
        
    print(f"\n[+] Sitemap tree traversal complete. Captured {len(url_database)} potential article links.")
    
    # 4. Save to JSON
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
