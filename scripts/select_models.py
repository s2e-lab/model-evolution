#!/usr/bin/env python
# coding: utf-8
"""
Selecting model repositories to include on our study.
"""

import os
import zipfile
from pathlib import Path
from utils import DATA_DIR
import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS


def load(input_file: Path) -> pd.DataFrame:
    # uncompress zip file to the DATA_DIR
    with zipfile.ZipFile(input_file.with_suffix(".json.zip"), 'r') as zip_ref:
        zip_ref.extractall(DATA_DIR)
    # load the data
    df = pd.read_json(input_file)
    # delete the unzipped file
    os.remove(input_file)
    return df


def filter(df: pd.DataFrame) -> pd.DataFrame:
    df['last_modified'] = pd.to_datetime(df['last_modified'], utc=True)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)

    # find models created_at before 2022 and last_modified in 2024
    df_filtered = df[(df["created_at"].dt.year <= 2022) & (df["last_modified"].dt.year == 2024)]
    # if the year is 2022, we need to check the month. We want to only have models created *before* September 2022 (not including)
    df_filtered = df_filtered[((df_filtered["created_at"].dt.year < 2022) | (df_filtered["created_at"].dt.month < 9))]

    # find model repositories with at least one model file (extension in MODEL_FILE_EXTENSIONS)
    df_filtered = df_filtered[
        df_filtered["siblings"].apply(lambda x: any([file["extension"] in MODEL_FILE_EXTENSIONS for file in x]))]

    return df_filtered




if __name__ == "__main__":
    input_file = DATA_DIR / "huggingface_sort_by_createdAt_top996939.json"
    output_file = DATA_DIR / "huggingface_sort_by_createdAt_top996939_selected.json"

    # Step 1: Load the repositories' metadata
    print(f"Loading data from {input_file}...")
    df = load(input_file)
    # From Hugging Face API, we have the following information:
    # It's important to note that there is a unique value, 2022-03-02T23:29:04.000Z assigned to all repositories
    # that were created before we began storing creation dates.
    print("Min creation date = ", df["created_at"].min())

    # Step 2 - Filter the repositories based on the following criteria
    # - models created before September 2022; AND
    # - models last modified in 2024; AND
    # - models with at least one model file.
    print(f"Filtering data from {input_file}...")
    df = filter(df)

    # Step 3 - Save the data
    # ensure gated column is boolean to avoid runtime errors
    df["gated"] = df["gated"].astype(bool)
    df.to_json(output_file)
    print(f"Selected {len(df)} repositories to include in the study.")
    print(f"Saved the selected repositories to {output_file}")
