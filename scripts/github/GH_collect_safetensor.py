import os
import json
import requests
import time
import sys
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, wait_random_exponential

''' This script collects GitHub pull requests that contain the words "safetensor" or "safe tensor" or "safetensors" in the title or body. '''

class RateLimitException(Exception):                                                # function to handle rate limit errors
    pass


@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(60) + wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type(RateLimitException)
)
def fetch_data(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 401:                                                 # UNSUCCESSFUL: token access error
        print(f"Unauthorized access to {url}. Please check your token.")
        return [], {}
    if response.status_code == 200:                                                 # SUCCESS
        json_response = response.json()                                             # parse response content as json
        if isinstance(json_response, dict):
            return json_response.get('items', []), response.links                   # return pull requests as well as pagination links
        else:
            print(f"Unexpected response type: {type(json_response)}")
            return [], {}
    elif response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:   # UNSUCCESSFUL: rate-limited
        reset_time = int(response.headers['X-RateLimit-Reset'])                     # extract reset time
        sleep_duration = max(0, reset_time - int(time.time()))                      # calculate sleep duration and ensure nonnegative time
        print(f"Rate limited. Sleeping for {sleep_duration} seconds.")
        time.sleep(sleep_duration)
        raise RateLimitException("Rate limited")                                    # after sleeping, raise RateLimitExceptoion
    else:
        response.raise_for_status()

@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(60) + wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type(RateLimitException)
)
def fetch_comments(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 401:                                                 # UNSUCCESSFUL: token access error
        print(f"Unauthorized access to {url}. Please check your token.")
        return [], {}
    if response.status_code == 200:                                                 # SUCCESS
        json_response = response.json()
        if isinstance(json_response, list):
            return json_response, response.links
        else:
            print(f"Unexpected response type: {type(json_response)}")
            return [], {}
    elif response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:
        reset_time = int(response.headers['X-RateLimit-Reset'])
        sleep_duration = max(0, reset_time - int(time.time()))
        print(f"Rate limited. Sleeping for {sleep_duration} seconds.")
        time.sleep(sleep_duration)
        raise RateLimitException("Rate limited")
    else:
        response.raise_for_status()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python GH_collect_safetensor.py <output-file>")
        sys.exit(1)
    output_file = sys.argv[1]                                                         # get output file name from command line argument
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")                                                   # get github token from .env file
    if not token:
        raise ValueError("GITHUB_TOKEN is required.")

    url = 'https://api.github.com/search/issues'                                        # set base url as github api search endpoint

    date_ranges = [                                                                     # single request exceed 1000 results (Github API limit), must separate into different time range
        ('2024-05-01', '2024-09-01'),                                                   # range from 01 JAN 2020 - 01 SEP 2024
        ('2024-01-01', '2024-05-01'),
        ('2023-09-01', '2024-01-01'),
        ('2023-05-01', '2023-09-01'),
        ('2023-01-01', '2023-05-01'),
        ('2022-09-01', '2023-01-01'),
        ('2022-05-01', '2022-09-01'),
        ('2022-01-01', '2022-05-01'),
        ('2021-09-01', '2022-01-01'),
        ('2021-05-01', '2021-09-01'),
        ('2021-01-01', '2021-05-01'),
        ('2020-09-01', '2021-01-01'),
        ('2020-05-01', '2020-09-01'),
        ('2020-01-01', '2020-05-01')
    ]

    query_0 = 'safetensor OR "safe tensor" OR safetensors is:closed is:pr -author:app/dependabot -author:app/dependabot-preview -author:app/renovate -author:app/greenkeeper -author:greenkeeperio-bot created:>2024-09-01'
    query_n = 'safetensor OR "safe tensor" OR safetensors is:closed is:pr -author:app/dependabot -author:app/dependabot-preview -author:app/renovate -author:app/greenkeeper -author:greenkeeperio-bot created:<2020-01-01'
    base_query = 'safetensor OR "safe tensor" OR safetensors is:closed is:pr -author:app/dependabot -author:app/dependabot-preview -author:app/renovate -author:app/greenkeeper -author:greenkeeperio-bot created:'

    queries = [query_0] + [f"{base_query}{start_date}..{end_date}" for start_date, end_date in date_ranges] + [query_n]

    n = 0
    n_with_bot = 0

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

    pr_list = []

    for query in queries:
        params = {
            'q': query,
            'per_page': 100,
            'page': 1
        }
        while True:
            try:
                pull_requests, response_links = fetch_data(url, headers, params)          # call fetch_data to get pull_requests and response_links
                for pr in pull_requests:
                    n_with_bot += 1
                    if pr['user']['type'] != 'Bot' and (pr['user']['login'].lower().endswith('bot') == False):
                        comments_url = pr['comments_url']
                        comments, response_links_comments = fetch_comments(
                            comments_url, headers)
                        comment_list = []                                                 # retrieve comments for current pr and append to comment_list
                        for comment in comments:
                            comment_body = comment['body']
                            comment_list.append(comment_body)
                        pr_details = {
                            'title': pr['title'],
                            'url': pr['html_url'],
                            'author': pr['user']['login'],
                            'question': pr['body'],
                            'comments': comment_list
                        }
                        pr_list.append(pr_details)
                        print(f"[{n}] TITLE: {pr['title']}\n")
                        n += 1
                if 'next' in response_links:                                               # continue to next page if it exists
                    params['page'] += 1
                    time.sleep(10)
                else:
                    break                                                                  # if no more pages, exit
            except RateLimitException:                                                     # if still rate-limited after sleep, exit
                print("Still rate-limited. Exiting.")
                break

    print(f"Total number of pull requests: {n}")
    print(f"Total number of pull requests with bot: {n_with_bot}")
    with open(output_file, 'w') as f:
        json.dump(pr_list, f)
    print(f"Data has been dumped in {output_file}.")