#!/usr/bin/env python
# coding: utf-8
"""
It applies inclusion / exclusion criteria to select model repositories to include on our study.
Exclusion criteria:
    (E1) - Not modified on or after 2024
    (E2) - Does not have at least one model file
    (E3) - Gated (i.e. private)
    (E4) - Size <= `SIZE_LIMIT` (i.e. 1TB)
@Author: Joanna C. S. Santos
"""

import random
import os
import zipfile
import time
import re
import sqlite3
from math import ceil

import pandas as pd
import requests
from requests.models import Response

# from analyticaml import MODEL_FILE_EXTENSIONS
# FIXME, hardcoded for now LMAO
MODEL_FILE_EXTENSIONS = {'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill', 'pth', 'pt', 'ts', 'model', 'pb', 'joblib', 'npy',
                         'npz', 'onnx', 'safetensors'}
from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError
from tqdm import tqdm
from dotenv import load_dotenv
from utils import load, DATA_DIR, SCRIPTS_DIR
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import json

# load environment information with API tokens
load_dotenv(SCRIPTS_DIR / ".env")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-22", utc=True)
FIRST_DAY_OF_2024 = pd.to_datetime("2024-01-01", utc=True)
SIZE_LIMIT = 1 * 1024 * 1024 * 1024 * 1024  # 1 TB
api = HfApi(token=HF_API_TOKEN)


def has_model_file(model_files: list) -> bool:
    """
    This function checks if a model has at least one model file.
    :param model_files: list of files in the repository.
    :return: True if the repository has at least one model file, False otherwise.
    """
    return any([file["extension"] in MODEL_FILE_EXTENSIONS for file in model_files])


def get_wait_time(response: Response, fallback=30.0) -> float:
    """
    Gets the rate limit from the response headers and try to compute how long to wait.
    If not found, returns the fallback value.
    :param response: a response object from the Hugging Face API.
    :param fallback: a fallback value.
    :return: how long to wait.
    """
    if response is None: return fallback
    header = response.headers.get("RateLimit", "")
    match = re.search(r'(?:^|;)\s*t=(\d+(?:\.\d+)?)', header)
    if match:
        return float(match.group(1))
    return fallback


def get_repo_size(repo_id: str, sha: str, max_retries: int | None = None, initial_backoff: float = 5.0, max_backoff: float = 300.0, ) -> tuple[
    int, list[dict], str]:
    """
    Gets repository size and file metadata from the Hugging Face API.
    Retries:
      - HTTP 429 rate limits
      - HTTP 5xx server errors
      - connection errors
      - read/connect timeouts
    Does not retry:
      - inaccessible or nonexistent repositories
      - most other 4xx client errors
    Set max_retries=None to keep retrying indefinitely.
    """
    attempt = 0

    while True:
        try:
            model_info = api.model_info(repo_id, files_metadata=True, revision=sha)
            repo_files = []
            for sibling in model_info.siblings or []:
                # Copy the dictionary instead of modifying the object's internal __dict__ directly.
                repo_file = vars(sibling).copy()
                filename = repo_file.get("rfilename", "")
                repo_file["extension"] = (filename.rsplit(".", 1)[-1] if "." in filename else "")
                repo_files.append(repo_file)
            return model_info.usedStorage, repo_files, ""
        except RepositoryNotFoundError:
            # This may mean nonexistent, private, gated, or inaccessible.
            print(f"[NOT ACCESSIBLE] {repo_id}")
            return 0, [], f"[RepositoryNotFoundError] {repo_id}"

        except HfHubHTTPError as error:
            response = error.response
            status_code = (response.status_code if response is not None else None)

            # Do not repeatedly retry ordinary client-side failures.
            if status_code in {400, 401, 403, 404}:
                print(f"[HTTP {status_code}] Skipping {repo_id}")
                return 0, [], f"[HfHubHTTPError {status_code}] {repo_id}"

            # Retry rate limits and temporary server errors.
            if status_code == 429 or (status_code is not None and 500 <= status_code < 600):
                attempt += 1
                if max_retries is not None and attempt > max_retries:
                    print(f"[GAVE UP] {repo_id} after {max_retries} retries")
                    return 0, [], f"[MAX_RETRIES EXCEEDED (retried {max_retries} times)] {repo_id}"
                exponential_wait = min(initial_backoff * (2 ** (attempt - 1)), max_backoff, )
                wait_seconds = get_wait_time(response, fallback=exponential_wait, )
                print(f"[HTTP {status_code}] {repo_id}: waiting {wait_seconds:.1f}s before retry #{attempt}")
                time.sleep(wait_seconds)
                continue

            # Unexpected HTTP error: report rather than hiding it.
            print(f"[HTTP ERROR] {repo_id}:  {status_code} — {error}")
            return 0, [], f"[HTTP ERROR] {repo_id}:  {status_code} — {error}"

        except (
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
        ) as error:
            attempt += 1

            if max_retries is not None and attempt > max_retries:
                print(f"[GAVE UP] {repo_id} after {max_retries} retries {error}")
                return 0, []

            wait_seconds = min(initial_backoff * (2 ** (attempt - 1)), max_backoff, )
            wait_seconds += random.uniform(0, 2)

            print(f"[NETWORK ERROR] {repo_id}:  {type(error).__name__};  waiting {wait_seconds:.1f}s  before retry {attempt}")

            time.sleep(wait_seconds)
            continue

        except Exception as error:
            # Preserve unexpected errors instead of silently treating them as zero-byte repositories.
            print(f"[UNEXPECTED ERROR] {repo_id}:  {type(error).__name__}: {error}")
            return 0, [], f"[UNEXPECTED ERROR] {repo_id}:  {type(error).__name__}: {error}"
    return 0, [], f"[UNKNOWN ERROR] {repo_id}"


