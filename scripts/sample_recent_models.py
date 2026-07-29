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


def sample(df: pd.DataFrame, seed: int = 42, previous_repos: set | None = None, exclude_repos: set | None=None) -> pd.DataFrame:
    """
    Return a temporally stratified sample.

    For each creation quarter, calculate the required sample size, prioritize
    repositories analyzed previously, and randomly fill any remaining slots.

    :param df: DataFrame to sample from.
    :param seed: Fixed random seed for reproducibility.
    :param previous_repos: Repository identifiers analyzed previously that you'd like to prioritize to pick to avoid re-running everything for cached results.
    :param exclude_repos:  Repositories to exclude from sampling because they are known to fail.
    :return: Sampled DataFrame.
    """
    random.seed(seed)
    previous_repos = previous_repos or set()
    exclude_repos = exclude_repos or set()

    date_col = "created_at"
    repo_col = "id"  # Change to "id" if that is the identifier in df.

    df = df.copy()
    df[date_col] = pd.to_datetime(
        df[date_col],
        utc=True,
        errors="coerce"
    )
    df = df.dropna(subset=[date_col])
    if exclude_repos:
        df = df[~df[repo_col].isin(exclude_repos)]
    print(f"Sampling from {len(df)} repositories...")

    df["quarter"] = df[date_col].dt.tz_localize(None).dt.to_period("Q")


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

    # Step 1.1: When we need to retry from where we stopped to grab more samples after some failed
    # we load the previous ones such that we can ensure they are still selected again
    df_previous = pd.read_json(DATA_DIR / "selected_recent_repos.json")
    previous_repos = set(df_previous["id"].tolist())
    print(f"Found {len(previous_repos)} previous repositories.")
    exclude_repos = {
        'thejosango/nuha', 'AI-Sweden-Models/gpt-sw3-6.7b-v2'
        'fayetitchenal/segformer_finetuned_test_110424', 'besimray/miner_id_3_794df6f6-b398-448d-8972-ec017a83142c_1730836890', 'kiupuc/speecht5_tts',
        'iamanaiart/LCM-hardcoreHentai13_v13Baked-openvino', 'EmbeddedLLM/Phi-3-vision-128k-instruct-onnx',
        'SR467/xzg','mjmanashti/fingemma-2b-ti','CHShakish/my-pet-dog', 'sartifyllc/African-Cross-Lingua-Embeddings-Model', 'JaaackXD/Llama-3-70B-Instruct-GGUF','polyconnect/dqn-SpaceInvadersNoFrameskip-v4', 'Kwai-Kolors/Kolors',
    }

    # Step 2: Sample recent repositories.
    df_recent = sample(df, seed=42, previous_repos=previous_repos, exclude_repos=exclude_repos)
    df_recent.reset_index(drop=True, inplace=True)

    print(f"Selected repositories: {len(df_recent)} recent repos")

    # Step 3: Save the sampled repositories.
    df_recent.to_json(out_recent_models_file, orient="records", indent=2)
    print("Done!")
    print("Recommended next steps:")
    print("\t- Run the get_commit_logs.py to download the commits logs for the selected repositories.")
