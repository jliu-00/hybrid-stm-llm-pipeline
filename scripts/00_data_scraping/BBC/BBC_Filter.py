import pandas as pd
import os
import opencc

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'BBC_2023_2025.csv')
output_path = os.path.join(script_dir, 'BBC_2023_2025_filtered.csv')
log_path = os.path.join(script_dir, 'bbc_filter_stats.txt')

try:
    df = pd.read_csv(file_path)
    
    # Calculate statistics before filtering
    entries_before = len(df)
    chars_before = df['News Content'].astype(str).str.len().sum()

    df_filtered = df.copy()

    # 1. Remove entries where 'News Content' has fewer than 250 Chinese characters
    # r'[\u4e00-\u9fff]' matches any CJK unified ideograph (Chinese character)
    char_counts = df_filtered['News Content'].astype(str).str.count(r'[\u4e00-\u9fff]')
    df_filtered = df_filtered[char_counts >= 250].copy()

    # 2. Remove specific strings from 'News Content'
    strings_to_remove = [
        "你的器材不支持播放多媒体材料 Play video",
        "（编者按：本文包含对死亡的血腥描述，部分读者可能会感到不安。）",
        "你的器材不支持播放多媒体材料 视频加注文字，"
    ]
    for s in strings_to_remove:
        df_filtered['News Content'] = df_filtered['News Content'].str.replace(s, '', regex=False)

    # 3. Entfernt Datums- und Aktualisierungszeilen (z. B. "2025年12月30日 最近更新： 2026年1月1日")
    date_line_pattern = r'(?m)^[ \t]*\d{4}年\d{1,2}月\d{1,2}日(?:\s*最近更新[：:]\s*\d{4}年\d{1,2}月\d{1,2}日)?.*$\n?'
    df_filtered['News Content'] = df_filtered['News Content'].str.replace(date_line_pattern, '', regex=True)

    # 3.5 Collapse multiple empty lines into a single empty line
    df_filtered['News Content'] = df_filtered['News Content'].str.replace(r'\n\s*\n(\s*\n)+', '\n\n', regex=True)

    # 4. Convert Traditional to Simplified Chinese using opencc
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
