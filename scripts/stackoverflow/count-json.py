import json
import sys


def count_entries(filename):
    # Load the data from the JSON file
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Count the number of items in the 'items' list
    count = len(data.get('items', []))
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count-json.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    num_entries = count_entries(filename)
    print(f"Number of entries in the JSON file: {num_entries}")
