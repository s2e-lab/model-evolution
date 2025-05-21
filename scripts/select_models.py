#!/usr/bin/env python
# coding: utf-8
"""
Selecting model repositories to include on our study.
"""

import os
import random
import zipfile
from pathlib import Path

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS

from utils import DATA_DIR

SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-22", utc=True)

def load(file_path: Path) -> pd.DataFrame:
    """
    This function loads the data from the Hugging Face API.
    :param file_path: path to the zip file to be loaded.
    :return: a pandas DataFrame with the metadata of the models.
    """
    # uncompress zip file to the DATA_DIR
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(DATA_DIR)
    # load the data
    df = pd.read_json(file_path.with_suffix(""))
    # delete the unzipped file
    os.remove(file_path.with_suffix(""))
    return df


def has_model_file(model_files: list) -> bool:
    """
    This function checks if a model has at least one model file.
    :param model_files: list of files in the repository.
    :return: True if the repository has at least one model file, False otherwise.
    """
    return any([file["extension"] in MODEL_FILE_EXTENSIONS for file in model_files])


def filter_legacy(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function filters the repositories based on the following criteria:
    - models created before 22 September 2022; AND
    - models last modified in 2024; AND
    - models with at least one model file; AND
    - models that are not gated.
    :param df: data frame with all models'  metadata
    :return: a data frame with the selected models that are 'legacy'.
    """
    # find models created_at before 22 September 2022 and last_modified in 2024

    df_filtered = df[(df["created_at"] < SAFETENSORS_RELEASE_DATE) & (df["last_modified"].dt.year == 2024)]
    # find model repositories with at least one model file (extension in MODEL_FILE_EXTENSIONS)
    df_filtered = df_filtered[df_filtered["siblings"].apply(has_model_file)]
    # exclude gated repositories
    df_filtered = df_filtered[~df_filtered["gated"]]
    return df_filtered


def filter_recent(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function filters the repositories based on the following criteria:
    - models created on or after 22 September 2022; AND
    - models last modified in 2024; AND
    - models with at least one model file; AND
    - models that are not gated.
    :param df: data frame with all models'  metadata
    :return: a data frame with the selected models
    """
    # find models created_at on or after RELE and last_modified in 2024
    df_filtered = df[(df["created_at"] >= SAFETENSORS_RELEASE_DATE) & (df["last_modified"].dt.year == 2024)]
    # find model repositories with at least one model file (extension in MODEL_FILE_EXTENSIONS)
    df_filtered = df_filtered[df_filtered["siblings"].apply(has_model_file)]
    # exclude gated repositories
    df_filtered = df_filtered[~df_filtered["gated"]]

    return df_filtered


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
    print(df["month"].min(), df["month"].max())

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
    input_file = DATA_DIR / "hf_sort_by_createdAt_top1211357.json.zip"
    out_legacy_models_file = DATA_DIR / "selected_legacy_repos.json"
    out_recent_models_file = DATA_DIR / "selected_recent_repos.json"

    # Step 1: Load the repositories' metadata
    print(f"Loading data from {input_file}...")
    df = load(input_file)
    df['last_modified'] = pd.to_datetime(df['last_modified'], utc=True)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    df["gated"] = df["gated"].astype(bool)

    # From Hugging Face API, we have the following information: created_at, last_modified, and siblings
    # Notice that 2022-03-02T23:29:04.000Z assigned to all repositories created before HF began storing creation dates.
    print("Min creation date = ", df["created_at"].min())

    # Step 2 - Filter the repositories and identify legacy and recent repositories
    print(f"Filtering data from {input_file}...")
    df_legacy = filter_legacy(df)
    df_recent = sample(filter_recent(df), len(df_legacy))

    # Check if the number of legacy and recent repositories is the same
    assert len(df_legacy) == len(df_recent), "Number of legacy and recent repositories should be the same"

    # Step 3 - Save the data
    df_legacy.to_json(out_legacy_models_file)
    df_recent.to_json(out_recent_models_file)
    print(f"Saved the selected repositories to {out_legacy_models_file} / {out_recent_models_file}")
    print(len(df_legacy), "legacy repositories selected for the study")
    print(f"\tLegacy Period: {df_legacy['created_at'].min()} - {df_legacy['created_at'].max()}")
    print(len(df_recent), "recent repositories selected for the study")
    print(f"\tRecent Period: {df_recent['created_at'].min()} - {df_recent['created_at'].max()}")
