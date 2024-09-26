import pandas as pd
import os
from datetime import datetime
import shutil
import git
from tqdm import tqdm


def clone(repo_url: str, clone_path: str) -> None:
    """
    Clone a repository from Hugging Face
    :param repo_url: the repository URL (e.g., "huggingface/transformers")
    :param clone_path: where to clone the repository locally.
    """
    clone_url = f"git@hf.co:{repo_url}"
    # Check if the repository directory already exists
    if not os.path.exists(clone_path):
        shutil.rmtree(clone_path, ignore_errors=True)
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
        commits.append(
            (commit.hexsha, commit.author.name, commit_date.strftime('%Y-%m-%d'),
             commit.message, ";".join(changed_files))
        )

    return commits


if __name__ == "__main__":
    # read start index and end index from the command line
    import sys
    sys.argv = ["get_repo_history.py", "0", "1"]
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
        end_idx = int(sys.argv[2])
    else:
        print("Usage: python get_repo_history.py <start_index> <end_index>")
        sys.exit(1)



    input_file = "../data/huggingface_sort_by_createdAt_top996939_selected.json"
    df = pd.read_json(input_file)
    repo_urls = df["id"].tolist()
    # iterates over the repositories
    commits = []
    for repo_url in tqdm(repo_urls[start_idx:end_idx]):
        clone_path = os.path.join("./tmp", repo_url.replace("/", "+"))  # Replace with your desired local path
        # clone(repo_url, clone_path)
        repo_commits = get_commits(clone_path)
        repo_commits = [(repo_url,) + c for c in repo_commits]
        commits.extend(repo_commits)

    # save the commits to CSV

    df_commits = pd.DataFrame(commits, columns=["repo_url", "commit_hash", "author", "date", "message", "changed_files"])
    df_commits.to_csv("../data/huggingface_sort_by_createdAt_top996939_selected_commits.csv", index=False)