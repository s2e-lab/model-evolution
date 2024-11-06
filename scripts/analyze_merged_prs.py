"""
This script analyzes the PRs opened by Hugging Face's conversion tool and that were merged.
For each of these PRs, it identifies the associated repo and extracts the commit history.
The commit history is saved to a CSV file (any caught exceptions are added to a separate CSV file).
@Author: Joanna C. S. Santos
"""
import json
import os
import zipfile
from collections import OrderedDict
# %%
from pathlib import Path

import pandas as pd
from huggingface_hub import model_info
from tqdm import tqdm

DATA_DIR = Path('../data')
RESULTS_DIR = Path('../results')


def find_merged_repos() -> set:
    """
    Find the repositories that had PRs merged.
    :return: a set of the repositories that had PRs merged (their URLs).
    """
    # Extracted results, load to frame and delete the large CSV
    with zipfile.ZipFile(DATA_DIR / 'sfconvertbot_pr_metadata.csv.zip', 'r') as zip_ref:
        zip_ref.extractall(DATA_DIR)
    df = pd.read_csv(DATA_DIR / 'sfconvertbot_pr_metadata.csv')
    os.remove(DATA_DIR / 'sfconvertbot_pr_metadata.csv')
    # Python lacks ordered sets, so we need to use an ordered dictionary
    merged_repos = OrderedDict()
    # iterate over frame
    for index, row in tqdm(df.iterrows(), total=len(df), unit="PR"):
        header = row['header_metadata']
        if not header or not header.startswith("{"):
            continue
        header = json.loads(row['header_metadata'])
        status = header['discussion']['status']
        if status == 'merged':
            merged_repos[row['model_id']] = ""
    return merged_repos.keys()




if __name__ == '__main__':

    columns = ["model_id", "created_at", "last_modified", "all_files_in_tree"]
    merged_repos = find_merged_repos()
    file_prefix = 'merged_prs_repo_files'
    # iterates over the repositories
    commits, errors = [], []
    save_at = 100  # indicate how many iterations to save the dataframes

    for index, repo_url in tqdm(enumerate(merged_repos), unit="repo", total=len(merged_repos)):
        try:
            info = model_info(repo_url, files_metadata=True)
            files = [x.rfilename for x in info.siblings]
            commits.append((repo_url, info.created_at, info.last_modified, ";".join(files)))

            if index > 0 and index % save_at == 0:
                output_file = f"{file_prefix}_{index}.csv"
                df_commits = pd.DataFrame(commits, columns=columns)
                df_commits.to_csv(DATA_DIR / output_file, index=False)
                # delete prior checkpoint
                if os.path.exists(DATA_DIR / f"{file_prefix}_{index - save_at}.csv"):
                    os.remove(DATA_DIR / f"{file_prefix}_{index - save_at}.csv")
                print(f"Commits saved to {output_file}")
        except Exception as e:
            print(f"Error processing {repo_url}: {e}")
            errors.append((repo_url, e))

    # save the commits to CSV
    df_commits = pd.DataFrame(commits, columns=columns)
    output_file = f"{file_prefix}.csv"
    df_commits.to_csv(DATA_DIR / output_file, index=False)

    # save errors to CSV
    error_file = output_file.replace("repo_files", "repo_files_errors")
    df_errors = pd.DataFrame(errors, columns=["repo_url", "error"])
    df_errors.to_csv(DATA_DIR / error_file, index=False)

    # delete prior checkpoints
    for i in range(0, len(merged_repos), save_at):
        if os.path.exists(DATA_DIR / f"{file_prefix}_{i}.csv"):
            os.remove(DATA_DIR / f"{file_prefix}_{i}.csv")

    print(f"Commits saved to {output_file}")
