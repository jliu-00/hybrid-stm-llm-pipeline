import pandas as pd
import os
import opencc

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'TWReporter_China_2023_2025.csv')
output_path = os.path.join(script_dir, 'TWReporter_China_2023_2025_filtered.csv')
log_path = os.path.join(script_dir, 'TWreporter_filter_stats.txt')

try:
    df = pd.read_csv(file_path)
    
    # Calculate statistics before filtering
    entries_before = len(df)
    chars_before = df['News Content'].astype(str).str.len().sum()

    # 1. Remove rows where 'News Title' starts with "【Podcast】"
    df_filtered = df[~df['News Title'].astype(str).str.startswith('【Podcast】')].copy()

    # 2. Remove lines starting with "Fill"
    # (?m) enables multiline mode. ^ matches start of line. \n? optionally removes the trailing newline.
    fill_pattern = r'(?m)^Fill.*$\n?'
    df_filtered['News Content'] = df_filtered['News Content'].str.replace(fill_pattern, '', regex=True)

    # 3. Remove photo/image credits in parentheses
    # Matches fullwidth or halfwidth parentheses containing specific keywords
    photo_credit_pattern = r'[（\(][^）\)]*(?:攝影|图片提供|圖片提供|摄影)[^）\)]*[）\)]'
    df_filtered['News Content'] = df_filtered['News Content'].str.replace(photo_credit_pattern, '', regex=True)

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
