"""
This script is used to check the status of the PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import math
from pathlib import Path

import requests
from datasets import load_dataset
from requests import Response
from tqdm import tqdm
import pandas as pd

def get_pr_status(response: Response) -> str:
    """
    Check the status of the PR.
    :param response: the response of the HTTP request
    :return: the status of the PR
    """
    if response.status_code == 200:
        html_resp = response.text
        if 'Ready to merge' in html_resp:
            return "Ready to Merge"
        elif 'Cannot merge' in html_resp:
            return "Cannot merge"
        # try to find the string changed pull request status to N, and extract status from it
        elif 'changed pull request status to' in html_resp:
            status = html_resp.split('changed pull request status to')[1].split('</strong>')[0].strip()
            status = status.replace('<strong class="text-gray-700">', '')
            return status
    else:
        return f"HTTP Error (status code = {response.status_code})"


if __name__ == '__main__':
    # ds = load_dataset("safetensors/conversions")['train']
    # # convert dataset to dataframe
    # df_sfconvert = ds.to_pandas()
    # df_sfconvert['time'].min(), df_sfconvert['time'].max()

    df_sfconvert = pd.read_csv(Path('../results/sfconvertbot_merge_status.csv'))
    # convert nan to None
    df_sfconvert['merged'] = df_sfconvert['merged'].apply(lambda x: x if str(x) != "nan" else None)
    # iterate over dataframe to check whether the PRs were merged
    for i, row in tqdm(df_sfconvert.iterrows(), total=len(df_sfconvert)):
        if row['merged'] != None or i < 8000: continue
        pr_url = row['pr_url']
        # make an HTTP request
        response = requests.get(pr_url)
        df_sfconvert.loc[i, 'merged'] = get_pr_status(response)
        # SAVES THE DATAFRAME EVERY 500 ITERATIONS
        if i != 0 and i % 500 == 0:
            df_sfconvert.to_csv(Path(f'../results/sfconvertbot_merge_status_{i}.csv'), index=False)

    df_sfconvert.to_csv(Path('../results/sfconvertbot_merge_status.csv'), index=False)
