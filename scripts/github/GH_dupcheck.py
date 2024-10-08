"""
This script checks if the Github JSON data file contains any duplicate items.
"""

import json
import sys



def remove_duplicates(filename):
    # Load the data from the JSON file
    with open(filename, 'r') as f:
        data = json.load(f)

    # Initialize structures for tracking duplicates
    url_set, unique_items = set(), []

    # Iterate over items to check for duplicates
    for item in data:
        url = item['url']
        if url not in url_set:
            unique_items.append(item)
        url_set.add(url)

    # Save the unique items back to the JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(unique_items, f, ensure_ascii=False, indent=4)

    return len(data) - len(unique_items)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python GH_dupcheck.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]

    num_duplicates = remove_duplicates(filename)
    print(f"Number of duplicate entries removed: {num_duplicates}")