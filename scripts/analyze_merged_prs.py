"""
This script analyzes the PRs opened by Hugging Face's conversion tool and that were merged.
For each of these PRs, it identifies the associated repo and extracts the commit history.
The commit history is saved to a CSV file (any caught exceptions are added to a separate CSV file).
@Author: Joanna C. S. Santos
"""
import json
#%%
from pathlib import Path

import pandas as pd
import os
import zipfile

from tqdm import tqdm

from scripts import utils
from scripts.get_commit_logs import get_commits
from scripts.utils import clone

DATA_DIR = Path('../data')
RESULTS_DIR = Path('../results')

def find_merged_repos() ->set:
    """
    Find the repositories that had PRs merged.
    :return: a set of the repositories that had PRs merged (their URLs).
    """
    # Extracted results, load to frame and delete the large CSV
    with zipfile.ZipFile(DATA_DIR / 'sfconvertbot_pr_metadata.csv.zip', 'r') as zip_ref:
        zip_ref.extractall(DATA_DIR)
    df = pd.read_csv(DATA_DIR / 'sfconvertbot_pr_metadata.csv')
    os.remove(DATA_DIR / 'sfconvertbot_pr_metadata.csv')
    merged_repos = set()
    # iterate over frame
    for index, row in tqdm(df.iterrows(), total=len(df), unit="PR"):
        header = row['header_metadata']
        if not header or not header.startswith("{"):
            continue
        header = json.loads(row['header_metadata'])
        status = header['discussion']['status']
        if status == 'merged':
            merged_repos.add(row['model_id'])
    return merged_repos

def load_prior_commits():
    """
    Load the prior commits from the CSV files.
    :return: a dataframe with the prior commits.
    """
    # load the prior commits
    df_commits = pd.read_csv(DATA_DIR / 'huggingface_sort_by_createdAt_top996939_commits_0_1035.csv')
    cache = dict()
    for index, row in tqdm(df_commits.iterrows(), total=len(df_commits), unit="cache commit"):
        repo_url = row['repo_url']
        if repo_url not in cache:
            cache[repo_url] = []
        cache[repo_url].append(tuple([row[c] for c in columns]))
    return cache


if __name__ == '__main__':
    columns = ["repo_url", "commit_hash", "author", "date", "message", "changed_files", "all_files_in_tree"]
    merged_repos = find_merged_repos()
    cache = load_prior_commits()
    # iterates over the repositories
    commits, errors = [], []
    save_at = 100  # indicate how many iterations to save the dataframes
    for repo_url in tqdm(list(merged_repos)[:2], unit="repo"):
        clone_path = os.path.join("./tmp", repo_url.replace("/", "+"))
        try:
            if repo_url in cache:
                repo_commits = cache[repo_url]
                commits.extend(repo_commits)
                continue

            # if not in cache, clone the repository to get the commits
            clone(repo_url, clone_path)
            repo_commits = get_commits(clone_path)
            commits.extend([(repo_url,) + c for c in repo_commits])
            if len(commits) % save_at == 0:
                output_file = f"merged_prs_commits_{len(commits)}.csv"
                df_commits = pd.DataFrame(commits, columns=columns)
                df_commits.to_csv(output_file, index=False)
                # delete prior checkpoint
                if len(commits) > save_at:
                    os.remove(f"merged_prs_commits_{len(commits) - save_at}.csv")
                print(f"Commits saved to {output_file}")
        except Exception as e:
            print(f"Error processing {repo_url}: {e}")
            errors.append((repo_url, e))
        finally:
            if clone_path and os.path.exists(clone_path):
                utils.delete_folder(clone_path)

    # save the commits to CSV
    df_commits = pd.DataFrame(commits, columns=columns)
    output_file = f"merged_prs_commits.csv"
    df_commits.to_csv(DATA_DIR / output_file, index=False)

    # save errors to CSV
    error_file = output_file.replace("commits", "commits_errors")
    df_errors = pd.DataFrame(errors, columns=["repo_url", "error"])
    df_errors.to_csv(DATA_DIR / error_file, index=False)

    # delete prior checkpoint
    if len(commits) > save_at:
        os.remove(f"merged_prs_commits_{len(commits) - save_at}.csv")

    print(f"Commits saved to {output_file}")