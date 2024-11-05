"""
This script is used to
(1) Obtain PR metadata  for the PR URLs that were created by the sfconvertbot.
(2) Merge it with the metadata from the conversion dataset.
(3) Save the metadata in a CSV file.
@Author: Joanna C. S. Santos
"""
import json
import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from bot_utils import save_checkpoint
from scripts.bot.bot_utils import extract_discussion_metadata

DATA_DIR = Path('../../data')


def load_conversion_dataset():
    """
    Loads the conversion dataset.
    :return: a cache where the key is the pr_url and the value is the row within the data frame.
    """
    df = pd.read_csv(DATA_DIR / 'hf_conversions.csv').fillna("")
    # remove duplicates (we found a few [8] duplicates in this dataset!)
    df.drop_duplicates(subset='pr_url', inplace=True)
    cache = {}  # key is the PR URL
    for index, row in df.iterrows():
        pr_url = row['pr_url'].split("#")[0]
        if row['model_id']:
            # ensure timestamps are consistent across datasets
            header = row['header_metadata'] if row['header_metadata'] else ""
            json_header = json.loads(row['header_metadata']) if header.startswith('{') else None
            row['time'] = json_header['discussion']['createdAt'] if json_header else None
            # after ensuring timestamps are consistent, we can add to cache
            cache[pr_url] = row
    return cache


if __name__ == '__main__':
    # load prior results from the conversion dataset
    cache = load_conversion_dataset()

    # specify the save rate for the last 500 iterations
    save_at = 250

    # load the PR URLs from the sfconvertbot
    df = pd.read_csv(DATA_DIR / 'sfconvertbot_pr_urls.csv')
    out_file_prefix = 'sfconvertbot_pr_metadata'
    processed_prs = set()

    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df.iterrows(), total=len(df), unit='PR URL'):
        pr_url = row['pr_url'].split("#")[0]
        processed_prs.add(pr_url)
        if pr_url in cache:
            row = cache[pr_url]
            df.loc[i, 'discussion_metadata'] = row['discussion_metadata']
            df.loc[i, 'header_metadata'] = row['header_metadata']
            df.loc[i, 'model_id'] = row['model_id']
            df.loc[i, 'time'] = row['time']
            continue
        else:
            events, header = extract_discussion_metadata(pr_url)
            df.loc[i, 'discussion_metadata'] = events
            df.loc[i, 'header_metadata'] = header
            # parse the header as JSON
            json_header = json.loads(header) if header and header.startswith('{') else None
            df.loc[i, 'model_id'] = json_header['discussion']['repo']['name'] if json_header else None
            df.loc[i, 'time'] = json_header['discussion']['createdAt'] if json_header else None

        # SAVES THE DATAFRAME EVERY 500 ITERATIONS
        if i != 0 and i % save_at == 0:
            save_checkpoint(df, out_file_prefix, i, save_at)

    # add in any PRs that were not processed from the cache
    for pr_url, row in tqdm(cache.items(), total=len(cache), unit='PR URL'):
        if pr_url not in processed_prs:
            df = pd.concat([df, row.to_frame().T], ignore_index=True)
            processed_prs.add(pr_url)

    # save the final data frame
    df.to_csv(DATA_DIR / (out_file_prefix + '.csv'), index=False)

    # delete last checkpoint files
    for i in range(save_at, len(df), save_at):
        check_file = DATA_DIR / (out_file_prefix + f'_{i}.csv')
        if check_file.exists():
            os.remove(check_file)
