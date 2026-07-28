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

# from analyticaml import MODEL_FILE_EXTENSIONS
# FIXME, hardcoded for now LMAO
MODEL_FILE_EXTENSIONS = {
    'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill', 'pth', 'pt',
    'ts', 'model', 'pb', 'joblib', 'npy', 'npz', 'onnx', 'safetensors'
}

from utils import load, DATA_DIR


def sample(
        df: pd.DataFrame,
        total: int,
        min_per_quarter: int = 100,
        seed: int = 42
):
    """
    Return a temporally stratified random sample of `total` repositories.

    Each creation quarter receives up to `min_per_quarter` repositories.
    The remaining sample is allocated proportionally to the population of
    each quarter.

    :param df: DataFrame to sample from
    :param total: total number of samples to return
    :param min_per_quarter: minimum target allocation for each quarter
    :param seed: random seed used for reproducibility
    :return: DataFrame containing `total` sampled rows
    """
    random.seed(seed)

    if total > len(df):
        raise ValueError(
            f"Cannot sample {total} repositories from a population of {len(df)}."
        )

    date_col = "created_at"

    # 1) Normalize dates and attach a year-quarter stratum.
    df = df.copy()
    df[date_col] = pd.to_datetime(
        df[date_col],
        utc=True,
        errors="coerce"
    )

    # Repositories without a valid creation date cannot be temporally stratified.
    df = df.dropna(subset=[date_col])

    df["quarter"] = (
        df[date_col]
        .dt.tz_localize(None)
        .dt.to_period("Q")
    )

    # 2) Ordered list of quarters.
    quarters = sorted(df["quarter"].unique())
    num_quarters = len(quarters)

    if min_per_quarter * num_quarters > total:
        raise ValueError(
            f"min_per_quarter={min_per_quarter} requires at least "
            f"{min_per_quarter * num_quarters} samples across "
            f"{num_quarters} quarters, but total={total}."
        )

    quarter_sizes = df["quarter"].value_counts().to_dict()

    # 3) Give each quarter a minimum allocation, capped by its population.
    allocation = {
        quarter: min(min_per_quarter, quarter_sizes[quarter])
        for quarter in quarters
    }

    remaining = total - sum(allocation.values())

    # 4) Distribute remaining slots proportionally to each quarter's
    # remaining population capacity.
    while remaining > 0:
        capacity = {
            quarter: quarter_sizes[quarter] - allocation[quarter]
            for quarter in quarters
            if allocation[quarter] < quarter_sizes[quarter]
        }

        if not capacity:
            raise ValueError(
                "Not enough eligible repositories to complete the sample."
            )

        total_capacity = sum(capacity.values())

        # Largest-remainder proportional allocation.
        raw_additions = {
            quarter: remaining * capacity[quarter] / total_capacity
            for quarter in capacity
        }

        additions = {
            quarter: min(
                capacity[quarter],
                int(raw_additions[quarter])
            )
            for quarter in capacity
        }

        added = sum(additions.values())

        for quarter, amount in additions.items():
            allocation[quarter] += amount

        remaining -= added

        # Assign rounding remainder according to the largest fractional parts.
        if remaining > 0:
            ranked_quarters = sorted(
                capacity,
                key=lambda quarter: (
                        raw_additions[quarter] - int(raw_additions[quarter])
                ),
                reverse=True
            )

            for quarter in ranked_quarters:
                if remaining == 0:
                    break

                if allocation[quarter] < quarter_sizes[quarter]:
                    allocation[quarter] += 1
                    remaining -= 1

    # 5) Randomly sample within each quarter.
    sampled_idx = []

    for quarter in quarters:
        quarter_idx = df.index[df["quarter"] == quarter].tolist()
        sampled_idx.extend(
            random.sample(quarter_idx, allocation[quarter])
        )

    sampled_df = df.loc[sorted(sampled_idx)].reset_index(drop=True)
    sampled_df = sampled_df.drop(columns="quarter")

    assert len(sampled_df) == total
    return sampled_df


if __name__ == "__main__":
    input_file = DATA_DIR / "all_recent_repos.json.zip"
    out_recent_models_file = DATA_DIR / "v2_select_recent_repos.json"

    # Step 1: Load the repositories' metadata.
    print(f"Loading recent repository data from {input_file.name}...")
    df = load(input_file)

    # Step 2: Sample recent repositories.
    print(f"Sampling from {len(df)} recent repositories...")

    target_size = 3850
    num_extra = 10
    sample_size = target_size + num_extra

    df_recent = sample(df, total=sample_size, min_per_quarter=100, seed=42)

    df_recent.reset_index(drop=True, inplace=True)

    assert sample_size == len(df_recent), (
        f"Expected {sample_size} recent repositories, "
        f"but sampled {len(df_recent)}."
    )

    print(f"Selected repositories: {len(df_recent)} recent repos")

    # Optional: display the number selected from each quarter.
    quarter_counts = (
        pd.to_datetime(df_recent["created_at"], utc=True)
        .dt.tz_localize(None)
        .dt.to_period("Q")
        .value_counts()
        .sort_index()
    )

    print("Sample allocation by creation quarter:")
    print(quarter_counts)

    # Step 3: Save the sampled repositories.
    df_recent.to_json(out_recent_models_file, orient="records", indent=2)
