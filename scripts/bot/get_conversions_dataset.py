"""
This script is used to check the status of the PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import os
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

from scripts.bot.bot_utils import extract_discussion_metadata, save_checkpoint

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
        # saves the data frame every save_at iterations to avoid losing data
        if i != 0 and i % save_at == 0:
            save_checkpoint(df, out_file_prefix, i, save_at)

    df.to_csv(Path(f'../../data/{out_file_prefix}.csv'), index=False)
    # delete the checkpoint files
    for i in range(save_at, len(df), save_at):
        check_file = Path(f'../../data/{out_file_prefix}_{i}.csv')
        if check_file.exists():
            os.remove(check_file)
