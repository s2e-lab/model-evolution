"""
This script clones the repositories from Hugging Face and extracts the commit history.
It reads the repositories from a JSON file (subset of model repositories) and saves the commits to a CSV file.
It also saves the errors to a separate CSV file.

Notice that if you want to retry the repositories that failed, you should run with the argument `--retry`.
@Author: Joanna C. S. Santos
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import git
import pandas as pd
from analyticaml import check_ssh_connection
from tqdm import tqdm

from utils import clone, DATA_DIR, delete_folder

NULL_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


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


import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Process repository group.")
    # Positional arguments with strict choices
    parser.add_argument(
        "group_type",
        choices=["legacy", "recent"],
        help="Type of repository group to process: 'legacy' or 'recent'."
    )
    # Optional boolean flag
    parser.add_argument(
        "--retry",
        action="store_true",
        help="If set, the script will  retry the repositories that failed."
    )

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


if __name__ == "__main__":

    # Check if the SSH connection is working
    if not check_ssh_connection():
        print("Please set up your SSH keys on HuggingFace.")
        print("https://huggingface.co/docs/hub/en/security-git-ssh")
        print("Run the following command to check if your SSH connection is working:")
        print("ssh -T git@hf.co")
        print("If it is anonymous, you need to add your SSH key to your HuggingFace account.")
        sys.exit(1)

    # Parse command line arguments
    args = parse_args()
    group_type = args.group_type
    should_retry = args.retry
    print(f"Group type: {group_type}")
    print(f"Retry: {should_retry}")

    # Process the repositories
    if should_retry:
        input_file = DATA_DIR / f"hf_sort_by_createdAt_top996939_{group_type}_errors.csv"
        df = pd.read_csv(input_file)
        repo_urls = df["repo_url"].tolist()
        print(f"Retrying the repositories that failed from {input_file}")
        output_file = input_file.stem.replace("_errors", "_commits_retried") + ".csv"
        error_file = output_file.replace("commits", "errors")
    else:
        # read start index and end index from the command line
        input_file = DATA_DIR / f"hf_sort_by_createdAt_top996939_{group_type}_selected.json"
        df = pd.read_json(input_file)
        repo_urls = df["id"].tolist()[:1000]  # limit to 1000 repositories
        print(f"Extracting commits from {input_file}")
        output_file = input_file.stem.replace("_selected", "_commits") + ".csv"
        error_file = output_file.replace("commits", "errors")

    # iterates over the repositories
    commits, errors = [], []
    save_at = 50
    commits_columns = ["repo_url", "commit_hash", "author", "date", "message", "changed_files", "all_files_in_tree"]
    error_columns = ["repo_url", "error"]

    output_file = DATA_DIR / output_file
    error_file = DATA_DIR / error_file

    for i, repo_url in tqdm(enumerate(repo_urls), unit="repo", total=len(repo_urls)):
        clone_path = os.path.join("./tmp", repo_url.replace("/", "+"))
        try:
            repo = clone(repo_url, clone_path, True)
            repo_commits = get_commits(clone_path)
            repo_commits = [(repo_url,) + c for c in repo_commits]
            commits.extend(repo_commits)
            if i > 0 and i % save_at == 0:
                save(commits, commits_columns, output_file)
                save(errors, error_columns, error_file)
            repo.close()
        except Exception as e:
            print(f"Error processing {repo_url}: {e}")
            errors.append((repo_url, e))
        finally:
            if os.path.exists(clone_path):
                delete_folder(clone_path)

    # save the rest of the commits to CSV
    save(commits, commits_columns, output_file)
    save(errors, error_columns, error_file)

    print(f"Commits saved to {output_file}")
    print(f"Errors saved to {error_file}")
