from pathlib import Path

import pandas as pd

# Reference date when safetensors was released
SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-23")
# Data and results directories
DATA_DIR = Path('../../data')
RESULTS_DIR = Path('../../results')

def read_commits():
    """
    Read the commits from the repository evolution dataset.
    :return:
    """
    df = pd.read_csv(DATA_DIR / 'repository_evolution_commits_0_5014.csv')
    # ensure date is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    # Calculate elapsed days since reference date (safetensors first release)
    df['elapsed_days'] = (df['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    return df


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
    df_releases = df_releases.sort_values(['date', 'tag'], ascending=[True, False]).drop_duplicates('date',
                                                                                                    keep='first')

    # remove the python- prefix from the tag
    df_releases['tag'] = df_releases['tag'].str.replace('python-', '')

    return df_releases
