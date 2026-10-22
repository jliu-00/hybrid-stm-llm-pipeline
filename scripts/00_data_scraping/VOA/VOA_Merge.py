import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_LINKS_FILE = os.path.join(SCRIPT_DIR, "VOA_NewLinks.csv")
OLD_LINKS_FILE = os.path.join(SCRIPT_DIR, "VOA_OldLinks.csv")
FINAL_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "VOA_2023_2025.csv")

CSV_HEADERS = [
    'Media Name', 'News Title', 'News Date', 'News Content', 
    'News Link', 'Media Region', 'Funding Source'
]

def load_csv_data(filepath):
    data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except Exception as e:
            print(f"[-] Error reading {filepath}: {e}")
    return data

def main():
    print("=== VOA Phase 4: Data Merging ===")
    
    new_data = load_csv_data(NEW_LINKS_FILE)
    old_data = load_csv_data(OLD_LINKS_FILE)
    
    print(f"[*] Loaded {len(new_data)} records from NewLinks.")
    print(f"[*] Loaded {len(old_data)} records from OldLinks.")
    
    all_data = new_data + old_data
    
    # Deduplication by 'News Link'
    unique_data = {}
    for row in all_data:
        link = row.get('News Link')
        if link and link not in unique_data:
            unique_data[link] = row
            
    final_list = list(unique_data.values())
    
    # Sort reverse chronologically
    final_list.sort(key=lambda x: x.get('News Date', ''), reverse=True)
    
    print(f"[*] Deduped to {len(final_list)} unique records.")
    
    try:
        with open(FINAL_OUTPUT_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
            if final_list:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(final_list)
        print(f"[+] Final dataset successfully merged and sorted: {FINAL_OUTPUT_FILE}")
    except Exception as e:
        print(f"[-] Error writing final file: {e}")

if __name__ == "__main__":
    main()
