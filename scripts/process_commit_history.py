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
    # load legacy data
    _, df_legacy_evolution_commits, df_legacy_evolution_errors = load("legacy")
    print(f"# Legacy commits BEFORE excluding failed repos: {len(df_legacy_evolution_commits)} "
          f"over {df_legacy_evolution_commits['repo_url'].nunique()} unique repositories.")
    df_legacy_evolution_commits = exclude_failed_repos(df_legacy_evolution_commits, df_legacy_evolution_errors)
    print(f"# Legacy commits AFTER excluding failed repos: {len(df_legacy_evolution_commits)} "
          f"over {df_legacy_evolution_commits['repo_url'].nunique()} unique repositories.")
    # load recent data
    _, df_recent_evolution_commits, df_recent_evolution_errors = load("recent")
    print(f"# Recent commits BEFORE excluding failed repos: {len(df_recent_evolution_commits)} "
          f"over {df_recent_evolution_commits['repo_url'].nunique()} unique repositories.")
    df_recent_evolution_commits = exclude_failed_repos(df_recent_evolution_commits, df_recent_evolution_errors)
    print(f"# Recent commits AFTER excluding failed repos: {len(df_recent_evolution_commits)} "
          f"over {df_recent_evolution_commits['repo_url'].nunique()} unique repositories.")

    # make df_recent_evolution_commits have the same number of unique repo_url as df_legacy_evolution_commits
    unique_legacy_repos = df_legacy_evolution_commits["repo_url"].unique()
    unique_recent_repos = df_recent_evolution_commits["repo_url"].unique()

    print("# Legacy repo URLs:", len(unique_legacy_repos))
    print("# Recent repo URLs:", len(unique_recent_repos))
    # randomly sample df_recent_evolution_commits
    random.seed(42)  # for reproducibility
    sampled_recent_repos = random.sample(list(unique_recent_repos), len(unique_legacy_repos))
    df_recent_evolution_commits = df_recent_evolution_commits[df_recent_evolution_commits["repo_url"].isin(sampled_recent_repos)]
    print(f"# Recent commits AFTER balancing: {len(df_recent_evolution_commits)} "
          f"over {df_recent_evolution_commits['repo_url'].nunique()} unique repositories.")

    # save the data
    df_legacy_evolution_commits.to_csv(DATA_DIR / "repositories_evolution_legacy_commits_processed.csv", index=False)
    df_recent_evolution_commits.to_csv(DATA_DIR / "repositories_evolution_recent_commits_processed.csv", index=False)

    # assert they have the same nuymber of unique repo_url
    assert df_legacy_evolution_commits["repo_url"].nunique() == df_recent_evolution_commits["repo_url"].nunique(), \
        "The number of unique repositories in legacy and recent commits should be the same after balancing."