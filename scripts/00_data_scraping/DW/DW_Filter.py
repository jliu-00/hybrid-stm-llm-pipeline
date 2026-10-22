import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'DW_2023_2025_All.csv')
output_path = os.path.join(script_dir, 'DW_2023_2025_filtered.csv')
log_path = os.path.join(script_dir, 'dw_filter_stats.txt')

df = pd.read_csv(file_path)

# Calculate statistics before filtering
entries_before = len(df)
chars_before = df['News Content'].astype(str).str.len().sum()

# 1. Zeilen entfernen, deren Titel mit "德语媒体：" (Presseschau deutschsprachiger Medien) beginnt
df_filtered = df[~df['News Title'].astype(str).str.startswith('德语媒体：')].copy()

# 2. Define strings to remove from 'News Content'
strings_to_remove = [
    "（德国之声中文网）",
    "© 2025年德国之声版权声明：本文所有内容受到著作权法保护，如无德国之声特别授权，不得擅自使用。任何不当行为都将导致追偿，并受到刑事追究。",
    "DW中文有Instagram！欢迎搜寻dw.chinese，看更多深入浅出的图文与影音报道。",
    "To view this video please enable JavaScript, and consider upgrading to a web browser that supports HTML5 video\n",
    "To view this video please enable JavaScript, and consider upgrading to a web browser that supports HTML5 video"
]

# Clean 'News Content' column
for s in strings_to_remove:
    df_filtered['News Content'] = df_filtered['News Content'].astype(str).str.replace(s, '', regex=False)

# Calculate statistics after filtering
entries_after = len(df_filtered)
chars_after = df_filtered['News Content'].astype(str).str.len().sum()

# Save filtered data
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
