#!/usr/bin/env python
# coding: utf-8
"""
Selecting model repositories to include on our study.
@Author: Joanna C. S. Santos
"""

import random

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS
from huggingface_hub import HfApi
from tqdm import tqdm

from scripts.utils import load
from utils import DATA_DIR

SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-22", utc=True)
FIRST_DAY_OF_2024 = pd.to_datetime("2024-01-01", utc=True)
SIZE_LIMIT = 2 * 1024 * 1024 * 1024 * 1024  # 2 TB
api = HfApi()


def has_model_file(model_files: list) -> bool:
    """
    This function checks if a model has at least one model file.
    :param model_files: list of files in the repository.
    :return: True if the repository has at least one model file, False otherwise.
    """
    return any([file["extension"] in MODEL_FILE_EXTENSIONS for file in model_files])


def get_repo_size(repo_id: str) -> int:
    """
    This function gets the size of a repository.
    :param repo_id: id of the repository
    :return: size of the repository in bytes
    """
    try:
        model_info = api.model_info(repo_id, files_metadata=True)
        # Get the model files
        repo_files = []
        if model_info.siblings:
            for sibling in model_info.siblings:
                repo_file = vars(sibling)
                repo_file["extension"] = repo_file["rfilename"].rsplit(".", 2)[-1]
                repo_files.append(repo_file)

        return model_info.usedStorage, repo_files
    except:
        return 0, []  # If the repository does not exist or cannot be accessed, return 0 size


def exclude_models(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function excludes models based on the following exclusion criteria (EC):
    (E1) - Not modified on or after 2024
    (E2) - Does not have at least one model file
    (E3) - Gated (i.e. private)
    :param df: data frame with all models' metadata
    :return: a data frame with the selected models that are not larger than 2 TB.
    """
    # find repositories that are modified on or after 2024
    df_filtered = df[df["last_modified"] >= FIRST_DAY_OF_2024]
    # find repositories that have at least one model file
    df_filtered = df_filtered[df_filtered["siblings"].apply(has_model_file)]
    # find non-gated repositories
    df_filtered = df_filtered[~df_filtered["gated"]]
    return df_filtered


def filter_by_size(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function filters the repositories that are larger than 2 TB.
    :param df: data frame with all models' metadata
    :return: a data frame with the selected models that are not larger than 2 TB.
    """
    # get the size of the repositories and add to the dataframe
    for idx, repo in tqdm(df.iterrows(), total=len(df), unit="repo"):
        df.at[idx, "size"], df.at[idx, "siblings"] = get_repo_size(repo["id"])
    # exclude repositories that are larger than 2 TB and not empty
    return df[(df["size"] < SIZE_LIMIT) & (df["size"] > 0)]


def select_legacy(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function returns the repositories created before safetensors' release date.
    :param df: data frame with all models'  metadata
    :return: a data frame with the selected models that are 'legacy'.
    """
    return df[df["created_at"] < SAFETENSORS_RELEASE_DATE]


def select_recent(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function filters the repositories created after safetensors' release date.
    :param df: data frame with all models'  metadata
    :return: a data frame with the selected models
    """
    return df[df["created_at"] >= SAFETENSORS_RELEASE_DATE]


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


def create_size_cache():
    """
    This function creates a cache of the sizes of the repositories.
    It saves the cache to a file in the DATA_DIR.
    """
    size_cache = {}
    df_cache = load(DATA_DIR / "hf_sort_by_createdAt_top1210660.json.zip")
    for _, row in df_cache.iterrows():
        repo_id = row["id"]
        repo_size = row["usedStorage"] if "usedStorage" in row else 0
        sha = row["sha"]
        size_cache[f"{repo_id}_{sha}"] = repo_size
    return size_cache


if __name__ == "__main__":
    input_file = DATA_DIR / "hf_sort_by_createdAt_top1209409.json.zip"
    out_legacy_models_file = DATA_DIR / "selected_legacy_repos.json"
    out_recent_models_file = DATA_DIR / "selected_recent_repos.json"

    # Step 1: Load the repositories' metadata
    print(f"Loading data from {input_file}...")
    df = load(input_file)
    df['last_modified'] = pd.to_datetime(df['last_modified'], utc=True)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    df["gated"] = df["gated"].astype(bool)
    df["size"] = 0  # initialize size column

    # Notice that 2022-03-02T23:29:04.000Z assigned to all repositories created before HF began storing creation dates.
    print("Min creation date = ", df["created_at"].min())

    # Step 2 - Exclude models
    print(f"Excluding models from {input_file} (initial size = {len(df)})...")
    df = exclude_models(df)

    # Step 3 - Inspect the repositories and identify legacy repositories
    print("Selecting legacy repositories...")
    df_legacy = select_legacy(df)
    df_legacy = filter_by_size(df_legacy)

    # Step 4 - Sample recent repositories
    print("Selecting recent repositories...")
    df_copy = df.copy()
    df_recent = pd.DataFrame(columns=df_copy.columns)

    while len(df_legacy) != len(df_recent):
        # sample and add to df_recent
        print(f"SAMPLING RECENT REPOSITORIES... {len(df_legacy) - len(df_recent)}")
        selected = sample(select_recent(df_copy), len(df_legacy) - len(df_recent))
        selected = filter_by_size(selected)
        print(f"\tAfter filtering, {len(selected)} recent repositories left")

        df_recent = selected if df_recent.empty else pd.concat([df_recent, selected])
        # df_recent =
        print(f"\tCurrent recent sample size {len(df_recent)} recent repositories...")

        # exclude from df_copy the repositories that were already sampled
        df_copy = df_copy[~df_copy["id"].isin(df_recent["id"])]
        print(f"\tCurrent copy sample size {len(df_copy)}...")

    df_recent.reset_index(inplace=True)
    # Check if the number of legacy and recent repositories is the same
    assert len(df_legacy) == len(df_recent), "Number of legacy and recent repositories should be the same"
    print(f"Selected repositories: {len(df_legacy)} legacy / {len(df_recent)} recent")
    # Step 3 - Save the data
    df_legacy.to_json(out_legacy_models_file, orient="records", indent=2)
    df_recent.to_json(out_recent_models_file, orient="records", indent=2)
    print(f"Saved the selected repositories to {out_legacy_models_file} / {out_recent_models_file}")
    print(len(df_legacy), "legacy repositories selected for the study")
    print(f"\tLegacy Period: {df_legacy['created_at'].min()} - {df_legacy['created_at'].max()}")
    print(len(df_recent), "recent repositories selected for the study")
    print(f"\tRecent Period: {df_recent['created_at'].min()} - {df_recent['created_at'].max()}")
