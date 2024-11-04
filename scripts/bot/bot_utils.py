import requests
from bs4 import BeautifulSoup
from datasets import load_dataset


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


def get_bot_conversions(out_file_prefix: str) -> None:
    """
    This function loads the `safetensors/conversions` dataset from the Hugging Face Datasets library.
    This is an obsolete dataset that contains PRs created by the sfconvertbot.
    The function iterates over the dataset and extracts the discussion metadata from the PRs and saves it.
    """
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
            df_sfconvert.to_csv(Path(f'../../data/{out_file_prefix}_{i}.csv'), index=False)

    df_sfconvert.to_csv(Path(f'../../data/{out_file_prefix}.csv'), index=False)
    # delete the checkpoint files
    for i in range(500, len(df_sfconvert), 500):
        os.remove(Path(f'../data/../{out_file_prefix}_{i}.csv'))