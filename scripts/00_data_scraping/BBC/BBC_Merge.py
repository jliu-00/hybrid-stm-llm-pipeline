import pandas as pd
import os

def merge_and_deduplicate_links(new_file_path, old_file_path, output_file_path):
    """
    Append old links data below new links data and remove duplicates based on the 'News Link' column.
    
    :param new_file_path: Path to the CSV file containing new links
    :param old_file_path: Path to the CSV file containing old links
    :param output_file_path: Path to the output CSV file after merging and deduplicating
    """
    # Check if files exist
    if not os.path.exists(new_file_path):
        print(f"Error: File not found - {new_file_path}")
        return
    if not os.path.exists(old_file_path):
        print(f"Error: File not found - {old_file_path}")
        return

    try:
        # Read CSV files
        # Depending on the system environment, specifying encoding='utf-8' might be necessary if read errors occur
        df_new = pd.read_csv(new_file_path)
        df_old = pd.read_csv(old_file_path)

        # Check if the required 'News Link' column exists
        if 'News Link' not in df_new.columns or 'News Link' not in df_old.columns:
            print("Error: Both CSV files must contain the 'News Link' column.")
            return

        # Record the amount of data before merging
        print(f"Number of new links: {len(df_new)}")
        print(f"Number of old links: {len(df_old)}")

        # Append old data below new data
        df_combined = pd.concat([df_new, df_old], ignore_index=True)

        # Remove duplicates based on the 'News Link' column
        # keep='first' keeps the first occurrence (since df_new is on top, it prioritizes records from df_new)
        df_cleaned = df_combined.drop_duplicates(subset=['News Link'], keep='first')

        # Calculate how many duplicate records were removed
        duplicates_removed = len(df_combined) - len(df_cleaned)
        print(f"Found and removed {duplicates_removed} duplicate records after merging.")
        print(f"Final number of valid links: {len(df_cleaned)}")

        # Save the result as a new CSV file
        # Using utf-8-sig encoding ensures correct display when opened in applications like Excel
        df_cleaned.to_csv(output_file_path, index=False, encoding='utf-8-sig')
        print(f"Processing complete. Data saved to: {output_file_path}")

    except Exception as e:
        print(f"An error occurred while processing data: {e}")

if __name__ == "__main__":
    # Define input and output file names
    NEW_LINKS_FILE = 'BBC_NewLinks.csv'
    OLD_LINKS_FILE = 'BBC_OldLinks.csv'
    OUTPUT_FILE = 'BBC_2023_2025.csv'

    # Execute the merge and deduplicate function
    merge_and_deduplicate_links(NEW_LINKS_FILE, OLD_LINKS_FILE, OUTPUT_FILE)