def exclude_models(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function excludes models based on the following exclusion criteria (EC):
    (E1) - Not modified on or after 2024
    (E2) - Does not have at least one model file
    (E3) - Gated (i.e. private)
    :param df: data frame with all models' metadata
    :return: a data frame with models that do not match any of the exclusion criteria.
    """
    # find repositories that are modified on or after 2024
    df_filtered = df[df["last_modified"] >= FIRST_DAY_OF_2024]
    # find repositories that have at least one model file
    df_filtered = df_filtered[df_filtered["siblings"].apply(has_model_file)]
    # find non-gated repositories
    df_filtered = df_filtered[~df_filtered["gated"]]
    return df_filtered


def load_cache(cache_path: Path) -> None:
    """
    Create the repository-size cache if it does not already exist.
    :param cache_path: path to the cache database file.
    """
    if not cache_path.exists():
        with sqlite3.connect(cache_path) as connection:
            fields = [
                "repo_id TEXT NOT NULL",
                "sha TEXT NOT NULL",
                "size INTEGER NOT NULL",
                "siblings TEXT",
                "error TEXT",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]
            pk = "repo_id,sha"
            connection.execute(f"CREATE TABLE IF NOT EXISTS repo_sizes ({fields.join(', ')}, PRIMARY KEY({pk}))")
            connection.commit()


def get_cached_repo_size(cache_path: Path, repo_id: str, sha: str) -> tuple[int, list | None]:
    """
    Return a previously successful result from the cache.
    Returns None when no successful cached result exists.
    :param cache_path: path to the cache database file.
    :param repo_id: id of the repository
    :param sha: sha of the repository
    """
    with sqlite3.connect(cache_path) as connection:
        query = "SELECT size, siblings  FROM repo_sizes WHERE repo_id = ? AND sha = ?"
        row = connection.execute(query, (repo_id, sha)).fetchone()
        if row is None: return -1, None
        size, siblings_json = row
        siblings = json.loads(siblings_json) if siblings_json else []
        return size, siblings


def save_to_cache(cache_path: Path, repo_id: str, sha: str, size: int, siblings: list, error: str = None, ) -> None:
    """
    Insert or update one repository result in the cache.
    """
    siblings_json = json.dumps(siblings, default=str)

    with sqlite3.connect(cache_path) as connection:
        connection.execute(
            """
            INSERT INTO repo_sizes (repo_id, sha, size, siblings, error, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP) ON CONFLICT(repo_id, sha) DO
            UPDATE SET
                size = excluded.size,
                siblings = excluded.siblings,
                error = excluded.error,
                updated_at = CURRENT_TIMESTAMP
            """,
            (repo_id, sha, size, siblings_json, error,),
        )
        connection.commit()


def filter_by_size(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function filters the repositories that are larger than `SIZE_LIMIT` (E4).
    :param df: data frame with all models' metadata
    :return: a data frame with the selected models that are not larger than `SIZE_LIMIT` (E4).
    """
    cache_file = DATA_DIR / "_repo_size_cache.sqlite3"
    load_cache(cache_file)

    # get the size of the repositories and add to the dataframe
    for idx, repo in tqdm(df.iterrows(), total=len(df), unit="repo"):
        size, siblings = get_cached_repo_size(cache_file, repo.id, repo.sha)
        if size < 0 and siblings is None:
            size, siblings, error = get_repo_size(repo["id"], repo["sha"])
            save_to_cache(cache_file, repo["id"], repo["sha"], size, siblings, error)
        # Update data frame with the retrieved size and siblings info
        df.at[idx, "size"], df.at[idx, "siblings"] = size, siblings

    # exclude repositories that are larger than 2 TB and not empty or that we could not retrieve its value
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


if __name__ == "__main__":
    input_file = DATA_DIR / "hf_sort_by_createdAt_top1209240.json"  # FIXME, place back .zip
    # out_legacy_models_file = DATA_DIR / "selected_legacy_repos.json"
    # out_recent_models_file = DATA_DIR / "selected_recent_repos.json"
    out_all_recent_models_file = DATA_DIR / "__all_recent_repos.json"

    # Step 1: Load the repositories' metadata
    print(f"Loading data from {input_file.name}...")
    df = load(input_file)
    df['last_modified'] = pd.to_datetime(df['last_modified'], utc=True)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    df['gated'] = df['gated'].astype(bool)
    df['size'] = 0  # initialize size column

    # Notice that 2022-03-02T23:29:04.000Z assigned to all repositories created before HF began storing creation dates.
    print("Min creation date = ", df["created_at"].min())

    # Step 2 - Exclude models
    print(f"Excluding models from {input_file.name} (initial size = {len(df)})...")
    df = exclude_models(df)
    print(f"After applying global exclusion criteria (E1--E3), {len(df)} repositories left.")

    # Step 3 - Inspect the repositories and identify legacy and recent repositories
    print("Finding and filtering legacy repositories...")
    df_legacy = select_legacy(df)
    df_legacy = filter_by_size(df_legacy)
    print(f"There are {len(df_legacy)} legacy repositories that passes all exclusion criteria (E1--E4).")
    # 3.1 check all recent sample
    print("Finding and filtering recent repositories...")
    df_recent_all = select_recent(df.copy())
    # df_recent_all = df_recent_all.iloc[ceil(.75 * len(df)):]  # FIXME bottom 3/4
    df_recent_all = filter_by_size(df_recent_all)
    df_recent_all.to_json(out_all_recent_models_file, orient="records", indent=2)
    # Compress the file
    with zipfile.ZipFile(out_all_recent_models_file.with_suffix(".json.zip"), 'w', compression=zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.write(out_all_recent_models_file, arcname=out_all_recent_models_file.name)

    # Delete the uncompressed file
    out_all_recent_models_file.unlink()

    print(f"There are {len(df_recent_all)} repositories that passes all exclusion criteria (E1--E4).")
    exit(0)

    # Step 4 - Sample recent repositories
    print("Selecting recent repositories...")
    df_copy = df.copy()
    df_recent = pd.DataFrame(columns=df_copy.columns)
    num_extra = 10  # number of extra repositories to sample from the recent period
    while len(df_legacy) + num_extra != len(df_recent):
        num_samples = len(df_legacy) + num_extra - len(df_recent)
        # sample and add to df_recent
        print(f"\tSampling recent repositories ({num_samples} samples)")
        selected = sample(select_recent(df_copy), num_samples)
        selected = filter_by_size(selected)
        print(f"\tAfter filtering, {len(selected)} recent repositories left")
        df_recent = selected if df_recent.empty else pd.concat([df_recent, selected])
        print(f"\tCurrent recent sample size {len(df_recent)} recent repositories...")

        # exclude from df_copy the repositories that were already sampled
        df_copy = df_copy[~df_copy["id"].isin(df_recent["id"])]
        print(f"\tCurrent copy sample size {len(df_copy)}...")

    df_recent.reset_index(inplace=True)
    # Check if the number of legacy and recent repositories is the same
    assert len(df_legacy) + num_extra == len(df_recent), "Number of legacy and recent repositories should be the same"
    print(f"Selected repositories: {len(df_legacy)} legacy / {len(df_recent)} recent")

    # Step 5 - Save the data
    # df_legacy.to_json(out_legacy_models_file, orient="records", indent=2)
    # df_recent.to_json(out_recent_models_file, orient="records", indent=2)

    # Print summary information
    print(f"Saved the selected repositories to {out_legacy_models_file} / {out_recent_models_file}")
    print(len(df_legacy), "legacy repositories selected for the study")
    print(f"\tLegacy Period: {df_legacy['created_at'].min()} - {df_legacy['created_at'].max()}")
    print(len(df_recent), "recent repositories selected for the study")
    print(f"\tRecent Period: {df_recent['created_at'].min()} - {df_recent['created_at'].max()}")
    print("Done!")
    print("Recommended next steps:")
    print("\t- Run the tests on tests/test_select_models.py to check the results.")
    print("\t- Run the get_commit_logs.py to download the commits logs for the selected repositories.")
