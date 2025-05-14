import zipfile
from pathlib import Path

import pandas as pd
import os
from analyticaml import MODEL_FILE_EXTENSIONS
from typing import Literal
# Reference date when safetensors was released
SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-23")
# Data and results directories
DATA_DIR = Path('../../data')
RESULTS_DIR = Path('../../results')


def read_repositories_evolution(group: Literal['recent', 'legacy']) -> pd.DataFrame:
    """
    Read the commits from the repository evolution dataset.
    :return: a data frame
    """
    if group not in ('recent', 'legacy'):
        raise ValueError(f"Invalid mode: {group}")

    df = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_commits.csv")
    # ensure date is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    # Calculate elapsed days since reference date (safetensors first release)
    df['elapsed_days'] = (df['date'] - SAFETENSORS_RELEASE_DATE).dt.days

    # check whether all files are in cache
    all_model_files = [f for f in row["all_files_in_tree"].split(";") if is_model_file(f)]
    changed_files = dict()  # key = file_path, value = status (added, modified, deleted)
    for x in row["changed_files"].split(";"):
        status, file_path = x.split(maxsplit=1)
        changed_files[file_path] = status




    return df


def filter_by_extension(changed_files: str) -> bool:
    """
    Implement a filter to check if the list of changed files in a commit has model files.
    A model file is a file that has one of the extensions in MODEL_FILE_EXTENSIONS.
    :param changed_files: a string with the list of changed files in a commit (separated by ";").
    :return: True if there is a model file in the list, False otherwise.
    """
    changed_files = changed_files.split(";")
    file_extensions = [Path(f).suffix[1:] for f in changed_files]
    return any([ext in MODEL_FILE_EXTENSIONS for ext in file_extensions])


def get_commit_log_stats() -> pd.Series:
    """
    Read the commits logs extracted for the selected repositories and compute some basic stats.
    :return:
    """
    stats = pd.Series()

    # Load the repositories and set nan columns to empty string
    input_file = DATA_DIR / "huggingface_sort_by_createdAt_top996939_commits_0_1035.csv"
    df = pd.read_csv(input_file).fillna("")
    stats.loc["# commits in all logs (total)"] = len(df)

    # identify the commits that have at least one model file
    df = df[df["changed_files"].apply(lambda x: filter_by_extension(x))]
    df.reset_index(drop=True, inplace=True)
    # compute commits that do not contain at least one model file in its tree
    num_empty = 0
    for _, row in df.iterrows():
        all_model_files = []
        for f in row["all_files_in_tree"].split(";"):
            if Path(f).suffix[1:] in MODEL_FILE_EXTENSIONS:
                all_model_files.append(f)
        if len(all_model_files) == 0:
            num_empty += 1

    stats.loc["# commits touching at least one serialized model"] = len(df)
    stats.loc["# commits containing at least one model file in its tree"] = len(df) - num_empty
    stats.loc["# commits not containing at least one model file"] = num_empty
    stats.loc["last commit date"] = df["date"].max()
    stats.loc["# repos"] = df["repo_url"].nunique()

    return stats


def get_safetensors_releases():
    """
    Get the dates of the safetensors releases based on the tags in its repo.
    :return: a dataframe with the dates of the releases in days since the first release and their corresponding labels
    """
    # Dates of the releases in days since the first release and their corresponding labels
    df_releases = pd.read_csv(DATA_DIR / 'safetensors_tags.csv')
    df_releases['date'] = pd.to_datetime(df_releases['date'])
    df_releases['elapsed_days'] = (df_releases['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    # remove rc releases
    df_releases = df_releases[~df_releases['tag'].str.contains('rc')]

    # for releases on the same date, prefer the one that does not start with python-
    df_releases = (df_releases.sort_values(['date', 'tag'], ascending=[True, False])
                   .drop_duplicates('date', keep='first'))

    # remove the "python-" prefix from the tag
    df_releases['tag'] = df_releases['tag'].str.replace('python-', '')

    return df_releases


def unzip(zip_path, extract_to='.'):
    # Unzip the file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
