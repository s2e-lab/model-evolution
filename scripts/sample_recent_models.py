#!/usr/bin/env python
# coding: utf-8
"""
It samples recent model repositories to include on our study, using the sampling strategy described here:
@Author: Joanna C. S. Santos
"""

import random
import pandas as pd

# from analyticaml import MODEL_FILE_EXTENSIONS
# FIXME, hardcoded for now LMAO
MODEL_FILE_EXTENSIONS = {'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill', 'pth', 'pt', 'ts', 'model', 'pb', 'joblib', 'npy',
                         'npz', 'onnx', 'safetensors'}
from utils import load, DATA_DIR


def sample(df: pd.DataFrame, total: int):
    """
    Return a DataFrame with `total` rows, allocating (as evenly as possible)
    the same number of samples to each calendar month between min(date_col)
    and max(date_col).
    :param df: DataFrame to sample from
    :param total: total number of samples to return
    :return: DataFrame with `total` rows, sampled from the input DataFrame
    """
    random.seed(42)  # make sampling procedure reproducible
    date_col = "created_at"  # column to sample on
    # 1) Normalise the date column and attach a Year‑Month bucket (Period[M])
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
    df["month"] = df[date_col].dt.tz_localize(None).dt.to_period("M")  # .dt.to_period("M")

    # 2) Ordered list of months (oldest → newest)
    months = sorted(df["month"].unique())
    m = len(months)
    # print(df["month"].min(), df["month"].max())

    # 3) Base allocation per month + distribute the remainder deterministically
    base = total // m
    remainder = total % m
    allocation = {month: base for month in months}
    for month in months[:remainder]:  # bump the first `remainder` months
        allocation[month] += 1

    # 4) First pass: sample up to the allocation from each month
    sampled_idx = []
    deficits = 0

    for month in months:
        month_idx = df.index[df["month"] == month].tolist()
        k = allocation[month]
        # If we have enough samples for this month, sample k items
        if len(month_idx) >= k:
            sampled_idx.extend(random.sample(month_idx, k))
        else:  # keep everything, and track how many we still need for sampling (shortfall)
            sampled_idx.extend(month_idx)
            deficits += k - len(month_idx)

    # 5) Second pass: fill any shortfall from the still‑unsampled pool
    if deficits > 0:
        remaining_pool = list(set(df.index) - set(sampled_idx))
        sampled_idx.extend(random.sample(remaining_pool, deficits))

    sampled_df = df.loc[sorted(sampled_idx)].reset_index(drop=True)
    sampled_df = sampled_df.drop(columns="month")
    return sampled_df


if __name__ == "__main__":
    input_file = DATA_DIR / "all_recent_repos.json.zip"
    out_recent_models_file = DATA_DIR / "v2_select_recent_repos.json"

    # Step 1: Load the repositories' metadata
    print(f"Loading recent repository data from {input_file.name}...")
    df = load(input_file)
    df['last_modified'] = pd.to_datetime(df['last_modified'], utc=True)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    df['gated'] = df['gated'].astype(bool)
    df['size'] = 0  # initialize size column

    # Step 2 - Sample recent repositories
    print(f"Sampling len{df} recent repositories...")
    df_recent = pd.DataFrame(columns=df.columns)
    num_extra = 10  # number of extra repositories to sample from the recent period
    target_size = 1703
    df_recent = sample(df, target_size+num_extra)


    df_recent.reset_index(inplace=True)
    # Check if the number of legacy and recent repositories is the same
    assert target_size + num_extra == len(df_recent), "Number of legacy and recent repositories should be the same"
    print(f"Selected repositories:  {len(df_recent)} recent repos")

    # Step 5 - Save the data
    df_recent.to_json(out_recent_models_file, orient="records", indent=2)


