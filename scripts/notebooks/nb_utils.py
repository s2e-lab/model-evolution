import zipfile
from pathlib import Path
from typing import Literal

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS
from tqdm import tqdm

# Reference date when safetensors was released
SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-23")
# Data and results directories
DATA_DIR = Path('../../data')
RESULTS_DIR = Path('../../results')


def read_repositories_evolution(group: Literal['recent', 'legacy', 'both']) -> pd.DataFrame:
    """
    Read the commits from the repository evolution dataset.
    :return: a data frame
    """
    if group not in ('recent', 'legacy', 'both'):
        raise ValueError(f"Invalid mode: {group}")

    if group == 'both':
        df_recent = read_repositories_evolution('recent')
        df_legacy = read_repositories_evolution('legacy')
        df = pd.concat([df_recent, df_legacy], ignore_index=True)
        return df


    df = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_commits.csv")
    # ensure date is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    # Calculate elapsed days since reference date (safetensors first release)
    df['elapsed_days'] = (df['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    # Add a change_status to data frame
    df_commits = pd.read_csv(DATA_DIR / f"selected_{group}_commits.csv")
    # set "changed_files" and "all_files_in_tree" columns to empty string if it is NaN
    df_commits["changed_files"] = df_commits["changed_files"].fillna("")
    df_commits["all_files_in_tree"] = df_commits["all_files_in_tree"].fillna("")
    changed_files = dict()  # key = repo_url/file_path&&commit_hash; value = status (added, modified, deleted)
    for index, row in tqdm(df_commits.iterrows(), total=len(df_commits), unit="commit"):
        commit_hash = row["commit_hash"]
        repo_url = row["repo_url"]
        if row["changed_files"]:
            for x in row["changed_files"].split(";"):
                status, file_path = x.split(maxsplit=1)
                changed_files[f"{repo_url}/{file_path}&&{commit_hash}"] = status

    # Add the change_status to the data frame for the files that are in the commit
    df["change_status"] = ""
    for index, row in tqdm(df.iterrows(), total=len(df), unit="commit"):
        commit_hash = row["commit_hash"]
        model_file_path = row["model_file_path"]
        if df.at[index, "is_in_commit"]:
            df.at[index, "change_status"] = changed_files[f"{model_file_path}&&{commit_hash}"]

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


def get_commit_log_stats(group: Literal['recent', 'legacy']) -> pd.Series:
    """
    Read the commits logs extracted for the selected repositories and compute some basic stats.
    :return:
    """
    stats = pd.Series()

    # Load the repositories and set nan columns to empty string
    input_file = DATA_DIR / f"selected_{group}_commits.csv"
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


