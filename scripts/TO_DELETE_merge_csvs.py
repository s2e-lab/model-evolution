"""
This script clones the repositories from Hugging Face and extracts the commit history.
It reads the repositories from a JSON file (subset of model repositories) and saves the commits to a CSV file.
It also saves the errors to a separate CSV file.

Notice that if you want to retry the repositories that failed, you should set the variable should_retry to True.
@Author: Joanna C. S. Santos
"""
from pathlib import Path

import pandas as pd

if __name__ == "__main__":

    prior_results = [
        Path("../data/fixed3_repository_evolution_commits_0_2300.csv"),
        Path("../data/fixed3_repository_evolution_commits_2301_2507.csv"),
        Path("../data/fixed3_repository_evolution_commits_2507_5014.csv")
    ]
    # create a dataframe to hold the merged results
    df_commits = pd.DataFrame(
        columns=["repo_url", "commit_hash", "model_file_path", "serialization_format", "message", "author", "date"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])

    for file in prior_results:
        df1 = pd.read_csv(file)
        # add to df_commits
        df_commits = pd.concat([df_commits, df1], ignore_index=True)
        df2 = pd.read_csv(file.with_name(file.name.replace("commits", "errors")))
        # add to df_errors
        df_errors = pd.concat([df_errors, df2], ignore_index=True)

    # save the merged results
    out_file = Path("../data/fixed3_repository_evolution_commits_0_5014.csv")
    df_commits.to_csv(out_file, index=False)
    df_errors.to_csv(out_file.with_name(out_file.name.replace("commits", "errors")), index=False)
    print(len(df_commits))
    # how many unique [repo_url, commit_hash] are there?
    print(len(df_commits[["repo_url", "commit_hash"]].drop_duplicates()))
