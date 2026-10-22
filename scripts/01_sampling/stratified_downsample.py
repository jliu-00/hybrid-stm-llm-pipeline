import os
import argparse
import pandas as pd
import numpy as np

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Geschichtetes Downsampling aus lokal vorliegenden, vorbereinigten Mediendateien."
    )
    parser.add_argument("--input-dir", required=True,
                        help="Ordner mit den sieben vorbereinigten CSV-Dateien.")
    parser.add_argument("--output-dir", required=True,
                        help="Lokaler Ausgabeordner fuer die Stichprobe; Volltexte bleiben ausserhalb des veroeffentlichten Pakets.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Zufallsstartwert, z. B. 42, 2024 oder 12345 (Standard: 42).")
    args = parser.parse_args(argv)
    base_dir = os.path.abspath(os.path.expanduser(args.input_dir))
    output_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    sampling_seed = args.seed
    
    indep_files = [
        "Mangmang_2023_2025_filtered.csv",
        "TWReporter_China_2023_2025_filtered.csv",
        "TheInitium_2023_2025_filtered.csv",
        "TheNewsLens_2023_2025_filtered.csv"
    ]
    
    gov_files = {
        "dw": "DW_2023_2025_filtered.csv",
        "bbc": "BBC_2023_2025_filtered.csv",
        "voa": "VOA_2023_2025.csv"
    }

    # Load independent media and calculate target size
    indep_dfs = []
    indep_total_count = 0
    print("Loading independent media files...")
    for f in indep_files:
        path = os.path.join(base_dir, f)
        df = pd.read_csv(path)
        indep_dfs.append(df)
        indep_total_count += len(df)
        print(f" - {f}: {len(df)} rows")
    
    print(f"\nTotal independent media rows (target size for downsampling): {indep_total_count}")

    # Load government media and calculate proportions
    print("\nLoading government-funded media files...")
    gov_dfs = {}
    gov_total_count = 0
    for key, f in gov_files.items():
        path = os.path.join(base_dir, f)
        df = pd.read_csv(path)
        gov_dfs[key] = df
        gov_total_count += len(df)
        print(f" - {f}: {len(df)} rows")
        
    print(f"\nTotal government-funded media rows before downsampling: {gov_total_count}")

    # Stratified downsampling
    print("\nPerforming stratified downsampling...")
    downsampled_dfs = []
    current_downsampled_total = 0
    
    # Sort keys to ensure deterministic order of operations
    for key in sorted(gov_files.keys()):
        df = gov_dfs[key]
        proportion = len(df) / gov_total_count
        # Calculate target rows for this dataset
        # Use round to handle floats, ensure we don't exceed target due to rounding
        target_rows = int(round(proportion * indep_total_count))
        
        # Sample the dataframe
        sampled_df = df.sample(n=target_rows, random_state=sampling_seed)
        downsampled_dfs.append(sampled_df)
        current_downsampled_total += len(sampled_df)
        
        print(f" - {key.upper()}: downsampled from {len(df)} to {target_rows} rows ({proportion:.2%} of total gov media)")

    # Adjust rounding differences to match exactly indep_total_count
    diff = indep_total_count - current_downsampled_total
    if diff != 0:
        print(f"\nAdjusting for rounding difference: {diff} rows")
        # Add or remove from the largest dataset to balance
        largest_idx = np.argmax([len(df) for df in downsampled_dfs])
        key = sorted(gov_files.keys())[largest_idx]
        
        if diff > 0:
            # Need more rows, sample from remaining unselected rows
            selected_indices = downsampled_dfs[largest_idx].index
            remaining_df = gov_dfs[key].drop(selected_indices)
            extra_sample = remaining_df.sample(n=diff, random_state=sampling_seed)
            downsampled_dfs[largest_idx] = pd.concat([downsampled_dfs[largest_idx], extra_sample])
        else:
            # Need fewer rows, drop some randomly
            downsampled_dfs[largest_idx] = downsampled_dfs[largest_idx].sample(n=len(downsampled_dfs[largest_idx]) + diff, random_state=sampling_seed)
            
        current_downsampled_total += diff
        print(f" - Adjusted {key.upper()} to {len(downsampled_dfs[largest_idx])} rows.")
        
    print(f"Final downsampled government media count: {current_downsampled_total}")

    # Combine all datasets
    print("\nCombining datasets...")
    final_df = pd.concat(indep_dfs + downsampled_dfs, ignore_index=True)
    
    # Shuffle the final dataset to mix the rows
    final_df = final_df.sample(frac=1, random_state=sampling_seed).reset_index(drop=True)
    
    # Save to output
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"downsampled_dataset_seed_{sampling_seed}.csv")
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\nSuccessfully saved combined dataset with {len(final_df)} rows to:")
    print(output_path)
    print("\nDistribution in final dataset:")
    print(final_df['Funding Source'].value_counts())

if __name__ == '__main__':
    main()
