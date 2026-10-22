import pandas as pd
import os
import opencc

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'TheNewsLens_2023_2025.csv')
output_path = os.path.join(script_dir, 'TheNewsLens_2023_2025_filtered.csv')
log_path = os.path.join(script_dir, 'tnl_filter_stats.txt')

converter = opencc.OpenCC('tw2sp')

try:
    df = pd.read_csv(file_path)
    
    entries_before = len(df)
    chars_before = df['News Content'].astype(str).str.len().sum()

    # 1. Drop rows where 'News Content' starts with specific prefixes
    prefixes_to_drop = (
        "BBC News",
        "中央通訊社是中華民國的國家通訊社",
        "德國之聲（Deutsche Welle）是德國的國際廣播電視臺"
    )
    
    mask = df['News Content'].astype(str).str.lstrip().str.startswith(prefixes_to_drop)
    df_filtered = df[~mask].copy()

    # 2. Clean specific substrings and lines within 'News Content'
    strings_to_remove = [
        "【加入關鍵評論網會員】每天精彩好文直送你的信箱，每週獨享編輯精選、時事精選、藝文週報等特製電子報。還可留言與作者、記者、編輯討論文章內容。立刻點擊免費加入會員！",
        "【加入關鍵評論網成員】每天精彩好文直送你的信箱，每週獨享編輯精選、時事精選、藝文週報等特製電子報。還可留言與作者、記者、編輯討論文章內容。立刻點擊免費加入成員！",
        "投稿請寄到 oped@thenewslens.com 來信請附上投稿人真實名字、email和電話，並直接附上投稿內容（Word、純文字皆可）。我們會在收到稿件後24小時內回信，建議勿一稿多投。另外為了國際版翻譯需求，也請附上想要刊登的英文作者名稱。",
        "《關鍵評論網》編輯部助理編輯",
        "《關鍵評論網》助理編輯",
        "TNL精選書籍，讓你站上文字巨人的肩膀，遠眺世界。",
        "TNL編輯部專用帳號，發表每天整理的新聞、重點新聞分析整理。",
        "TNL 編輯精選好文轉載，感謝作者的熱情分享！"
    ]
    
    def clean_content(text):
        if pd.isna(text):
            return text
            
        for s in strings_to_remove:
            text = text.replace(s, '')
            
        lines = text.split('\n')
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("核稿編輯："):
                continue
            if stripped.startswith("責任編輯："):
                continue
            if stripped.startswith("關鍵評論網編輯："):
                continue
            if stripped.startswith("關鍵評論網記者"):
                continue
            if stripped.startswith("Photo Credit:"):
                continue
                
            new_lines.append(line)
            
        return '\n'.join(new_lines).lstrip('\n')

    df_filtered['News Content'] = df_filtered['News Content'].apply(clean_content)

    # 3. Convert Traditional Chinese to Simplified Chinese for string columns
    for col in ['News Title', 'News Content']:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col].apply(lambda x: converter.convert(str(x)) if pd.notna(x) else x)

    # Calculate statistics after filtering
    entries_after = len(df_filtered)
    chars_after = df_filtered['News Content'].astype(str).str.len().sum()

    df_filtered.to_csv(output_path, index=False, encoding='utf-8-sig')

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("Filter Statistics\n")
        f.write("=================\n\n")
        f.write(f"Entries before: {entries_before}\n")
        f.write(f"Entries after:  {entries_after}\n")
        f.write(f"Entries removed: {entries_before - entries_after}\n\n")
        
        f.write(f"Total characters in 'News Content' before: {chars_before}\n")
        f.write(f"Total characters in 'News Content' after:  {chars_after}\n")
        f.write(f"Total characters removed: {chars_before - chars_after}\n")

    print(f"Filtering and Conversion complete. Data saved to {output_path}")
    print(f"Statistics saved to {log_path}")

except Exception as e:
    print(f"Error processing file: {e}")
