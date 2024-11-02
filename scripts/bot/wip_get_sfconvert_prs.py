import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm
import json

from bot_utils import extract_discussion_metadata

if __name__ == '__main__':
    df = pd.read_csv("../../data/discussion_urls.csv")
    out_file_prefix = '../../data/crawled_sfconvertbot_pr_metadata'

    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df.iterrows(), total=len(df)):
        pr_url = row['pr_url']
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

    df.to_csv(Path(out_file_prefix + '.csv'), index=False)
    # delete the checkpoint files
    for i in range(500, len(df), 500):
        os.remove(Path(out_file_prefix + f'_{i}.csv'))
