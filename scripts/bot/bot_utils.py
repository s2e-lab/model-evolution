import os
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


def extract_discussion_metadata(pr_url: str) -> tuple:
    """
    Extracts the discussion metadata from the PR URL.
    :param pr_url: the URL of the PR.
    :return: a string with the discussion metadata (in JSON format).
    """
    # Send an HTTP GET request to the URL
    response = requests.get(pr_url)

    # Check if the request was successful
    if response.status_code != 200:
        msg = f"HTTP Error (status code: {response.status_code})"
        return msg, msg

    # Parse the page content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all divs with class "SVELTE_HYDRATER contents" and data-target="DiscussionEvents"
    discussion_events = soup.find_all('div', class_='SVELTE_HYDRATER contents',
                                      attrs={'data-target': 'DiscussionEvents'})

    discussion_header = soup.find_all('div', class_='SVELTE_HYDRATER contents',
                                      attrs={'data-target': 'DiscussionHeader'})
    events, header = None, None
    if len(discussion_events) > 0:
        events = discussion_events[0].get('data-props')
    if len(discussion_header) > 0:
        header = discussion_header[0].get('data-props')
    return events, header


def save_checkpoint(df: pd.DataFrame, out_file_prefix: str, i: int, save_at: int) -> None:
    """
    Saves the dataframe to a CSV file and deletes the prior checkpoint file. Checkpoint files are saved at the data folder.
    :param df: the dataframe to be saved.
    :param out_file_prefix: a prefix for the output file.
    :param i: a suffix
    :param save_at:  the number of iterations to save the checkpoint.
    """
    df.to_csv(Path(f'../../data/{out_file_prefix}_{i}.csv'), index=False)
    # delete prior checkpoint file
    prior_file = Path(f'../../data/{out_file_prefix}_{i - save_at}.csv')
    if prior_file.exists():
        os.remove(prior_file)
