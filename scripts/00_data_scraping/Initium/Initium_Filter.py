import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'TheInitium_2023_2025.csv')
output_path = os.path.join(script_dir, 'TheInitium_2023_2025_filtered.csv')
log_path = os.path.join(script_dir, 'initium_filter_stats.txt')

try:
    df = pd.read_csv(file_path)
    
    # Calculate statistics before filtering
    entries_before = len(df)
    chars_before = df['News Content'].astype(str).str.len().sum()

    # 1. Zeilen entfernen, bei denen der Inhalt mit "端傳媒新聞播客" (Podcast-Transkripte) beginnt
    df_filtered = df[~df['News Content'].astype(str).str.startswith('端傳媒新聞播客')].copy()

    # 2. Zeilen entfernen, bei denen der Titel mit "圆桌" (Runder Tisch / Foren) beginnt
    df_filtered = df_filtered[~df_filtered['News Title'].astype(str).str.startswith('圆桌')]

    # Calculate statistics after filtering
    entries_after = len(df_filtered)
    chars_after = df_filtered['News Content'].astype(str).str.len().sum()

    # Save filtered data with UTF-8 BOM for Excel compatibility
    df_filtered.to_csv(output_path, index=False, encoding='utf-8-sig')

    # Write statistics to log file
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("Filter Statistics\n")
        f.write("=================\n\n")
        f.write(f"Entries before: {entries_before}\n")
        f.write(f"Entries after:  {entries_after}\n")
        f.write(f"Entries removed: {entries_before - entries_after}\n\n")
        
        f.write(f"Total characters in 'News Content' before: {chars_before}\n")
        f.write(f"Total characters in 'News Content' after:  {chars_after}\n")
        f.write(f"Total characters removed: {chars_before - chars_after}\n")

    print(f"Filtering complete. Data saved to {output_path}")
    print(f"Statistics saved to {log_path}")
    
except Exception as e:
    print(f"Error processing file: {e}")
