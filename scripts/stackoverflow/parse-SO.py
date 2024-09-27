import requests
import json
import sys

# This script collects questions or answers from Stack Overflow that contain the words "safetensor" or "safe tensor" or "safetensors".
def search_questions(query):
    url = "https://api.stackexchange.com/2.2/search/excerpts"
    params = {
        "order": "desc",
        "sort": "activity",
        "pagesize": 100,
        "q": query,
        "site": "stackoverflow",
    }
    all_items = []
    page = 1

    while True:
        params['page'] = page  # Set page parameter to the current page
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        all_items.extend(data.get('items', []))

        # Break out of the loop if there are no more items to fetch
        if not data.get('has_more', False):
            break

        page += 1  # Increment the page number for the next iteration

    return all_items


def write_to_json(data, filename):
    # Save the data to the file, overwriting any existing content
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({'items': data}, f, ensure_ascii=False, indent=4)



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python parse-SO.py <output-filename>")
        sys.exit(1)


    all_items = []

    query1 = "safetensor"
    items1 = search_questions(query1)
    all_items.extend(items1)

    query2 = "safe tensor"
    items2 = search_questions(query2)
    all_items.extend(items2)

    query3 = "safetensors"
    items3 = search_questions(query3)
    all_items.extend(items3)

    write_to_json(all_items, sys.argv[1])
    print("# of questions or answers in SO that contain the queries =", len(all_items))
