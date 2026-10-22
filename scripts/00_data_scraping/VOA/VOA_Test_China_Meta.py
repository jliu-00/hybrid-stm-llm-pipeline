import requests
from bs4 import BeautifulSoup
import random

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

def fetch_category_links(category_url, limit=10):
    print(f"[*] Fetching test links exactly from {category_url}")
    try:
        response = requests.get(category_url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        main_area = soup.find('div', id='content') or soup.find('div', id='main-content') or soup.find('ul', id='ordinaryItems') or soup
        for a in main_area.find_all('a', href=True):
            href = a['href']
            if '/a/' in href and '/video/' not in href:
                full_url = href if href.startswith('http') else 'https://www.voachinese.com' + href
                if full_url not in links:
                    links.append(full_url)
                if len(links) >= limit:
                    break
        return links
    except Exception as e:
        print(f"[-] Error fetching category links: {e}")
        return []

def test_meta_keywords(urls):
    print("\n=== Testing VOA Meta Keywords Logic (China Category ONLY) ===\n")
    valid_count = 0
    invalid_count = 0
    
    for url in urls:
        print(f"[*] Fetching: {url}")
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_tag = soup.find('title')
            title = title_tag.text.strip() if title_tag else "No Title"
            print(f"    Title: {title}")
            
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                content = meta_keywords['content']
                print(f"    [Meta Keywords Found]: {content}")
                if "中国" in content:
                    print("    Valid: Contains keyword 'China'")
                    valid_count += 1
                else:
                    print("    Invalid: Does NOT contain keyword 'China'")
                    invalid_count += 1
            else:
                print("     No <meta name='keywords'> tag found.")
                invalid_count += 1
                
        except Exception as e:
            print(f"    [-] Error fetching URL: {e}")
            invalid_count += 1
        print("-" * 40)
        
    print(f"\n=== Summary ===")
    print(f"Total Tested: {len(urls)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")

if __name__ == "__main__":
    china_links = fetch_category_links("https://www.voachinese.com/z/1757", limit=15)
    test_meta_keywords(china_links)
