"""
This script is used to filter PRs made by the SFConvertBot.
We will do open coding of the selected PRs that were created by the sfconvertbot.
@Author: Joanna C. S. Santos
"""
import json
from pathlib import Path
from tqdm import tqdm
import pandas as pd

if __name__ == '__main__':
    input_file = Path('../../data/sfconvertbot_pr_metadata.csv')
    output_file = Path('../../data/sfconvertbot_pr_metadata_filtered.csv')
    df = pd.read_csv(input_file)
    # create a dataframe to store the filtered PRs
    df_filtered = pd.DataFrame(columns=df.columns)
    # set NaN values to None
    df = df.where(pd.notnull(df), None)


    # iterate over dataframe
    for index, row in tqdm(df.iterrows(), total=len(df)):
        discussion_metadata = row['discussion_metadata']
        # check if is valid JSON
        if not discussion_metadata or discussion_metadata == 'None' or not discussion_metadata.startswith('{'):
            continue


        # parse as JSON
        discussion_metadata = json.loads(discussion_metadata)

        events = discussion_metadata['discussion']['events']
        original_author = discussion_metadata['discussion']['author']
        # print(f"https://huggingface.co/{discussion_metadata['currentUrl']}")

        # criteria:
        # 1. PR has at least two non-empty comment
        # 2. two different authors in the discussion
        # 3. the average comment size is more than 2 words
        num_non_empty_comments = 0
        authors = set([original_author["name"]])
        num_words = 0
        for event in events:
            # print("\t",event)
            event_type = event['type']
            if event_type == 'comment' and not event['data']['hidden']:
                event_author = event['author']
                num_non_empty_comments += 1
                authors.add(event_author["name"])
                num_words += len(event['data']['latest']['raw'].split())

        should_include = num_non_empty_comments >= 2 and len(authors) >= 2 and num_words / num_non_empty_comments > 2
        if should_include:
            # add the row to the filtered dataframe
            df_filtered.loc[len(df_filtered)] = row
            # add title
            df_filtered.loc[len(df_filtered) - 1, 'title'] = discussion_metadata['discussion']['title'] + f" by {original_author['name']} ({discussion_metadata['currentUrl']})"

    # add a source column
    df_filtered['source'] = 'SFConvertBot PRs'
    # rename PR URL column to url
    df_filtered.rename(columns={'pr_url': 'url'}, inplace=True)
    # rename discussion_metadata to json_content
    df_filtered.rename(columns={'discussion_metadata': 'json_content'}, inplace=True)
    # reorder columns
    df_filtered = df_filtered[['source', 'title', 'url', 'json_content']]
    # save the filtered dataframe
    df_filtered.to_csv(output_file, index=False)
