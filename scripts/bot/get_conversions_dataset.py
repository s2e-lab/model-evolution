"""
This script is used to check the status of the PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import json
import os
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

from scripts.bot.bot_utils import extract_discussion_metadata


def save_checkpoint(df: pd.DataFrame, out_file_prefix: str, i: int, save_at: int) -> None:
    """
    Saves the dataframe to a CSV file and deletes the prior checkpoint file.
    :param df: the dataframe to be saved.
    :param out_file_prefix: a prefix for the output file (including parent folders).
    :param i: a suffix
    :param save_at:  the number of iterations to save the checkpoint.
    """
    df.to_csv(Path(f'../../data/{out_file_prefix}_{i}.csv'), index=False)
    # delete prior checkpoint file
    prior_file = Path(f'../../data/{out_file_prefix}_{i - save_at}.csv')
    if prior_file.exists():
        os.remove(prior_file)


if __name__ == '__main__':
    save_at = 500
    out_file_prefix = 'hf_conversions'
    ds = load_dataset("safetensors/conversions")['train']
    # convert dataset to dataframe
    df = ds.to_pandas()
    df['time'].min(), df['time'].max()
    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df.iterrows(), total=len(df)):
        pr_url = row['pr_url']
        events, header = extract_discussion_metadata(pr_url)
        df.loc[i, 'discussion_metadata'] = events
        df.loc[i, 'header_metadata'] = header
        # SAVES THE DATAFRAME EVERY 500 ITERATIONS
        if i != 0 and i % save_at == 0:
            save_checkpoint(df, out_file_prefix, i, save_at)

    df.to_csv(Path(f'../../data/{out_file_prefix}.csv'), index=False)
    # delete the checkpoint files
    for i in range(save_at, len(df), save_at):
        check_file = Path(f'../../data/{out_file_prefix}_{i}.csv')
        if check_file.exists():
            os.remove(check_file)


