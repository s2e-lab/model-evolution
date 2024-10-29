

#%%
from pathlib import Path

import pandas as pd


# Reference date when safetensors was released
SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-23")


def read_commits():
    df = pd.read_csv(Path('../../results/repository_evolution_0-4924_fixed_bug_MERGED.csv'))
    df_commits = pd.read_csv(Path('../../data/huggingface_sort_by_createdAt_top996939_commits_0_1035.csv'))

    # grabs the date from df2 and adds it to df based on commit_hash and repo_url matching
    df['date'] = ""
    for index, row in df.iterrows():
        commit_hash = row['commit_hash']
        repo_url = row['repo_url']
        matched_row = df_commits.loc[
            (df_commits['commit_hash'] == commit_hash) &
            (df_commits['repo_url'] == repo_url)
            ]

        df.at[index, 'date'] = matched_row['date'].values[0]
        df.at[index, 'message'] = matched_row['message'].values[0]

    df['date'] = pd.to_datetime(df['date'])

    # Calculate elapsed days since reference date
    df['elapsed_days'] = (df['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    return df

def get_safetensors_releases():
    """
    Get the dates of the safetensors releases based on the tags in its repo.
    :return: a dataframe with the dates of the releases in days since the first release and their corresponding labels
    """
    # Dates of the releases in days since the first release and their corresponding labels
    df_releases = pd.read_csv(Path('../../data/safetensors_tags.csv'))
    df_releases['date'] = pd.to_datetime(df_releases['date'])
    df_releases['elapsed_days'] = (df_releases['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    # remove rc releases
    df_releases = df_releases[~df_releases['tag'].str.contains('rc')]

    # for releases on the same date, prefer the one that does not start with python-
    df_releases = df_releases.sort_values(['date', 'tag'], ascending=[True, False]).drop_duplicates('date', keep='first')

    # remove the python- prefix from the tag
    df_releases['tag'] = df_releases['tag'].str.replace('python-', '')

    return df_releases