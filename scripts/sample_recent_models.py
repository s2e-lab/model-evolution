#!/usr/bin/env python
# coding: utf-8
"""
Samples recent model repositories using temporally stratified random sampling.

Each creation quarter receives a minimum allocation, and the remaining sample
is distributed proportionally to the number of repositories in each quarter.

@Author: Joanna C. S. Santos
"""

import random
import pandas as pd
from utils import load, DATA_DIR, calculate_sample_size


def sample(df: pd.DataFrame, seed: int = 42):
    """
    Return a temporally stratified random sample.

    For each creation quarter, calculate the sample size (S) needed for 95% confidence and a 5% margin of error,
    then randomly sample that number of repositories.

    :param df: DataFrame to sample from
    :param seed: fixed random seed for reproducibility
    :return: sampled DataFrame
    """
    random.seed(seed)

    date_col = "created_at"

    df = df.copy()
    df[date_col] = pd.to_datetime(
        df[date_col],
        utc=True,
        errors="coerce"
    )

    df = df.dropna(subset=[date_col])

    df["quarter"] = (
        df[date_col]
        .dt.tz_localize(None)
        .dt.to_period("Q")
    )

    quarters = sorted(df["quarter"].unique())
    sampled_idx = []

    print("Quarter sampling allocation:")

    for quarter in quarters:
        quarter_idx = df.index[df["quarter"] == quarter].tolist()

        population_size = len(quarter_idx)
        sample_size = calculate_sample_size(population_size, margin_error=0.05, confidence_level=0.95)

        print(f"{quarter}: population={population_size:,}, sample={sample_size:,}")

        sampled_idx.extend(random.sample(quarter_idx, sample_size))

    sampled_df = df.loc[sorted(sampled_idx)].reset_index(drop=True)
    sampled_df = sampled_df.drop(columns="quarter")

    return sampled_df

def sample_OLD(df: pd.DataFrame, seed: int = 42, previous_repos: set | None = None) -> pd.DataFrame:
    """
    Return a temporally stratified sample.

    For each creation quarter, calculate the required sample size, prioritize
    repositories analyzed previously, and randomly fill any remaining slots.

    :param df: DataFrame to sample from.
    :param seed: Fixed random seed for reproducibility.
    :param previous_repos: Repository identifiers analyzed previously.
    :return: Sampled DataFrame.
    """
    random.seed(seed)
    previous_repos = previous_repos or set()

    date_col = "created_at"
    repo_col = "id"  # Change to "id" if that is the identifier in df.

    df = df.copy()
    df[date_col] = pd.to_datetime(
        df[date_col],
        utc=True,
        errors="coerce"
    )
    df = df.dropna(subset=[date_col])

    df["quarter"] = (
        df[date_col]
        .dt.tz_localize(None)
        .dt.to_period("Q")
    )

    quarters = sorted(df["quarter"].unique())
    sampled_idx = []

    print("Quarter sampling allocation:")

    for quarter in quarters:
        quarter_df = df[df["quarter"] == quarter]

        population_size = len(quarter_df)
        sample_size = calculate_sample_size(
            population_size,
            margin_error=0.05,
            confidence_level=0.95
        )

        # Previously analyzed repositories in this quarter.
        previous_idx = quarter_df.index[
            quarter_df[repo_col].isin(previous_repos)
        ].tolist()

        # Repositories in this quarter that have not been analyzed.
        remaining_idx = quarter_df.index[
            ~quarter_df[repo_col].isin(previous_repos)
        ].tolist()

        # Randomize both pools reproducibly.
        random.shuffle(previous_idx)
        random.shuffle(remaining_idx)

        # Reuse as many previously analyzed repositories as possible.
        reused_idx = previous_idx[:sample_size]

        # Fill the remaining sample slots with new repositories.
        num_needed = sample_size - len(reused_idx)
        new_idx = random.sample(remaining_idx, num_needed)

        sampled_idx.extend(reused_idx)
        sampled_idx.extend(new_idx)

        print(
            f"{quarter}: population={population_size:,}, "
            f"sample={sample_size:,}, "
            f"reused={len(reused_idx):,}, "
            f"new={len(new_idx):,}"
        )

    sampled_df = df.loc[sorted(sampled_idx)].reset_index(drop=True)
    return sampled_df.drop(columns="quarter")


if __name__ == "__main__":
    input_file = DATA_DIR / "all_recent_repos.json.zip"
    out_recent_models_file = DATA_DIR / "selected_recent_repos.json"

    # Step 1: Load the repositories' metadata.
    print(f"Loading recent repository data from {input_file.name}...")
    df = load(input_file)
    # df_previous = pd.read_csv(DATA_DIR / "v1_selected_recent/repositories_evolution_recent_commits_processed.csv")
    # previous_repos = set(df_previous["repo_url"].tolist())
    # print(f"Found {len(previous_repos)} previous repositories.")

    # Step 2: Sample recent repositories.
    print(f"Sampling from {len(df)} recent repositories...")

    df_recent = sample(df, seed=42)#, previous_repos=previous_repos)
    df_recent.reset_index(drop=True, inplace=True)

    print(f"Selected repositories: {len(df_recent)} recent repos")

    # Step 3: Save the sampled repositories.
    df_recent.to_json(out_recent_models_file, orient="records", indent=2)
    print("Done!")
    print("Recommended next steps:")
    print("\t- Run the get_commit_logs.py to download the commits logs for the selected repositories.")
