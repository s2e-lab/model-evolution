import json

''' This script checks if the Github JSON data file contains any duplicate items. '''

def test_unique_urls(filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    url_set = set()
    url_dups = []
    dups = 0

    for entry in data:
        url = entry['url']
        if url in url_set:
            print(f"Duplicate URL found: {url}")
            url_dups.append(url)
            dups += 1
            continue
        url_set.add(url)

    if not url_dups:
        print("All URLs are unique!")
    else:
        print(f"\n{dups} duplicate URLs were found.")


filename = '../data/GH_data_safetensor.json'
test_unique_urls(filename)

import json

# Load existing data
with open('../data/GH_data_safetensor.json', 'r') as file:
    data = json.load(file)