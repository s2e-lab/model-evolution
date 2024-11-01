"""
This script is used to filter PRs made by the SFConvertBot.
We will do open coding of the selected PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import json
from pathlib import Path

import pandas as pd

if __name__ == '__main__':
    input_file = Path('../data/sfconvertbot_pr_metadata.csv')
    output_file = Path('../data/sfconvertbot_pr_metadata_filtered.csv')
    df = pd.read_csv(input_file)
    # create a dataframe to store the filtered PRs
    df_filtered = pd.DataFrame(columns=df.columns)

    # iterate over dataframe
    for index, row in df.iterrows():
        discussion_metadata = row['discussion_metadata']
        # check if is valid JSON
        if not discussion_metadata or discussion_metadata == 'None' or not discussion_metadata.startswith('{'):
            continue


        # parse as JSON
        discussion_metadata = json.loads(discussion_metadata)

        events = discussion_metadata['discussion']['events']
        original_author = discussion_metadata['discussion']['author']
        print(f"https://huggingface.co/{discussion_metadata['currentUrl']}")

        # criteria:
        # 1. PR has at least two non-empty comment
        # 2. two different authors in the discussion
        # 3. the average comment size is more than 2 words
        num_non_empty_comments = 0
        authors = set([original_author["name"]])
        num_words = 0
        for event in events:
            print("\t",event)
            event_type = event['type']
            event_author = event['author']

            if event_type == 'comment':
                num_non_empty_comments += 1
                authors.add(event_author["name"])
                num_words += len(event['data']['latest']['raw'].split())

        should_include = num_non_empty_comments >= 2 and len(authors) >= 2 and num_words / num_non_empty_comments > 2
        if should_include:
            # add the row to the filtered dataframe
            df_filtered.loc[len(df_filtered)] = row

    df_filtered.to_csv(output_file, index=False)
