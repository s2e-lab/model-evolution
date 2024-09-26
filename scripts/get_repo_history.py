"""
It is a Python script that clones a Git repository (if it doesn't already exist locally) and fetches the commit history within a specified date range.
The script uses the `git` module from the `GitPython` library to interact with the Git repository.
@author: Joanna C. S. Santos (joannacss@nd.edu)
"""
import csv
import os
from datetime import datetime

import git


def clone(repo_url: str, repo_path: str):
    # Check if the repository directory already exists
    if not os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)

    git.Repo.clone_from(repo_url, repo_path)


def get_commits_in_date_range(repo_path, start_date, end_date):
    repo = git.Repo(repo_path)
    commits = []

    # Iterate through the commits
    for commit in repo.iter_commits():
        commit_date = datetime.fromtimestamp(commit.committed_date)

        # Check if the commit falls within the date range
        if start_date <= commit_date <= end_date:
            # commit_info = f"{commit.hexsha} | {commit.author.name} | {commit_date.strftime('%Y-%m-%d')} | {commit.message.strip()}"
            # grabs as tuple
            commit_info = (commit.hexsha, commit.author.name, commit_date.strftime('%Y-%m-%d'), commit.message.strip())
            commits.append(commit_info)

    return commits


# Example usage:
repo_url = "saphvis/ngpx2022"  # Replace with your Git repository URL
repo_url = "glif/how2draw"  # Replace with your Git repository URL
clone_url = f"git@hf.co:{repo_url}"
repo_path = os.path.join("./tmp", repo_url.replace("/", "+"))  # Replace with your desired local path
start_date = datetime(2020, 1, 1)
end_date = datetime(2024, 12, 31)

# Step 1: Clone the repository if it doesn't already exist
clone(clone_url, repo_path)

# Step 2: Fetch the commit metadata within the date range
commit_metadata = get_commits_in_date_range(repo_path, start_date, end_date)
commit_metadata = [(repo_url,) + commit for commit in commit_metadata]

# Step 3: Save the list of commits to a file (repo_url + commit_info) as CSV
output_file = f"{repo_url.replace('/', '+')}_commits.csv"
with open(output_file, mode='w') as file:
    writer = csv.writer(file)
    writer.writerow(["Repo_url", "Commit ID", "Author", "Date", "Message"])
    writer.writerows(commit_metadata)

# Step 4: delete clone URL
import shutil

shutil.rmtree(repo_path)
