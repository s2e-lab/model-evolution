import pandas as pd

from utils import DATA_DIR
import random

def load(group: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the commit history data for a given group.
    :param group: The group of commits to load (e.g., 'recent', 'all').
    :return: A tuple containing the following DataFrames: df_commits, df_evolution_commits, df_evolution_errors.
    """
    df_commits = pd.read_csv(DATA_DIR / f"selected_{group}_commits.csv").fillna("")
    df_evolution_commits = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_commits.csv")
    df_evolution_errors = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_errors.csv")
    print(f"Number of repos  {len(df_commits['repo_url'].unique())} ")
    print(f"Number of repos with errors {len(df_evolution_errors['repo_url'].unique())} ")
    return df_commits, df_evolution_commits, df_evolution_errors


def exclude_failed_repos(df_evolution_commits: pd.DataFrame, df_evolution_errors: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude repositories that failed from the commits DataFrame.
    :param df_evolution_commits: DataFrame containing commit information.
    :param df_evolution_errors: DataFrame containing errors for repositories.
    :return: Filtered DataFrame excluding failed repositories.
    """
    failed_repos = set(df_evolution_errors["repo_url"].unique())
    return df_evolution_commits[~df_evolution_commits["repo_url"].isin(failed_repos)]



if __name__ == "__main__":
    # load recent data
    group = "recent"
    df_recent_commits, df_recent_evolution_commits, df_recent_evolution_errors = load(group)
    # find repos in df_recent_commits that are missing in df_recent_evolution_commits
    missing_repos = set(df_recent_commits["repo_url"]) - set(df_recent_evolution_commits["repo_url"])
    print(f"Number of missing repos in evolution commits: {len(missing_repos)}")
    # filter df_recent_commits to only include missing repos
    df_recent_missing_commits = df_recent_commits[df_recent_commits["repo_url"].isin(missing_repos)]
    print(f"Number of missing commits: {len(df_recent_missing_commits)}")
    # save the missing commits to a CSV file
    output_file = DATA_DIR / f"selected_{group}_commits_retry.csv"
    df_recent_missing_commits.to_csv(output_file, index=False)