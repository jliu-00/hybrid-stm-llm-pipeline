import pandas as pd
import os
import opencc

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Mangmang_2023_2025_All.csv')
output_path = os.path.join(script_dir, 'Mangmang_2023_2025_filtered.csv')
log_path = os.path.join(script_dir, 'mangmang_filter_stats.txt')

try:
    df = pd.read_csv(file_path)
    
    # Calculate statistics before filtering
    entries_before = len(df)
    chars_before = df['News Content'].astype(str).str.len().sum()

    df_filtered = df.copy()

    # 0. Remove specific rows by title and date
    titles_to_remove = [
        "告读者 | 关于这段时间的我们",
        "欢迎订阅《莽莽》Newsletter",
        "Uyghurs Left in Lurch After Zero- COVID"
    ]
    df_filtered = df_filtered[~df_filtered['News Title'].astype(str).str.strip().isin(titles_to_remove)]
    
    mask = (df_filtered['News Title'].astype(str).str.strip() == "莽莽 MANG MANG") & \
           (df_filtered['News Date'].astype(str).str.contains("2023/10/15", na=False))
    df_filtered = df_filtered[~mask]

    # 1. Remove independent lines starting with specific strings
    # (?m) enables multiline mode. ^ matches start of line. \n? optionally removes trailing newline.
    line_pattern = r'(?m)^[ \t]*(?:提示[：:]\s*本文(?:字|本)数|作者 / |照片 / |漫画 / |采写 /|原创插画 / |注[：:]).*$\n?'
    df_filtered['News Content'] = df_filtered['News Content'].str.replace(line_pattern, '', regex=True)

    # 1.5 Collapse multiple empty lines into a single empty line
    # Matches 3 or more consecutive newlines (with optional spaces) and replaces them with 2 newlines (one empty line)
    df_filtered['News Content'] = df_filtered['News Content'].str.replace(r'\n\s*\n(\s*\n)+', '\n\n', regex=True)

    # 2. Convert Traditional to Simplified Chinese using opencc
    converter = opencc.OpenCC('tw2sp')
    
    def convert_text(text):
        if pd.isna(text):
            return text
        return converter.convert(str(text))

    # Apply conversion to all string columns
    for col in df_filtered.columns:
        if df_filtered[col].dtype == object:
            df_filtered[col] = df_filtered[col].apply(convert_text)

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
