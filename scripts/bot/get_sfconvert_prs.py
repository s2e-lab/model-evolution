"""
This script is used to check the status of the PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import os
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

from scripts.bot.bot_utils import extract_discussion_metadata

if __name__ == '__main__':
    ds = load_dataset("safetensors/conversions")['train']
    # convert dataset to dataframe
    df_sfconvert = ds.to_pandas()
    df_sfconvert['time'].min(), df_sfconvert['time'].max()

    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df_sfconvert.iterrows(), total=len(df_sfconvert)):
        pr_url = row['pr_url']
        events, header = extract_discussion_metadata(pr_url)
        df_sfconvert.loc[i, 'discussion_metadata'] = events
        df_sfconvert.loc[i, 'header_metadata'] = header
        # SAVES THE DATAFRAME EVERY 500 ITERATIONS
        if i != 0 and i % 500 == 0:
            df_sfconvert.to_csv(Path(f'../../data/sfconvertbot_pr_metadata_{i}.csv'), index=False)

    df_sfconvert.to_csv(Path('../../data/sfconvertbot_pr_metadata.csv'), index=False)
    # delete the checkpoint files
    for i in range(500, len(df_sfconvert), 500):
        os.remove(Path(f'../data/../sfconvertbot_pr_metadata_{i}.csv'))
