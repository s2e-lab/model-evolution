"""
This script clones the repositories from Hugging Face and extracts the commit history.
It reads the repositories from a JSON file (subset of model repositories) and saves the commits to a CSV file.
It also saves the errors to a separate CSV file.

Notice that if you want to retry the repositories that failed, you should set the variable should_retry to True.
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

import utils


def clone(repo_url: str, clone_path: str) -> None:
    """
    Clone a repository from Hugging Face
    :param repo_url: the repository URL (e.g., "huggingface/transformers")
    :param clone_path: where to clone the repository locally.
    """
    clone_url = f"git@hf.co:{repo_url}"
    # Check if the repository directory already exists
    if os.path.exists(clone_path):
        utils.delete_folder(clone_path)
    git.Repo.clone_from(clone_url, clone_path)


def get_commits(clone_path: str):
    """
    Get the commits from a repository
    :param clone_path: where the repository is cloned.
    :return: a list of tuples with the commit information.
    """
    repo = git.Repo(clone_path)
    commits = []

    # Iterate through the commits
    for commit in repo.iter_commits():
        commit_date = datetime.fromtimestamp(commit.committed_date)
        changed_files = [x for x in commit.stats.files]
        all_files_in_tree = [item.path for item in commit.tree.traverse()]
        commits.append(
            (commit.hexsha, commit.author.name, commit_date.strftime('%Y-%m-%d %H:%M:%S'),
             commit.message.strip(), ";".join(changed_files), ";".join(all_files_in_tree))
        )

    return commits


def parse_args():
    """
    Parse the command line arguments
    :return: the start index and end index
    """
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
        end_idx = int(sys.argv[2])
    else:
        print("Usage: python get_repos_history.py <start_index> <end_index>")
        sys.exit(1)
    return start_idx, end_idx

if __name__ == "__main__":
    # Check if the SSH connection is working
    if not check_ssh_connection():
        print("Please set up your SSH keys on HuggingFace.")
        print("https://huggingface.co/docs/hub/en/security-git-ssh")
        print("Run the following command to check if your SSH connection is working:")
        print("ssh -T git@hf.co")
        print("If it is anonymous, you need to add your SSH key to your HuggingFace account.")
        sys.exit(1)

    #  set this to True if you want to retry the repositories that failed
    should_retry = True
    if should_retry:
        input_file = Path("../data/huggingface_sort_by_createdAt_top996939_errors_0_1035.csv")
        df = pd.read_csv(input_file)
        repo_urls = df["repo_url"].tolist()
        start_idx, end_idx = "RETRIED", len(repo_urls)
    else:
        # read start index and end index from the command line
        start_idx, end_idx = parse_args()
        input_file = Path("../data/huggingface_sort_by_createdAt_top996939_selected.json")
        df = pd.read_json(input_file)
        repo_urls = df["id"].tolist()
        repo_urls = repo_urls[start_idx:end_idx]


    # iterates over the repositories
    commits, errors = [], []

    for repo_url in tqdm(repo_urls, unit="repo"):
        try:
            clone_path = os.path.join("./tmp", repo_url.replace("/", "+"))
            clone(repo_url, clone_path)
            repo_commits = get_commits(clone_path)
            repo_commits = [(repo_url,) + c for c in repo_commits]
            commits.extend(repo_commits)
        except Exception as e:
            print(f"Error processing {repo_url}: {e}")
            errors.append((repo_url, e))
        finally:
            utils.delete_folder(clone_path)

    # save the commits to CSV
    columns = ["repo_url", "commit_hash", "author", "date", "message", "changed_files", "all_files_in_tree"]
    df_commits = pd.DataFrame(commits, columns=columns)
    output_file = input_file.stem.replace("_selected", "_commits_") + f"{start_idx}_{end_idx}.csv"
    output_file = Path("../data") / output_file
    df_commits.to_csv(output_file, index=False)

    # save errors to CSV
    error_file = input_file.stem.replace("_selected", "_errors_") + f"{start_idx}_{end_idx}.csv"
    error_file = Path("../data") / error_file
    df_errors = pd.DataFrame(errors, columns=["repo_url", "error"])
    df_errors.to_csv(error_file, index=False)

    print(f"Commits saved to {output_file}")
