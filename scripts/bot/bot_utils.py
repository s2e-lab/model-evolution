import requests
from bs4 import BeautifulSoup


def extract_discussion_metadata(pr_url:str)->tuple:
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
