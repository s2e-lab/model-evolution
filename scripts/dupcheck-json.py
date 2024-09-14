import json

def remove_duplicates(filename):
    # Load the data from the JSON file
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract items and initialize structures for tracking duplicates
    items = data.get('items', [])
    seen_ids = set()
    unique_items = []
    duplicate_count = 0
    
    # Iterate over items to check for duplicates
    for item in items:
        item_id = item.get('question_id') or item.get('answer_id')
        if item_id in seen_ids:
            duplicate_count += 1
        else:
            seen_ids.add(item_id)
            unique_items.append(item)
    
    # Save the unique items back to the JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({'items': unique_items}, f, ensure_ascii=False, indent=4)
    
    return duplicate_count

filename = '../data/SO_query_data.json'
num_duplicates = remove_duplicates(filename)
print(f"Number of duplicate entries removed: {num_duplicates}")
