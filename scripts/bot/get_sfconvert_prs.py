"""
This script is used to check the status of the PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import json
import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from scripts.bot.bot_utils import extract_discussion_metadata

if __name__ == '__main__':
    # load prior results from data/bot_cache
    prior_files = [f for f in os.listdir(Path('../../data/bot_cache')) if f.endswith('.csv')]
    cache = dict()  # key = pr_url, value = row
    for f in prior_files:
        df = pd.read_csv(os.path.join('../../data/bot_cache', f)).fillna("")
        for index, row in df.iterrows():
            pr_url = row['pr_url'].split("#")[0]
            if row['model_id']:
                cache[pr_url] = row

    df = pd.read_csv(Path("../../data/sfconvertbot_pr_urls.csv"))
    out_file_prefix = '../../data/sfconvertbot_pr_metadata'

    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df.iterrows(), total=len(df)):
        pr_url = row['pr_url'].split("#")[0]
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
        if i != 0 and i % 500 == 0:
            df.to_csv(Path(out_file_prefix + f'_{i}.csv'), index=False)
            # delete prior checkpoint file
            if Path(out_file_prefix + f'_{i - 500}.csv').exists():
                os.remove(Path(out_file_prefix + f'_{i - 500}.csv'))

    df.to_csv(Path(out_file_prefix + '.csv'), index=False)
    # delete the  checkpoint files
    for i in range(500, len(df), 500):
        check_file = Path(out_file_prefix + f'_{i}.csv')
        if check_file.exists():
            os.remove(check_file)
