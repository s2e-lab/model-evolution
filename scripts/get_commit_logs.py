"""
This script clones the repositories from Hugging Face and extracts the commit history.
It reads the repositories from a JSON file (subset of model repositories) and saves the commits to a CSV file.
It also saves the errors to a separate CSV file.
@Author: Joanna C. S. Santos
"""
import argparse
import os
from datetime import datetime
from pathlib import Path
import json
import sqlite3
import git
import pandas as pd
from tqdm import tqdm

from utils import clone, DATA_DIR, delete_folder, enforce_ssh

NULL_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


def load_cache(cache_path: Path) -> None:
    with sqlite3.connect(cache_path) as connection:
        fields = ",".join([
            "repo_url TEXT PRIMARY KEY",
            "commits TEXT",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ])
        connection.execute(f"CREATE TABLE IF NOT EXISTS commit_cache ({fields})")


def get_cached_commits(cache_path: Path, repo_url: str)  -> list | None:
    with sqlite3.connect(cache_path) as connection:
        query = "SELECT commits FROM commit_cache WHERE repo_url = ?"
        row = connection.execute(query, (repo_url,), ).fetchone()

    if row is None: return None

    commits_json = row[0]
    return json.loads(commits_json) if commits_json else []


def save_to_cache(cache_path: Path, repo_url: str, commits: list ) -> None:
    with sqlite3.connect(cache_path) as connection:
        connection.execute("""
                           INSERT INTO commit_cache (repo_url, commits, updated_at)
                           VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT(repo_url) DO
                           UPDATE SET
                               commits = excluded.commits,
                               updated_at = CURRENT_TIMESTAMP
                           """, (repo_url, json.dumps(commits)))


def get_commits(repo_path: str) -> tuple:
    """
    Get the commits from a repository
    :param repo_path: where the repository is cloned.
    :return: a list of tuples with the commit information.
    """
    repository = git.Repo(repo_path)

    commits = []

    # Iterate through the commits
    for commit in repository.iter_commits():
        commit_date = datetime.fromtimestamp(commit.committed_date)
        # skip commits made after 2024
        if commit_date.year > 2024: continue

        all_files_in_tree = [item.path for item in commit.tree.traverse()]
        if commit.parents:
            file_diffs = commit.parents[0].diff(commit)  # Compare with the parent+
            # changed files
            change_type = {'A': '+', 'D': '-', 'M': '*', 'R': '=', 'T': '>', 'C': '<'}
            changed_files = []
            for diff in file_diffs:
                file_path = diff.b_path if diff.b_path else diff.a_path  # Handle path based on change
                file_path = change_type[diff.change_type] + " " + file_path
                changed_files.append(file_path)
        else:
            file_diffs = commit.diff(NULL_TREE)  # Compare with an empty tree (initial commit)
            changed_files = [f"+ {diff.a_path}" for diff in file_diffs]

        commits.append(
            (commit.hexsha, commit.author.name, commit_date.strftime('%Y-%m-%d %H:%M:%S'),
             commit.message.strip(), ";".join(changed_files), ";".join(all_files_in_tree))
        )

    return commits


def parse_args():
    parser = argparse.ArgumentParser(description="Process repository group.")
    parser.add_argument("--group_type", required=True, choices=["legacy", "recent"], help="Choices: 'legacy' or 'recent'.")
    return parser.parse_args()


def save(data: list, columns: list, out_file: str | Path) -> None:
    """
    Save the commits to a CSV file
    :param data: the data to be saved.
    :param columns: header of the CSV file
    :param out_file: where to save the CSV file.
    """
    df_commits = pd.DataFrame(data, columns=columns)
    df_commits.to_csv(out_file, index=False)


def extract_all_commits(repositories: list, output_path: Path, error_path: Path, exclude_repos: set = None) -> None:
    """
    Extract all commits from a list of repositories and save them to a CSV file.
    :param output_path: where to save the CSV file containing the commits.
    :param error_path: where to save the CSV file containing the errors.
    :param repositories: list of repositories' URLs (eg: `organization/repoName`).
    :param exclude_repos: a list of previously saved repositories that we don't need to get commit logs for.
    """
    commits, errors =  [], []
    commits_columns = ["repo_url", "commit_hash", "author", "date", "message", "changed_files", "all_files_in_tree"]
    error_columns = ["repo_url", "error"]

    cache_path = DATA_DIR / "_commits_cache.sqlite3"
    exclude_repos = exclude_repos or set()
    load_cache(cache_path)

    for repo_url in tqdm(repositories, unit="repo", total=len(repositories)):
        if repo_url in exclude_repos: continue  # Skip repositories that have already been processed

        cached_commits = get_cached_commits(cache_path, repo_url)

        if cached_commits is not None:
            commits.extend((repo_url, *commit) for commit in cached_commits)
            continue

        clone_path = os.path.join("./tmp", repo_url.replace("/", "+"))
        try:
            repo = clone(repo_url, clone_path, True)
            repo_commits = get_commits(clone_path)
            save_to_cache(cache_path, repo_url, repo_commits)
            repo_commits = [(repo_url,) + c for c in repo_commits]
            commits.extend(repo_commits)
            repo.close()
        except Exception as e:
            print(f"Error processing {repo_url}: {e}")
            errors.append((repo_url, str(e)))
        finally:
            if os.path.exists(clone_path):
                delete_folder(clone_path)

    # save the rest of the commits to CSV
    save(commits, commits_columns, output_path)
    save(errors, error_columns, error_path)


if __name__ == "__main__":
    # ensure we have SSH setup with Hugging Face
    enforce_ssh()

    # Parse command line arguments
    args = parse_args()

    # grab the list of selected repositories' IDs from JSON file
    input_file = DATA_DIR / f"selected_{args.group_type}_repos.json"
    repo_urls = pd.read_json(input_file)["id"].tolist()

    # where to save data
    output_file = DATA_DIR / f"{input_file.stem.replace('_repos', '_commits')}.csv"
    error_file = output_file.with_name(output_file.name.replace("_commits", "_errors"))

    print(f"Extracting commits for repos listed in {input_file.name}")
    extract_all_commits(repo_urls, output_file, error_file)

    print(f"Commits saved to {output_file.name}")
    print(f"Errors saved to {error_file.name}")
    print("Done!")
    print("Recommended next steps:")
    print("\t1. Run the tests on tests/test_get_commit_logs.py to check the results.")
    print("\t2. Run the scripts/analyze_commit_history.py to identify the serialization format used in each saved model file.")
