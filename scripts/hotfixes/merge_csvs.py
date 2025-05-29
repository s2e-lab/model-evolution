import pandas as pd
import os
import glob
import argparse

def merge_csv_files(input_dir, output_file, pattern="*.csv"):
    """Merge all CSV files in the input_dir matching pattern into one output_file."""
    csv_files = glob.glob(os.path.join(input_dir, pattern))

    if not csv_files:
        print(f"No CSV files found in directory: {input_dir}")
        return

    print(f"Found {len(csv_files)} CSV files. Merging...")

    # Read and concatenate all CSVs
    dataframes = []
    for file in csv_files:
        print(f"Reading {file}")
        df = pd.read_csv(file)
        dataframes.append(df)

    merged_df = pd.concat(dataframes, ignore_index=True)
    merged_df.to_csv(output_file, index=False)
    print(f"Merge complete. Output written to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge multiple CSV files with headers.")
    parser.add_argument("input_dir", help="Directory containing CSV files to merge")
    parser.add_argument("output_file", help="Path to the merged output CSV file")
    parser.add_argument("--pattern", default="*.csv", help="Filename pattern to match CSV files (default: *.csv)")

    args = parser.parse_args()
    merge_csv_files(args.input_dir, args.output_file, args.pattern)
