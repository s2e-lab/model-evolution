import json

def count_entries(filename):
    # Load the data from the JSON file
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count the number of items in the 'items' list
    count = len(data.get('items', []))
    return count

filename = '../data/SO_query_data.json'
num_entries = count_entries(filename)
print(f"Number of entries in the JSON file: {num_entries}")
