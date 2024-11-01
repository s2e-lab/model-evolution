"""
This script is used to check the status of the PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from datasets import load_dataset
from tqdm import tqdm


def extract_discussion_metadata(pr_url:str)->str:
    """
    Extracts the discussion metadata from the PR URL.
    :param pr_url: the URL of the PR.
    :return: a string with the discussion metadata (in JSON format).
    """
    # Send an HTTP GET request to the URL
    response = requests.get(pr_url)

    # Check if the request was successful
    if response.status_code != 200:
        return "HTTP Error (status code: {response.status_code})"

    # Parse the page content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all divs with class "SVELTE_HYDRATER contents" and data-target="DiscussionEvents"
    discussion_events = soup.find_all('div', class_='SVELTE_HYDRATER contents',
                                      attrs={'data-target': 'DiscussionEvents'})
    if len(discussion_events) > 0:
        div = discussion_events[0]
        return div.get('data-props')

    return None


if __name__ == '__main__':
    ds = load_dataset("safetensors/conversions")['train']
    # convert dataset to dataframe
    df_sfconvert = ds.to_pandas()
    df_sfconvert['time'].min(), df_sfconvert['time'].max()

    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df_sfconvert.iterrows(), total=len(df_sfconvert)):
        pr_url = row['pr_url']
        df_sfconvert.loc[i, 'discussion_metadata'] = extract_discussion_metadata(pr_url)
        # SAVES THE DATAFRAME EVERY 500 ITERATIONS
        if i != 0 and i % 500 == 0:
            df_sfconvert.to_csv(Path(f'../data/sfconvertbot_pr_metadata_{i}.csv'), index=False)

    df_sfconvert.to_csv(Path('../data/sfconvertbot_pr_metadata.csv'), index=False)
    # delete the checkpoint files
    for i in range(500, len(df_sfconvert), 500):
        os.remove(Path(f'../data/sfconvertbot_pr_metadata_{i}.csv'))
